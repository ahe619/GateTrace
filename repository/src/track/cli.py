"""Frozen author-panel tracking from one explicitly bound YOLOX cache."""
import argparse
import gzip
import json
from pathlib import Path
from src.detect.io import (activate_frozen, development, explicit_asset, load_json,
                           new_output, offline_runtime, require, runtime_directories, sha, write_json)


def mot_line(frame, row):
    x1, y1, x2, y2 = row["box"]
    score = row["score"] if row["score"] is not None else -1
    # Native tracker xyxy is 0-based; MOTChallenge serializes the left/top as 1-based.
    return ",".join(map(str, [frame, row["track_id"], x1+1, y1+1, x2-x1, y2-y1, score, -1, -1, -1])) + "\n"


def cache_metadata(cache_dir):
    doc = load_json(Path(cache_dir) / "cache_manifest.json")
    require(doc["schema"] == "crowd_flow_yolox_cache_v1", "Unsupported cache")
    development(doc["sequence"])
    require(type(doc["frames"]) is int and doc["frames"] > 0, "Nonempty native-frame cache required")
    return doc


def run(cache_dir, method, output, gmc_manifest=None):
    doc = cache_metadata(cache_dir)
    output = new_output(output)
    cache = explicit_asset(cache_dir, doc["cache"])
    gmc = None
    if method == "bot":
        require(gmc_manifest is not None, "BoT-SORT requires an explicit GMC binding manifest")
        gd = load_json(gmc_manifest)
        require(set(gd) == {"sequence", "gmc"} and gd["sequence"] == doc["sequence"], "GMC sequence differs")
        gmc = explicit_asset(Path(gmc_manifest).parent, gd["gmc"])
    else:
        require(gmc_manifest is None, "GMC only applies to BoT-SORT")
    activate_frozen("src/track/frozen")
    offline_runtime()
    from sota83d.panel import PanelTracker
    output.mkdir(parents=True, exist_ok=False)
    runtime_directories(output)
    if gmc is not None:
        destination = output / "runtime/tracker/GMC_files/MOTChallenge" / ("GMC-" + doc["sequence"] + ".txt")
        destination.parent.mkdir(parents=True)
        destination.write_bytes(gmc.read_bytes())
    tracker = PanelTracker(method, doc["sequence"], tuple(reversed(doc["native_size"])),
                           bot_root=output / "runtime" if method == "bot" else None)
    tracks = output / (doc["sequence"] + ".txt")
    observations = output / "observations.jsonl.gz"
    count = 0
    try:
        with gzip.open(cache, "rt", encoding="utf-8") as source, \
             tracks.open("x", encoding="utf-8", newline="\n") as mot, \
             gzip.open(observations, "xt", encoding="utf-8", newline="\n") as audit:
            for count, line in enumerate(source, 1):
                row = json.loads(line)
                require(row["source_frame"] == count and row["frame"] == count-1,
                        "Cache frame order differs; no missing-frame fill")
                result = tracker.update(row["detections"], count)
                for emitted in result["outputs"]:
                    mot.write(mot_line(count, emitted))
                audit.write(json.dumps(dict(source_frame=count, frame=count-1, time_s=row["time_s"],
                                            **result), allow_nan=False) + "\n")
        require(count == doc["frames"], "Incomplete cache; no completion receipt written")
    finally:
        tracker.close()
    write_json(output / "track_manifest.json", dict(schema="crowd_flow_panel_tracks_v1",
        sequence=doc["sequence"], method=method, frames=count, source_cache_sha256=sha(cache),
        tracks=dict(path=tracks.name, bytes=tracks.stat().st_size, sha256=sha(tracks)),
        observations=dict(path=observations.name, bytes=observations.stat().st_size, sha256=sha(observations)),
        parameters=tracker.args, with_reid=False,
        coordinate_contract="MOTChallenge 1-based left/top/frame/ID; width/height unchanged from native xyxy",
        events_interface="standard output-box bottom-center; feed to scripts/score_tracker.py"))
    return {"status": "TRACKED", "method": method, "frames": count}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cache", required=True, type=Path)
    p.add_argument("--method", required=True, choices=("byte", "oc", "bot"))
    p.add_argument("--out", type=Path)
    p.add_argument("--gmc-manifest", type=Path)
    p.add_argument("--execute", action="store_true")
    a = p.parse_args(argv)
    if a.execute:
        if a.out is None:
            p.error("--out is required with --execute")
        result = run(a.cache, a.method, a.out, a.gmc_manifest)
    else:
        doc = cache_metadata(a.cache)
        result = dict(status="CACHE_METADATA_VALIDATED_ONLY", sequence=doc["sequence"],
                      method=a.method, cache_rows_read=False, tracker_initialized=False)
    print(json.dumps(result, indent=2))
    return 0
