"""Score native v11 final events against explicit development GT, without decoding events.

This is an I/O adapter around unchanged core functions. Packaging status remains
NOT_REAL_DATA_REGRESSED; successful execution alone is not a historical parity receipt.
"""
import argparse
from collections import Counter, defaultdict
import copy
import gzip
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import sys
import time
from types import SimpleNamespace

from src.detect.io import (REPO, binding, explicit_asset, load_json, new_output,
                           offline_runtime, require, sha)

SEQUENCES = ("MOT20-01", "MOT20-02")
GATES = ("H_30", "H_50", "H_70", "V_25", "V_50", "V_75")
BINS = ("low", "mid_low", "mid_high", "high")
REGRESSION_STATUS = "NOT_REAL_DATA_REGRESSED"


def core_api():
    """Verify only code; import under an alias without touching bundled example data."""
    require(sys.flags.optimize == 0, "Do not use Python -O/-OO")
    rows = load_json(REPO / "metadata/core_frozen_map.json")["core_code_files"]
    for row in rows:
        path = REPO / row["repo_path"]
        require(path.stat().st_size == row["bytes"] and sha(path) == row["sha256"],
                "Frozen core source differs: " + row["repo_path"])
    package = "_portable_native_score_core"
    if package not in sys.modules:
        source = REPO / "core/src"
        spec = importlib.util.spec_from_file_location(package, source / "__init__.py",
                                                     submodule_search_locations=[str(source)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[package] = module
        spec.loader.exec_module(module)
    modules = {name: importlib.import_module(package + "." + path) for name, path in {
        "score": "score", "labels": "labels", "census": "frozen_labels_census",
        "e1": "frozen_score.e1", "identity": "frozen_score.identity",
        "matching": "frozen_score.matching", "view": "frozen_score.labels_view",
        "aggregate": "frozen_score.aggregate"}.items()}
    entry_name = package + "_reproduce_entry"
    if entry_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(entry_name, REPO / "core/reproduce.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[entry_name] = module
        spec.loader.exec_module(module)
    modules["entry"] = sys.modules[entry_name]
    return SimpleNamespace(**modules)


def scoped_inputs(files, kind, api):
    """Reuse the frozen development path guard before opening GT/seqinfo contents."""
    require(kind in ("gt", "seqinfo") and set(files) == set(SEQUENCES), "Explicit development input map required")
    first = Path(files[SEQUENCES[0]])
    depth = 2 if kind == "gt" else 1
    require(len(first.parents) > depth, "Expected complete development input path")
    checked = api.entry.input_paths(first.parents[depth], kind)
    require(all(Path(files[s]).resolve() == checked[s] for s in SEQUENCES),
            "Explicit inputs must share the guarded development root and sequence paths")
    return checked


def validate_native_manifest(doc, sequence):
    require(sequence in SEQUENCES and doc["sequence"] == sequence, "Native sequence outside requested development scope")
    require(doc["schema"] == "crowd_flow_native_v11_output_v1", "Native output schema differs")
    require(doc["event_box_source"] == "raw_detection_box"
            and doc["identity_box_source"] == "post_M4_tracker_rows", "Native event/identity source contract differs")
    require(doc["identity_scoring_executed"] is False, "Input already carries identity scoring")
    require(doc["fps"] == 25 and type(doc["frames"]) is int and doc["frames"] > 0, "Native frame metadata differs")
    require(len(doc["native_size"]) == 2 and all(type(v) is int and v > 1 for v in doc["native_size"]), "Native size invalid")
    require(doc["source_kind"] in ("crowddet", "yolox"), "Native source kind differs")
    expected = {"frames", *GATES}
    require(set(doc["files"]) == expected, "Require one frame cache and exactly six native gate artifacts")
    for key, ref in doc["files"].items():
        binding(ref)
        filename = "frames.jsonl.gz" if key == "frames" else "gates/" + key + "/events.json"
        require(ref["path"] == filename, "Native artifact path differs: " + key)
    return doc


def output_pool(row, index, api):
    """Preserve frozen E1-v2 output-box/raw-index association, including M4 checks."""
    require(type(row["frame"]) is int and type(row["source_frame"]) is int
            and row["frame"] == index and row["source_frame"] == index + 1,
            "Native frame order differs")
    require(math.isfinite(row["time_s"]) and abs(row["time_s"] - index / 25) <= 1e-9,
            "Native frame time differs")
    _, output, _, _ = api.e1.pools(row, "v11")
    return output


def frame_identity(row, index, gt, api, numpy):
    records, _, audit = api.e1.assign(output_pool(row, index, api), gt, api.matching.solve, numpy)
    observations = [dict(source_frame=index + 1, track_id=z["tid"], raw_detection_index=z["index"],
        gt_id=z["gt_id"], gt_class=z["gt_class"], gt_line=z["gt_line"], status=z["status"],
        box=z["box"], assigned_iou=z["assigned_iou"], margin=z["margin"]) for z in records]
    return observations, audit


def gate_score(document, sequence, gate, length, outputobs, classes, transitions, gtviews, api):
    """Attach newly computed identities to a copy of the native final event list."""
    require(sequence in SEQUENCES and gate in GATES, "Scoring unit outside development scope")
    require(document["sequence"] == sequence and document["gate_id"] == gate
            and document["metadata"]["nb_frames"] == length and document["metadata"]["fps"] == 25,
            "Native final event metadata differs")
    predictions = copy.deepcopy(document["final_events"])
    require(len({p["prediction_id"] for p in predictions}) == len(predictions), "Duplicate final event ID")
    for prediction in predictions:
        require(prediction["sequence"] == sequence and prediction["gate_id"] == gate,
                "Native event scope differs")
        frame = api.score._integer(prediction["source_frame"])
        target = api.score._integer(prediction["target_frame"])
        tid = api.score._integer(prediction["track_id"])
        require(target + 1 == frame and 1 <= frame <= length and tid in outputobs,
                "Native event lacks emitted track/anchor")
        api.view.exact_time(frame, prediction["time_s"])
        api.view.position(prediction["crossing_position_native_px"])
        require("_identity" not in prediction and "identity_association" not in prediction,
                "Cached identity answers are prohibited")
        prediction["_identity"] = api.identity.event_identity(outputobs[tid], frame, classes)
    require(len(transitions) == len(gtviews), "Label/view count differs")
    selected = [(r, g) for r, g in zip(transitions, gtviews)
                if r["sequence"] == sequence and r["line_id"] == gate and r["confirmed"]]
    selected.sort(key=lambda z: (z[0]["gt_frame_1based"], z[0]["track_id"], z[0]["event_id"]))
    truths = [dict(id=r["event_id"], frame=int(r["gt_frame_1based"]), gid=int(r["track_id"]),
        direction=r["direction"], position=r["position_native_px"], h=g["h"], bin=g["bin"])
        for r, g in selected]
    matched, _, _, audit = api.e1.event_matching(predictions, truths, api.matching.solve,
                                               api.matching.can_match_right_optimally)
    unit = dict(sequence=sequence, gate=gate, N_GT=len(truths), N_final=len(predictions), correct=len(matched),
        identity_statuses=dict(Counter(p["_identity"]["status"] for p in predictions)),
        bins={b: dict(correct=sum(j in matched for j, g in enumerate(truths) if g["bin"] == b),
                      GT=sum(g["bin"] == b for g in truths)) for b in BINS})
    ranges = api.score._optimal_ranges(audit, truths, api.matching)
    return unit, dict(sequence=sequence, gate=gate, ranges=ranges), audit


def run(native_roots, gt_files, seqinfo_files, output):
    require(set(native_roots) == set(gt_files) == set(seqinfo_files) == set(SEQUENCES),
            "Exactly MOT20-01 and MOT20-02 are required")
    api = core_api()
    gt_files = scoped_inputs(gt_files, "gt", api)
    seqinfo_files = scoped_inputs(seqinfo_files, "seqinfo", api)
    manifests = {seq: validate_native_manifest(load_json(Path(native_roots[seq]) / "native_manifest.json"), seq)
                 for seq in SEQUENCES}
    manifest_hashes = {seq: sha(Path(native_roots[seq]) / "native_manifest.json") for seq in SEQUENCES}
    require(len({d["source_kind"] for d in manifests.values()}) == 1, "Do not aggregate different detector sources")
    output = new_output(output)
    for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[key] = "1"
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    offline_runtime()
    import numpy as np
    require(np.__version__ == "2.2.6", "Frozen label reconstruction requires NumPy 2.2.6; no automatic installation")
    output.mkdir(parents=True, exist_ok=False)
    cpu, wall = time.process_time(), time.monotonic()
    reads = []

    def budget():
        require(time.process_time() - cpu <= 1800 and time.monotonic() - wall <= 1800,
                "Native scoring exceeds 1800 seconds; preserve partial outputs")
        require(shutil.disk_usage(output).free >= 20 * 1024 ** 3, "Less than 20 GiB free")

    def read(path, alias, expected_sha=None):
        budget()
        path = Path(path)
        before = path.stat()
        raw = path.read_bytes()
        after = path.stat()
        digest = hashlib.sha256(raw).hexdigest()
        require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), "Input changed while reading")
        reads.append(dict(path=alias, bytes=len(raw), sha256=digest))
        require(expected_sha is None or digest == expected_sha, "Bound input changed: " + alias)
        return raw

    def save(path, value):
        api.score._write(path, value)

    save(output / "started.json", dict(schema="crowd_flow_native_v11_score_start_v1",
        regression_status=REGRESSION_STATUS, sequences=list(SEQUENCES),
        event_source="supplied_native_final_events_no_redecoding", identity_source="actual_post_M4_tracker_rows",
        no_inference=True, no_tracking=True, no_stored_identity_used=True))
    try:
        budget()
        summary = api.labels.build_labels(gt_files, seqinfo_files, output / "labels")
        transitions = [json.loads(line) for line in gzip.decompress(read(output / "labels/transitions.jsonl.gz",
                        "rebuilt_labels:transitions.jsonl.gz")).decode("utf-8-sig").splitlines() if line.strip()]
        require(all(t["sequence"] in SEQUENCES for t in transitions), "Label scope differs")
        gtviews = [api.view.gt_row(r, "labels/transitions.jsonl.gz", i) for i, r in enumerate(transitions, 1)]
        require(sum(bool(t["confirmed"]) for t in transitions) == 724, "Whole-sequence population must be 724")
        units, range_units = [], []
        for sequence in SEQUENCES:
            doc, root = manifests[sequence], Path(native_roots[sequence])
            meta = summary["sequences"][sequence]["metadata"]
            require(doc["frames"] == meta["seqLength"] and doc["fps"] == meta["fps"]
                    and doc["native_size"] == [meta["width"], meta["height"]], "Native/label metadata differs")
            reread = read(root / "native_manifest.json", sequence + ":native_manifest.json", manifest_hashes[sequence])
            require(json.loads(reread) == doc, "Native manifest changed after validation")
            gtbytes = read(gt_files[sequence], "gt:" + sequence, api.census.EXPECTED_INPUTS[sequence]["gt"])
            gt, classes = api.identity.parse_gt(gtbytes.decode("utf-8-sig"), doc["frames"])
            del gtbytes
            assets = {key: explicit_asset(root, ref) for key, ref in doc["files"].items()}
            compact = read(assets["frames"], sequence + ":frames.jsonl.gz", doc["files"]["frames"]["sha256"])
            outputobs, n = defaultdict(list), 0
            with gzip.open(output / (sequence + "_frame_identity.jsonl.gz"), "xt", encoding="utf-8") as stream:
                for line in gzip.decompress(compact).decode("utf-8").splitlines():
                    budget()
                    row = json.loads(line)
                    observations, audit = frame_identity(row, n, gt.get(n + 1, []), api, np)
                    for observation in observations:
                        outputobs[observation["track_id"]].append(observation)
                    stream.write(json.dumps(api.score._serial(dict(source_frame=n + 1, observations=observations,
                        output_assignment=audit)), allow_nan=False, separators=(",", ":")) + "\n")
                    n += 1
            require(n == doc["frames"], "Incomplete native frame cache")
            del compact
            evidence = []
            for gate in GATES:
                budget()
                eventdoc = json.loads(read(assets[gate], sequence + ":" + doc["files"][gate]["path"],
                                           doc["files"][gate]["sha256"]))
                unit, ranges, audit = gate_score(eventdoc, sequence, gate, n, outputobs, classes,
                                                 transitions, gtviews, api)
                units.append(unit)
                range_units.append(ranges)
                evidence.append(dict(gate=gate, **audit))
            save(output / (sequence + "_event_matching.json"), evidence)
        combined = api.aggregate.aggregate(units)
        report = dict(schema="crowd_flow_native_v11_score_result_v1", status="NATIVE_IDENTITY_SCORING_COMPLETE",
            regression_status=REGRESSION_STATUS, historical_parity="NOT_CHECKED_BY_THIS_ENTRY",
            native_manifest_sha256=manifest_hashes, source_kind=manifests[SEQUENCES[0]]["source_kind"],
            main=dict(name="E1 v2 whole sequence native v11", aggregate=combined,
                by_sequence={s: api.aggregate.aggregate([u for u in units if u["sequence"] == s]) for s in SEQUENCES}),
            summary_table={**{b: dict(matched=combined["bins"][b]["numerator"], denominator=combined["bins"][b]["denominator"])
                              for b in BINS},
                "overall": dict(matched=combined["correct"], denominator=combined["GT"]),
                "precision": dict(matched=combined["correct"], denominator=combined["final_events"])},
            matching_ranges=dict(aggregate=api.score._aggregate_ranges(range_units),
                by_sequence={s: api.score._aggregate_ranges([u for u in range_units if u["sequence"] == s]) for s in SEQUENCES}),
            population="whole_sequence_724_not_core_671", event_source="supplied_native_final_events_no_redecoding",
            identity_pool="actual post-M4 output boxes; frozen raw-index tie ordering",
            unknown_precision_policy="Unknown, ambiguous, mixed and ignore remain in ALL-final denominator",
            secondary_core_671="NOT_COMPUTED",
            range_semantics="All max-cardinality/minimum-exact-time optima per disjoint sequence/gate; not confidence intervals",
            anonymous_range_policy="All native final events under the same legal time/direction/position gates; no denominator deletion",
            no_inference=True, no_tracking=True, human_QC="not_reviewed", independent_reproduction=False,
            numpy=np.__version__, cpu_s=time.process_time() - cpu, elapsed_s=time.monotonic() - wall)
        save(output / "units.json", dict(main=units))
        save(output / "matching_ranges.json", range_units)
        save(output / "scores.json", report)
        save(output / "read_ledger.json", reads)
        budget()
        save(output / "complete.json", dict(status="NATIVE_IDENTITY_SCORING_COMPLETE",
            regression_status=REGRESSION_STATUS, historical_parity="NOT_CHECKED_BY_THIS_ENTRY"))
        return api.score._serial(report)
    except BaseException as exc:
        save(output / "FAIL.json", dict(status="FAIL_PRESERVED", error=repr(exc), reads=reads,
            regression_status=REGRESSION_STATUS, cpu_s=time.process_time() - cpu, elapsed_s=time.monotonic() - wall))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--native-01", type=Path, required=True)
    parser.add_argument("--native-02", type=Path, required=True)
    parser.add_argument("--gt-root", type=Path, required=True, help="Contains MOT20-01/gt/gt.txt and MOT20-02/gt/gt.txt")
    parser.add_argument("--seqinfo-root", type=Path, required=True, help="Contains MOT20-01/seqinfo.ini and MOT20-02/seqinfo.ini")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    require(sys.flags.optimize == 0, "Do not use Python -O/-OO")
    roots = dict(zip(SEQUENCES, (args.native_01, args.native_02)))
    if args.execute:
        if args.out is None:
            parser.error("--out is required with --execute")
        result = run(roots, {s: args.gt_root / s / "gt/gt.txt" for s in SEQUENCES},
                     {s: args.seqinfo_root / s / "seqinfo.ini" for s in SEQUENCES}, args.out)
        result = dict(status=result["status"], regression_status=REGRESSION_STATUS, summary_table=result["summary_table"])
    else:
        for sequence, root in roots.items():
            validate_native_manifest(load_json(root / "native_manifest.json"), sequence)
        result = dict(status="NATIVE_SCORE_MANIFESTS_VALIDATED_ONLY", scientific_assets_opened=False,
                      regression_status=REGRESSION_STATUS)
    print(json.dumps(result, indent=2))
    return 0
