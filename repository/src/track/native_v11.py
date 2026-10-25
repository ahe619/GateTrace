"""Development v11: original threshold tracker, raw detection feet, M4 and native events.

This produces native event and output-box artifacts. It does not call the standard
output-box event extractor or claim that native identity scoring has run.
"""
import argparse
import copy
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import types
from src.detect.io import (REPO, activate_frozen, binding, development, explicit_asset,
    fragment_namespace, frozen_module, load_json, new_output, offline_runtime, require,
    runtime_directories, sha, verify_frozen, write_json)


def validate(doc):
    require(set(doc) == {"schema", "sequence", "fps", "native_size", "frames", "source_kind",
                        "cache", "geometry", "g1", "m4_policy", "detector_lineage"}, "Native v11 fields differ")
    require(doc["schema"] == "crowd_flow_native_v11_inputs_v1", "Unknown native v11 manifest")
    development(doc["sequence"])
    require(doc["fps"] == 25 and doc["source_kind"] in ("yolox", "crowddet"), "Frozen fps/source required")
    require(type(doc["frames"]) is int and doc["frames"] > 0, "Positive complete frame count required")
    require(len(doc["native_size"]) == 2 and all(type(v) is int and v > 1 for v in doc["native_size"]), "Native [W,H] required")
    for key in ("cache", "geometry", "g1", "m4_policy", "detector_lineage"):
        binding(doc[key])
    return doc


class ExplicitRuntimeReader:
    """Reads only pinned adapter sources and registered installed runtime trees."""
    def __init__(self, source_root):
        self.source_root = Path(source_root).resolve()
        self.runtime_roots = []
        self.reads = []

    def register_runtime_tree(self, path, purpose=""):
        self.runtime_roots.append(Path(path).resolve())

    def read(self, path, expected_sha=None, purpose=""):
        path = Path(path).resolve()
        require(path.is_relative_to(self.source_root) or any(path.is_relative_to(p) for p in self.runtime_roots),
                "Read outside explicit source/runtime roots")
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        require(expected_sha is None or digest == expected_sha, "Frozen runtime source differs")
        self.reads.append(dict(name=path.name, bytes=len(raw), sha256=digest, purpose=purpose))
        return raw


def method_tracker(output):
    activate_frozen("src/track/frozen")
    root = Path(output) / "runtime/native_sources"
    folder = root / "scripts"
    folder.mkdir(parents=True, exist_ok=False)
    for name in ("r15e17_trackers.py", "r15_tracker_idxfix.py"):
        (folder / name).write_bytes((REPO / "src/track/frozen" / name).read_bytes())
    reader = ExplicitRuntimeReader(root)
    inference = types.ModuleType("r15e24_inference")
    inference.__dict__["_root"] = lambda: root
    fragment_namespace("r15e24_inference.py", inference.__dict__)
    sys.modules["r15e24_inference"] = inference
    ns = fragment_namespace("r15e26_run_v2.py", dict(copy=copy, math=math, require=require,
        FROZEN={"r15_tracker_idxfix.py": "477c3041fed126903e8e18de967e14da4a98775fef5ac4a4cf48a5eb611ac0d3"}))
    return ns["MethodTracker"](reader, .1), ns["fresh_raw"], reader


def native_events(frames, doc, geometry, g1):
    event = frozen_module("src/track/frozen/r15e24_events.py", "_portable_native_events")
    sources = REPO / "src/track/frozen/event_sources"
    verify_frozen("src/track/frozen/event_sources/")
    def read(path, purpose=""):
        return Path(path).read_bytes()
    api = event.load_frozen(read, sources)
    ranges = g1["fitting_coordinate_range"]
    if set(ranges) == {"x_normalized", "y_top_normalized"}:
        ranges = {"head_x_norm": ranges["x_normalized"], "head_y_norm": ranges["y_top_normalized"]}
    model = event.make_height_model(g1["coefficients"], ranges)
    observations = [{k: d[k] for k in ("frame", "source_frame", "track_id", "box", "confidence",
        "raw_detection_index", "point", "point_source")} for row in frames for d in row["detections"]
        if d.get("track_id") is not None]
    result = {}
    for gate in geometry["lines"]:
        result[gate["line_id"]] = api.evaluate_sequence_gate(observations, sequence=doc["sequence"],
            gate_id=gate["line_id"], width=doc["native_size"][0], height=doc["native_size"][1],
            nb_frames=doc["frames"], fps=25, model=model, polygons=gate["polygons"])
    return result


def output_bindings(output):
    """Bind emitted bytes for the separate native-event identity scorer."""
    names = {"frames": "frames.jsonl.gz", **{gate: "gates/" + gate + "/events.json"
             for gate in ("H_30", "H_50", "H_70", "V_25", "V_50", "V_75")}}
    return {key: dict(path=name, bytes=(Path(output) / name).stat().st_size,
                      sha256=sha(Path(output) / name)) for key, name in names.items()}


