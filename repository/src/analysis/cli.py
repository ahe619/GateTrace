"""Explicit JSON adapters for unchanged analytical primitives; no data discovery."""
import argparse
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path
from src.detect.io import development, fragment_namespace, frozen_module, load_json, new_output, require, write_json

FILES = {"e1": "r15e28_e1_core78a_v2.py", "e2": "r15e28_e2_masks.py",
         "headgate": "r15e27_headgate_inference.py", "d1": "r15e29_gap_core81.py",
         "gatelink": "r15e32_gatelink_oracle.py"}


def module(key):
    return frozen_module("src/analysis/frozen/" + FILES[key], "_portable_" + key)


def analyze(action, doc):
    development(doc["sequence"])
    if action == "reid-decision":
        ns = fragment_namespace("r15_reid93_analysis.py", {"Fraction": Fraction})
        return ns["decision"](doc["report"])
    if action == "reid-support":
        ns = fragment_namespace("r15_reid93_analysis.py", {"Fraction": Fraction})
        return dict(categories=[ns["sidecat"](support) for support in doc["supports"]],
                    interpretation="descriptive support categories; no identity reassignment or causal claim")
    if action == "e2-mask":
        m = module("e2")
        rows = [m.Observation(**row) for row in doc["observations"]]
        require(all(row.sequence_id == doc["sequence"] for row in rows), "Observation sequence differs")
        return asdict(m.make_mask(rows, retention=doc["retention"], seed=doc["seed"],
                                  mode=doc["mode"], fps_by_sequence={doc["sequence"]: doc["fps"]}))
    if action == "d1-gaps":
        timelines = {int(k): v for k, v in doc["timelines"].items()}
        return dict(gaps=module("d1").gaps(timelines, fps=doc["fps"]), descriptive_only=True)
    if action == "headgate-project":
        projection = module("headgate").HeadProjection(mode="mot", anchor="head_box_bottom_center",
            size=doc["native_size"], calibration=doc["calibration"])
        return dict(points=[projection.point(d) for d in doc["detections"]], metadata=projection.metadata())
    if action == "gatelink":
        m = module("gatelink")
        require(doc["max_gap_frames"] in (50, 125), "Frozen GateLink gap must be 50 or 125 frames")
        if doc["mode"] == "bridge":
            rows, added = m.bridge_same_id(doc["rows"], doc["max_gap_frames"])
            return dict(rows=rows, added=added, oracle=True)
        require(doc["mode"] == "link", "GateLink mode must be bridge or link")
        ids = {(r["source_frame"], r["track_id"]): r["gt_id"] for r in doc["valid_identities"]}
        rows, links, added = m.oracle_link(doc["rows"], ids, doc["max_gap_frames"])
        return dict(rows=rows, links=links, added=added, oracle=True)
    if action == "e1-pools":
        raw, outputs, mapping, detections = module("e1").pools(doc["frame"], doc["system"])
        return dict(admitted=raw, outputs=outputs, raw_to_output=mapping, detections=detections)
    if action == "e1-attribute":
        args = dict(doc["arguments"])
        for key in ("support", "gtframes", "outputobs"):
            args[key] = {int(k): v for k, v in args[key].items()}
        args["fragment_lookup"] = {(r["source_frame"], r["track_id"]): tuple(r["fragment"])
                                   for r in args["fragment_lookup"]}
        category, subtype, details = module("e1").attribute(**args)
        return dict(category=category, subtype=subtype, details=details, causal_claim=False)
    if action == "m4-stitch":
        m = frozen_module("src/track/frozen/r15e26_stitch_v2.py", "_portable_m4")
        return m.stitch_frame_rows(doc["frames"], namespace=doc["namespace"], fps=doc["fps"],
                                  gates=doc["gates"], g1=doc["g1"], clarification=doc["policy"])
    raise ValueError("Unsupported analysis action")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("e2-mask", "d1-gaps", "headgate-project", "gatelink",
                                      "e1-pools", "e1-attribute", "m4-stitch", "reid-decision", "reid-support"))
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args(argv)
    output = new_output(a.out)
    result = analyze(a.action, load_json(a.input))
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, result)
    print("WROTE_EXPLICIT_ANALYSIS_OUTPUT")
    return 0
