"""YOLOX pixel export with an explicit per-image manifest. Default is validation only."""
import argparse
import gzip
import json
from pathlib import Path
from .io import (activate_frozen, binding, development, explicit_asset, finite_positive,
                 load_json, new_output, offline_runtime, require, runtime_directories, sha, write_json)

WEIGHT_SHA = "e3945f3523fde1e107708aacd64dab0670c34e371d136e54587cac7a50d3cfba"


def validate_manifest(doc):
    require(set(doc) == {"schema", "sequence", "fps", "native_size", "weight", "images"},
            "Pixel manifest fields differ")
    require(doc["schema"] == "crowd_flow_pixel_inputs_v1", "Unknown pixel manifest")
    development(doc["sequence"])
    require(finite_positive(doc["fps"]), "Positive finite fps required")
    require(len(doc["native_size"]) == 2 and all(type(x) is int and x > 1 for x in doc["native_size"]),
            "native_size is [width,height]")
    binding(doc["weight"])
    require(doc["weight"]["sha256"] == WEIGHT_SHA, "Frozen MOT17 checkpoint SHA required")
    require(isinstance(doc["images"], list) and doc["images"], "Explicit ordered image bindings required")
    paths = set()
    for frame, item in enumerate(doc["images"], 1):
        require(set(item) == {"source_frame", "binding"} and item["source_frame"] == frame,
                "Image manifest must contain every native frame, consecutively from 1")
        binding(item["binding"])
        require(item["binding"]["path"] not in paths, "Duplicate image path")
        paths.add(item["binding"]["path"])
    return doc


def export(manifest_path, output, device):
    manifest_path = Path(manifest_path)
    doc = validate_manifest(load_json(manifest_path))
    output = new_output(output)
    weight = explicit_asset(manifest_path.parent, doc["weight"])
    # No fallback, download, model replacement, preprocessing or threshold changes.
    activate_frozen("src/detect/frozen")
    output.mkdir(parents=True, exist_ok=False)
    runtime_directories(output)
    offline_runtime()
    import cv2
    import r15_yolox82e_detector as detector
    model = detector.load_model(weight, device=device, expected_sha256=WEIGHT_SHA)
    cache = output / "detections.jsonl.gz"
    with gzip.open(cache, "xt", encoding="utf-8", newline="\n") as stream:
        for item in doc["images"]:
            path = explicit_asset(manifest_path.parent, item["binding"])
            image = cv2.imread(str(path), cv2.IMREAD_COLOR)
            require(image is not None, "Image decoding failed: " + item["binding"]["path"])
            require(list(image.shape[:2][::-1]) == doc["native_size"], "Native image size differs")
            result = model.predict_bgr(image)
            detections = []
            for index, box in enumerate(result["boxes_native_xyxy"]):
                detections.append(dict(raw_detection_index=index, box=box.tolist(),
                    objectness=float(result["obj_conf"][index]),
                    class_confidence=float(result["class_conf"][index]),
                    confidence=float(result["score"][index]), class_id=int(result["class_id"][index]),
                    track_id=None))
            frame = item["source_frame"]
            row = dict(frame=frame-1, source_frame=frame, time_s=(frame-1)/doc["fps"],
                       detections=detections, source_image_sha256=item["binding"]["sha256"])
            stream.write(json.dumps(row, allow_nan=False, separators=(",", ":")) + "\n")
    metadata = dict(model.metadata)
    metadata["weight_path"] = doc["weight"]["path"]
    write_json(output / "cache_manifest.json", dict(schema="crowd_flow_yolox_cache_v1",
        sequence=doc["sequence"], fps=doc["fps"], native_size=doc["native_size"],
        frames=len(doc["images"]), source_manifest_sha256=sha(manifest_path),
        cache=dict(path=cache.name, bytes=cache.stat().st_size, sha256=sha(cache)),
        detector=metadata, bitwise_reproducibility_promised=False))
    return {"status": "EXPORTED", "frames": len(doc["images"])}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--device", default="cuda:0")
    p.add_argument("--execute", action="store_true", help="Explicitly load the local model and process listed development images")
    a = p.parse_args(argv)
    if a.execute:
        p.error("--out is required with --execute") if a.out is None else None
        result = export(a.manifest, a.out, a.device)
    else:
        doc = validate_manifest(load_json(a.manifest))
        result = dict(status="MANIFEST_VALIDATED_ONLY", sequence=doc["sequence"],
                      frame_bindings=len(doc["images"]), assets_opened=False, gpu_initialized=False)
    print(json.dumps(result, indent=2))
    return 0