def run(manifest, output):
    manifest = Path(manifest)
    doc = validate(load_json(manifest))
    output = new_output(output)
    assets = {key: explicit_asset(manifest.parent, doc[key])
              for key in ("cache", "geometry", "g1", "m4_policy", "detector_lineage")}
    geometry, g1, policy, lineage = [load_json(assets[key]) for key in ("geometry", "g1", "m4_policy", "detector_lineage")]
    require(geometry["sequence"] == doc["sequence"] and g1["sequence"] == doc["sequence"], "Geometry sequence differs")
    require(g1["native_size"] == doc["native_size"], "G1 size differs")
    require(tuple(g["line_id"] for g in geometry["lines"]) == ("H_30", "H_50", "H_70", "V_25", "V_50", "V_75"), "Frozen six gate order required")
    m4 = frozen_module("src/track/frozen/r15e26_stitch_v2.py", "_portable_native_m4")
    require(sha(assets["m4_policy"]) == m4.FROZEN_POLICY_SHA256, "Original development M4 policy bytes required")
    m4.require_production_ready(policy)
    if doc["source_kind"] == "yolox":
        from src.detect.cli import WEIGHT_SHA
        require(lineage["weight_sha256"] == WEIGHT_SHA and lineage["test_size_hw"] == [800, 1440]
                and lineage["conf"] == .01 and lineage["nms_iou"] == .7, "YOLOX lineage differs")
    else:
        require(lineage["kind"] == "P2" and lineage["raw_threshold"] == "score > 0.01" and lineage["max_det"] is None,
                "Frozen CrowdDet raw lineage required")
        require(lineage["author"]["short_size"] == 1280 and lineage["author"]["max_size"] == 2240
                and lineage["author"]["set_nms_threshold"] == .5, "CrowdDet detector parameters differ")
    output.mkdir(parents=True, exist_ok=False)
    runtime_directories(output)
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[key] = "4"
    offline_runtime()
    import torch
    import cv2
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    cv2.setNumThreads(1)
    tracker, fresh, reader = method_tracker(output)
    point_for = fragment_namespace("r15e24_run55.py", {"math": math})["point_for"]
    frames = []
    with gzip.open(assets["cache"], "rt", encoding="utf-8") as stream:
        for frame, line in enumerate(stream):
            source = json.loads(line)
            require(source["frame"] == frame and source["source_frame"] == frame+1
                    and source["time_s"] == frame/25, "Cache frame/time mismatch")
            detections, tracker_rows = tracker.update(fresh(source["detections"]), tuple(reversed(doc["native_size"])))
            for detection in detections:
                point, reason, outside = point_for(detection["box"], *doc["native_size"])
                detection.update(frame=frame, source_frame=frame+1, point=point,
                    point_source="box_bottom_center", point_invalid_reason=reason, point_outside_image=outside)
            frames.append(dict(frame=frame, source_frame=frame+1, time_s=frame/25,
                detections=detections, tracker_rows=tracker_rows,
                tracker_frame_metadata=tracker.last_frame_metadata))
    require(len(frames) == doc["frames"], "Cache frame count differs")
    stitched = m4.stitch_frame_rows(frames, namespace={"sequence": doc["sequence"], "block": "full_sequence"},
        fps=25, gates=geometry["lines"], g1=g1, clarification=policy)
    frames = stitched.pop("frames")
    with gzip.open(output / "frames.jsonl.gz", "xt", encoding="utf-8", newline="\n") as stream:
        for row in frames:
            stream.write(json.dumps(row, allow_nan=False) + "\n")
    write_json(output / "stitch.json", stitched)
    for gate, result in native_events(frames, doc, geometry, g1).items():
        folder = output / "gates" / gate
        folder.mkdir(parents=True)
        write_json(folder / "events.json", result)
    write_json(output / "native_manifest.json", dict(schema="crowd_flow_native_v11_output_v1",
        sequence=doc["sequence"], source_manifest_sha256=sha(manifest), tracker=tracker.metadata,
        fps=25, native_size=doc["native_size"], frames=doc["frames"], source_kind=doc["source_kind"],
        files=output_bindings(output), regression_status="NOT_REAL_DATA_REGRESSED",
        source_reads=reader.reads, event_box_source="raw_detection_box", identity_box_source="post_M4_tracker_rows",
        identity_scoring_executed=False,
        scoring_contract="Use scripts/score_native_v11.py for saved final_events plus actual tracker_rows; do not pass to score_tracker.py."))
    return dict(status="NATIVE_EVENTS_EXTRACTED_NOT_SCORED", frames=len(frames), gates=6)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--out", type=Path)
    p.add_argument("--execute", action="store_true")
    a = p.parse_args(argv)
    if a.execute:
        if a.out is None:
            p.error("--out is required with --execute")
        result = run(a.manifest, a.out)
    else:
        doc = validate(load_json(a.manifest))
        result = dict(status="NATIVE_MANIFEST_VALIDATED_ONLY", sequence=doc["sequence"], assets_opened=False)
    print(json.dumps(result, indent=2))
    return 0
