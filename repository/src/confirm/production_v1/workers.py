"""Hash-bound production orchestration; importing this file does no data I/O.

The algorithms below are loaded from exact frozen source ASTs or pure modules.
This file adds ownership, explicit inputs, receipts and fail-closed validation;
it does not replace detector, association, M4, point or event arithmetic.
Writing this implementation is not evidence of development parity or approval.

Asset contracts (all paths/bytes/SHA256 are explicit manifest bindings):
* seqinfo: original per-sequence INI (25 fps); image_inventory: JSON with
  sequence, images=[{source_frame,path,bytes,sha256}], each also an image asset.
* geometry: {sequence,lines:[six original geometry records]}; g1: the original
  {sequence,coefficients,native_size,fitting_coordinate_range} G1 record.
* detector_parameters / tracker_parameters: exact dictionaries exported below.
* python_module assets: id is the complete import name, including __init__
  packages. No undeclared r15*/sota* import can fall back to the script directory.
* YOLOX consumers require the current export handoff, not an old cache search.
* v11 requires crowddet_cache (complete frames_pre_stitch) and detector_lineage.

No legacy configs, census, saved identity answers, old driver globals, or GT
are opened by these workers. Every dependency opened by a frozen helper still
passes through Ctx's explicit asset gate. Runtime roots are not data read grants.
"""
from __future__ import annotations

import ast
import collections
import configparser
import copy
import gzip
import hashlib
import importlib.abc
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
import types


SOURCE_SHA256 = {
    "code_detector": "2167c6bb02ccb240b479da85ef3e3fd55d9dcb4c6945e32c413b439b1ea1da76",
    "code_observer": "4819bff2f0e4a581ccbc9bd8eea20d767af5baf85d3dead7fe5bd420df81c608",
    "code_cache": "a328c75305e28300f14cb293eae89f40fe80c6127efa52bd266128e7e359f0e4",
    "code_method_tracker": "97f80b90d7bd4dd1fd687d3b5375289ba3f372ec3a172d5e276a9e3877d5c026",
    "code_inference": "4f56e1a23ab81533f120eeb44871a0de00e74946f789cbba4fd99a479cfb0864",
    "code_tracker_backend": "fceb7352bca9c75061371e6c6e27ad8c243a293a770010fae0a5e819a2b97599",
    "code_idxfix": "477c3041fed126903e8e18de967e14da4a98775fef5ac4a4cf48a5eb611ac0d3",
    "code_point_for": "90d81ca958ab21e7e5c99f3a917710520803c7896546e67815c829072a6cc5f5",
    "code_m4": "bcd8e96583f96a0088812c9ea183b1598529d21926edc6b739182f3ffbd165a8",
    "code_events": "14ddf655a5ddf59861ba15fa7b3f712e3234b11b18e33aacf23114817dd924bb",
    "code_panel": "6a485ff44c980635a787f12a76d8e10e4168743e37f85d56aa92c8cdf1f00c7b",
    "code_event_view": "35ed003fd13b4dc4a70b013b012e2e43e5a2b09eed78e8a0ab5573b8edf88c05",
}
GATES = ("H_30", "H_50", "H_70", "V_25", "V_50", "V_75")
DETECTOR_PARAMETERS = {
    "detector": "YOLOX-X", "test_size": [800, 1440], "conf": .01,
    "nms_iou": .7, "max_det": None, "device": "cuda:0",
    "precision": "FP32_load_fuse_then_FP16", "native_fps": 25,
    "coordinate_contract": "native_0_based_xyxy_no_clipping",
    "score_semantics": "FP32 objectness*class_confidence exactly once",
}
V11_PARAMETERS = {
    "tracking_threshold": .1, "native_fps": 25, "tracker_frame_rate": 25,
    "association_parameters": {"tracker_type": "bytetrack", "track_high_thresh": .25,
        "track_low_thresh": .1, "new_track_thresh": .25, "track_buffer": 30,
        "match_thresh": .8, "fuse_score": True},
    "M4": True, "point_source": "box_bottom_center",
    "event_box_source": "raw_detection_box", "identity_box_source": "post_M4_tracker_rows",
}
PANEL_PARAMETERS = {
    "byte": {"track_thresh": .6, "track_buffer": 30, "match_thresh": .9, "mot20": False},
    "oc": {"det_thresh": .6, "max_age": 30, "min_hits": 3, "iou_threshold": .3,
        "delta_t": 3, "asso_func": "iou", "inertia": .2, "use_byte": False},
    "bot": {"track_high_thresh": .6, "track_low_thresh": .1, "new_track_thresh": .7,
        "track_buffer": 30, "match_thresh": .8, "proximity_thresh": .5,
        "appearance_thresh": .25, "cmc_method": "file", "with_reid": False,
        "mot20": False, "ablation": False},
}
ADMISSION = {"byte": .01, "oc": .1, "bot": .09}
YOLOX_WEIGHT_SHA256 = "e3945f3523fde1e107708aacd64dab0670c34e371d136e54587cac7a50d3cfba"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def panel_parameters(method):
    """The manifest must provide this complete fixed dictionary for a panel."""
    return {"author_parameters": copy.deepcopy(PANEL_PARAMETERS[method]),
        "admission_fp16": ADMISSION[method], "native_fps": 25,
        "tracker_frame_rate": None if method == "oc" else 30,
        "empty_admission_update": False, "M4": False,
        "point_source": "box_bottom_center", "identity_box_source": "author_emitted_tracker_xyxy",
        "gmc_policy": "exact_frame_no_seek_skip_fill" if method == "bot" else None}


def _binding_path(ctx, binding):
    p = Path(binding["path"])
    return p.resolve() if p.is_absolute() else (Path(ctx.ROOT) / p).resolve()


def _json_asset(ctx, role, sequence=None, system=None):
    b = ctx.asset(role, sequence=sequence, system=system)
    return ctx.json(_binding_path(ctx, b), expected_sha=b["sha256"], purpose="Explicit " + role)


def _asset_bytes(ctx, binding, purpose):
    raw = ctx.read_bytes(_binding_path(ctx, binding), expected_sha=binding["sha256"], purpose=purpose)
    require(len(raw) == binding["bytes"] and hashlib.sha256(raw).hexdigest() == binding["sha256"],
            "Asset size/SHA changed: " + purpose)
    return raw


def _source(ctx, role, audit):
    binding = ctx.asset(role)
    require(binding["sha256"] == SOURCE_SHA256[role], "Frozen source declaration changed: " + role)
    raw = _asset_bytes(ctx, binding, "Exact frozen source " + role)
    path = str(_binding_path(ctx, binding))
    audit.append({"role": role, "binding": dict(binding), "exact_original_source": True})
    return path, raw


def _ast_module(ctx, role, name, members, audit, injected=None):
    """Compile named original nodes; omit imports, globals with I/O and main."""
    path, raw = _source(ctx, role, audit)
    source = raw.decode("utf-8-sig")
    tree = ast.parse(source, path)
    found = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            found[node.name] = node
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            found[node.targets[0].id] = node
    require(set(members) <= set(found), "Required frozen AST member is absent: " + role)
    selected = [found[key] for key in members]
    # Constants must be literal; evaluating a named old global is not allowed.
    for node in selected:
        if isinstance(node, ast.Assign):
            ast.literal_eval(node.value)
    mod = types.ModuleType(name)
    mod.__file__ = path
    mod.__dict__.update(injected or {})
    exec(compile(ast.Module(body=selected, type_ignores=[]), path, "exec"), mod.__dict__)
    audit[-1]["selected_members"] = [{"name": key,
        "segment_sha256": hashlib.sha256(ast.get_source_segment(source, found[key]).encode("utf-8")).hexdigest()}
        for key in members]
    return mod


def _pure_module(ctx, role, name, audit):
    """Only the allowlisted, SHA-pinned import-safe wrappers may use this path."""
    require(role in {"code_detector", "code_observer", "code_panel", "code_event_view", "code_m4", "code_events"},
            "Not an approved pure wrapper")
    path, raw = _source(ctx, role, audit)
    _assert_import_safe(ast.parse(raw.decode("utf-8-sig"), path))
    audit[-1]["top_level_data_io_absent_static_check"] = True
    mod = types.ModuleType(name)
    mod.__file__ = path
    exec(compile(raw.decode("utf-8-sig"), path, "exec"), mod.__dict__)
    return mod


def _assert_import_safe(tree):
    """Restricted top-level syntax proof, in addition to exact whole-file SHA.

    Method/function bodies are not executed during definition. Their decorators,
    defaults and class bodies ARE checked; import-time calls are allowed only
    for literal dict construction. The allowlisted imports are standard library.
    """
    standard = {"__future__", "ast", "bisect", "collections", "contextlib", "copy",
        "fractions", "hashlib", "importlib", "json", "math", "os", "pathlib", "types", "typing"}
    constants = set()
    def value(node):
        if isinstance(node, ast.Constant):
            return True
        if isinstance(node, ast.Name):
            return node.id in constants
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return all(value(x) for x in node.elts)
        if isinstance(node, ast.Dict):
            return all(k is not None and value(k) and value(v) for k, v in zip(node.keys, node.values))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return value(node.operand)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
            return all(value(x) for x in node.args) and all(k.arg is not None and value(k.value) for k in node.keywords)
        return False
    def statement(node, in_class=False):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return
        if isinstance(node, ast.Pass):
            return
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [x.name for x in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            require(not in_class and all(x.split(".")[0] in standard for x in names), "Unsafe wrapper top-level import")
            return
        if isinstance(node, ast.Assign):
            require(all(isinstance(x, ast.Name) for x in node.targets) and value(node.value), "Unsafe wrapper top-level assignment")
            constants.update(x.id for x in node.targets)
            return
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            require(all(isinstance(d, ast.Name) and d.id in {"property", "staticmethod", "classmethod", "contextmanager"}
                for d in node.decorator_list), "Unsafe wrapper definition decorator")
            defaults = list(node.args.defaults) + [d for d in node.args.kw_defaults if d is not None]
            require(all(value(x) for x in defaults), "Unsafe wrapper definition default")
            return
        if isinstance(node, ast.ClassDef):
            require(not node.decorator_list and not node.keywords and all(isinstance(x, ast.Name) and x.id in
                {"object", "RuntimeError", "Exception"} for x in node.bases), "Unsafe wrapper class construction")
            for child in node.body:
                statement(child, True)
            return
        raise RuntimeError("Executable wrapper top-level statement is forbidden: " + type(node).__name__)
    for node in tree.body:
        statement(node)


def _protected(name):
    return name.startswith(("r15", "sota83"))


class _BoundImports(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Exact manifest import map; no implicit project-file discovery."""
    def __init__(self, ctx, stage, audit):
        self.ctx, self.stage, self.audit = ctx, stage, audit
        self.mapping = {}
        for item in ctx.assets("python_module"):
            name = item["id"]
            require(_protected(name) and name not in self.mapping, "Invalid/duplicate bound module name")
            self.mapping[name] = item["binding"]
        self.installed = []

    def find_spec(self, fullname, path=None, target=None):
        if self.stage == "export_yolox" and fullname.startswith(("ultralytics", "fast_reid", "faiss", "yolox")):
            raise ImportError("Detection export cannot import a tracker or alternate detector: " + fullname)
        if self.stage != "export_yolox" and fullname.startswith(("fast_reid", "faiss", "yolox")):
            raise ImportError("CPU consumer cannot import detector/ReID code: " + fullname)
        if not _protected(fullname):
            if self.stage == "export_yolox" and (fullname == "lap" or fullname.startswith("lap.")):
                raise ImportError("Detection export cannot import LAP")
            return None
        if self.stage == "export_yolox":
            require(fullname.startswith("r15_yolox82e_vendor"), "Export tried to import a tracker/project driver: " + fullname)
        else:
            require(not fullname.startswith(("r15_yolox", "r15e17_crowddet")), "CPU consumer tried to import detector code")
        require(fullname in self.mapping, "Project module lacks explicit binding: " + fullname)
        p = _binding_path(self.ctx, self.mapping[fullname])
        return importlib.util.spec_from_loader(fullname, self, origin=str(p), is_package=p.name == "__init__.py")

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        b = self.mapping[module.__name__]
        p = _binding_path(self.ctx, b)
        raw = _asset_bytes(self.ctx, b, "Bound module " + module.__name__)
        module.__file__ = str(p)
        if p.name == "__init__.py":
            module.__path__ = [str(p.parent)]
        self.installed.append(module.__name__)
        self.audit.append({"role": "python_module", "module": module.__name__, "binding": dict(b)})
        exec(compile(raw.decode("utf-8-sig"), str(p), "exec"), module.__dict__)

    def seed(self, name, module):
        require(name not in sys.modules, "Project module already imported outside source gate: " + name)
        sys.modules[name] = module
        self.installed.append(name)

    def __enter__(self):
        require(not any(_protected(n) for n in sys.modules), "Use a fresh stage process; project modules already imported")
        require(not any(n.startswith(("numpy", "torch", "cv2", "lap", "ultralytics", "fast_reid", "faiss", "yolox"))
            for n in sys.modules), "Use a fresh process before scientific runtime imports")
        if self.stage == "export_yolox":
            require(not any(n == "lap" or n.startswith("lap.") for n in sys.modules), "Export process already contains LAP")
        sys.meta_path.insert(0, self)
        return self

    def __exit__(self, *_):
        sys.meta_path.remove(self)
        for name in reversed(self.installed):
            sys.modules.pop(name, None)


def _runtime_packages(ctx, names):
    for name in names:
        spec = importlib.util.find_spec(name)
        require(spec is not None and spec.origin is not None, "Required installed package absent: " + name)
        ctx.register_runtime_tree(Path(spec.origin).resolve().parent, purpose="Existing locked runtime: " + name)


def _runtime_environment(ctx, request):
    """Retain original thread counts and confine library caches to this unit."""
    threads = 1 if request.system in PANEL_PARAMETERS else 4
    require(ctx.manifest["resources"]["cpu_threads"] >= threads, "CPU-thread budget below frozen runtime requirement")
    folders = {"MPLCONFIGDIR": "matplotlib", "TORCH_HOME": "torch", "YOLO_CONFIG_DIR": "yolo",
               "TEMP": "temp", "TMP": "temp"}
    for name, folder in folders.items():
        path = Path(ctx.out) / "runtime_cache" / folder
        path.mkdir(parents=True, exist_ok=True)
        os.environ[name] = str(path)
    os.environ["MPLBACKEND"] = "Agg"
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = str(threads)
    if request.stage != "export_yolox":
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
    # This is a single-stage process; no post-stage reuse of mutable runtimes.
    return threads


def _begin(ctx, request, expected_stage):
    require(request.stage == expected_stage, "Stage/worker mismatch")
    require(ctx.approval.get("decision") == "APPROVE_EXECUTION", "Independent execution approval is missing")
    require(request.sequence in ("MOT20-01", "MOT20-02", "MOT20-03", "MOT20-05"), "Invalid sequence")
    if expected_stage == "consume" and request.system in ("v11", "yolox_v11"):
        require(ctx.approval.get("m4_policy_interpretation") == "preparation_scope_header_separate_execution_authorization",
                "M4 policy interpretation must be resolved before any sequence asset is read")
    ctx.budget.check("before " + expected_stage)
    require(not (Path(ctx.out) / "worker_complete.json").exists(), "Output completion already exists")


def _metadata(ctx, sequence):
    b = ctx.asset("seqinfo", sequence=sequence)
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(_asset_bytes(ctx, b, "Explicit sequence metadata").decode("utf-8-sig"))
    s = parser["Sequence"]
    require(s["name"] == sequence, "seqinfo name differs")
    require(s["imDir"] == "img1" and s["imExt"].lower() == ".jpg", "Unexpected source image convention")
    meta = {"sequence": sequence, "fps": s.getint("frameRate"), "width": s.getint("imWidth"),
            "height": s.getint("imHeight"), "seqLength": s.getint("seqLength")}
    require(meta["fps"] == 25 and min(meta[k] for k in ("width", "height", "seqLength")) > 0, "Invalid native metadata")
    meta["nb_frames"] = meta["seqLength"]
    return meta


def _write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def _line(stream, obj):
    stream.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n")


def _file(ctx, path, role, sequence, system, identifier=None):
    return {"id": identifier or role, "role": role, "sequence": sequence, "system": system,
            "binding": ctx.record_output(Path(path), role)}


def _rows(ctx, binding, purpose):
    path = _binding_path(ctx, binding)
    ctx.verified_stream(path, expected_sha=binding["sha256"], purpose=purpose)
    try:
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            for line in stream:
                ctx.budget.check(purpose)
                require(bool(line.strip()), "Blank cache/frame line")
                yield json.loads(line)
    finally:
        ctx.verified_stream(path, expected_sha=binding["sha256"], purpose=purpose + " after read")


def _lineage(ctx):
    return {"manifest_sha256": ctx.manifest_sha256, "freeze_sha256": ctx.freeze_sha256,
            "approval_sha256": ctx.approval_sha256}


def _finish(ctx, request, complete, files):
    complete.update(schema="r15_confirmation85_" + request.stage + "_complete_v1",
        complete=True, status="COMPLETE", stage=request.stage, sequence=request.sequence,
        system=request.system, files=files, **_lineage(ctx))
    # The outer runner owns complete.json and closes its read ledger afterwards.
    path = Path(ctx.out) / "worker_complete.json"
    _write_json(path, complete)
    completion = _file(ctx, path, "complete", request.sequence, request.system)
    handoff = {"schema": "r15_confirmation85_runtime_handoff_v1", "complete": True,
        "stage": request.stage, "sequence": request.sequence, "system": request.system,
        "files": files + [completion], **_lineage(ctx)}
    hp = Path(ctx.out) / "handoff.json"
    _write_json(hp, handoff)
    return {**complete, "domain_completion": completion["binding"], "handoff": ctx.record_output(hp, "handoff")}


def _image_inventory(ctx, sequence, meta):
    inventory = _json_asset(ctx, "image_inventory", sequence)
    require(inventory["sequence"] == sequence, "Image inventory sequence differs")
    images = inventory["images"]
    require(len(images) == meta["seqLength"], "Image inventory is not complete")
    declared = {_binding_path(ctx, x["binding"]): x["binding"] for x in ctx.assets("image", sequence=sequence)}
    require(len(declared) == len(images), "Image assets must exactly match complete inventory")
    for index, item in enumerate(images):
        require(item["source_frame"] == index + 1, "Image inventory frame order differs")
        b = {k: item[k] for k in ("path", "bytes", "sha256")}
        require(declared.get(_binding_path(ctx, b)) == b, "Image inventory lacks exact manifest binding")
    return images


def export_yolox(ctx, request):
    """One approved sequence, one detector export; no tracker dependency."""
    _begin(ctx, request, "export_yolox")
    require(request.system is None, "Export system must be null")
    seq, out, audit = request.sequence, Path(ctx.out), []
    meta = _metadata(ctx, seq)
    require(_json_asset(ctx, "detector_parameters") == DETECTOR_PARAMETERS, "Detector parameters changed")
    images = _image_inventory(ctx, seq, meta)
    weight = ctx.asset("detector_weight")
    require(weight["sha256"] == YOLOX_WEIGHT_SHA256, "YOLOX checkpoint differs from frozen detector")
    # Hash before any torch load; the exact loader hashes again immediately before use.
    ctx.verified_stream(_binding_path(ctx, weight), expected_sha=weight["sha256"], purpose="Declared YOLOX checkpoint")
    started = time.perf_counter()
    with _BoundImports(ctx, "export_yolox", audit):
        threads = _runtime_environment(ctx, request)
        _runtime_packages(ctx, ("numpy", "torch", "torchvision", "cv2", "loguru"))
        import numpy as np
        import torch
        import cv2
        torch.set_num_threads(threads)
        torch.set_num_interop_threads(1)
        cv2.setNumThreads(0)
        dm = _pure_module(ctx, "code_detector", "_production_detector", audit)
        om = _pure_module(ctx, "code_observer", "_production_observer", audit)
        detector = dm.load_model(_binding_path(ctx, weight), device="cuda:0", expected_sha256=weight["sha256"])
        torch.cuda.reset_peak_memory_stats()
        totals = collections.Counter()
        cache_path = out / "detections.jsonl.gz"
        with gzip.open(cache_path, "xt", encoding="utf-8", compresslevel=6) as stream:
            for frame, item in enumerate(images):
                ctx.budget.check("export frame")
                binding = {k: item[k] for k in ("path", "bytes", "sha256")}
                payload = _asset_bytes(ctx, binding, "Approved native image")
                image = cv2.imdecode(np.frombuffer(payload, np.uint8), cv2.IMREAD_COLOR)
                require(image is not None and image.shape == (meta["height"], meta["width"], 3), "Image shape mismatch")
                with om.Observer(detector) as observer:
                    result, dtype = observer.predict(image)
                require(dtype["validated"] and dtype["wrappers_restored"], "Dtype observation incomplete")
                n = len(result["score"])
                for key in ("obj_conf", "class_conf", "score", "class_id", "global_raw_idx"):
                    require(result[key].shape == (n,) and np.isfinite(result[key]).all(), "Invalid detector vector: " + key)
                require(result["boxes_native_xyxy"].shape == (n, 4) and result["raw_postprocess_7col_input_px"].shape == (n, 7), "Invalid detector matrix")
                require(np.isfinite(result["boxes_native_xyxy"]).all(), "Nonfinite native box")
                require(np.array_equal(result["global_raw_idx"], np.arange(n)) and np.all(result["class_id"] == 0), "Index/class changed")
                detections = [dict(raw_detection_index=i, box=result["boxes_native_xyxy"][i].tolist(),
                    confidence=float(result["score"][i]), class_id=0, pose_available=False, keypoints=None,
                    track_id=None, objectness=float(result["obj_conf"][i]),
                    class_confidence=float(result["class_conf"][i]), global_raw_idx=i) for i in range(n)]
                frame_meta = {k: copy.deepcopy(result[k]) for k in ("native_shape_hw", "scale_ratio",
                    "global_raw_idx_semantics", "raw_proposal_count", "output_is_author_none", "coordinate_contract")}
                frame_meta.update(detector_conf=.01, detector_nms_iou=.7, max_det=None,
                    score_semantics=DETECTOR_PARAMETERS["score_semantics"])
                _line(stream, dict(sequence=seq, frame=frame, source_frame=frame + 1, time_s=frame / 25,
                    native_shape_hw=[meta["height"], meta["width"]], detections=detections,
                    detector_frame_metadata=frame_meta, dtype_observation=dtype, input_image=binding))
                totals.update(raw_boxes=n, frames=1)
        detector_metadata = copy.deepcopy(detector.metadata)
        peak = torch.cuda.max_memory_allocated()
    files = [_file(ctx, cache_path, "yolox_cache", seq, None)]
    ap = out / "source_audit.json"
    _write_json(ap, {"sources": audit, "scientific_arithmetic_reimplemented": False})
    files.append(_file(ctx, ap, "source_audit", seq, None))
    return _finish(ctx, request, {"metadata": meta, "detector_metadata": detector_metadata,
        "weight": weight, "totals": dict(totals), "elapsed_s": time.perf_counter() - started,
        "actual_cpu_threads": threads, "peak_gpu_bytes": peak, "no_tracking": True, "no_GT_read": True}, files)


def _export_cache(ctx, request, meta, np, audit):
    require(request.handoff is not None and request.handoff_sha256 is not None, "YOLOX consumer needs current export handoff")
    handoff = ctx.json(request.handoff, expected_sha=request.handoff_sha256, purpose="Verified current export handoff")
    require(handoff["schema"] == "r15_confirmation85_runtime_handoff_v1" and handoff["complete"] is True,
            "Incomplete cache handoff")
    require(handoff["stage"] == "export_yolox" and handoff["sequence"] == request.sequence and handoff["system"] is None,
            "Cache producer/scope mismatch")
    require(all(handoff[k] == v for k, v in _lineage(ctx).items()), "Handoff manifest/freeze mismatch")
    def pick(role):
        items = [x for x in handoff["files"] if x["role"] == role and x["sequence"] == request.sequence and x["system"] is None]
        require(len(items) == 1, "Missing/duplicate cache handoff role: " + role)
        b = items[0]["binding"]
        ctx.admit_generated(b, request.handoff_sha256, "Current export " + role)
        return b
    cb, done = pick("yolox_cache"), pick("complete")
    complete = ctx.json(_binding_path(ctx, done), expected_sha=done["sha256"], purpose="Export completion")
    require(complete["complete"] is True and complete["metadata"] == meta, "Export completion metadata mismatch")
    require(complete["totals"]["frames"] == meta["seqLength"], "Export completion frame count differs")
    require(any(x["role"] == "yolox_cache" and x["binding"] == cb for x in complete["files"]), "Cache is not in producer completion")
    image_refs = _image_inventory(ctx, request.sequence, meta)
    def cache_rows(_path):
        for index, row in enumerate(_rows(ctx, cb, "Read approved detector cache")):
            require(index < len(image_refs), "Extra cache frame")
            require(row["dtype_observation"]["validated"] is True and row["dtype_observation"]["wrappers_restored"] is True,
                    "Cache dtype observation missing")
            require(row["input_image"] == {k: image_refs[index][k] for k in ("path", "bytes", "sha256")}, "Cache source image binding differs")
            yield row
    mod = _ast_module(ctx, "code_cache", "_production_cache", ["Cache"], audit,
        {"rows_from_gzip": cache_rows, "require": require, "copy": copy, "math": math})
    return mod.Cache(_binding_path(ctx, cb), meta, complete["detector_metadata"], np), cb


def _geometry(ctx, sequence, meta, event_mod):
    geometry = _json_asset(ctx, "geometry", sequence)
    g1 = _json_asset(ctx, "g1", sequence)
    require(geometry["sequence"] == sequence and g1["sequence"] == sequence, "Geometry/G1 scope differs")
    geoms = geometry["lines"]
    require(tuple(g["line_id"] for g in geoms) == GATES and all(g["sequence"] == sequence for g in geoms), "Six gate order/scope differs")
    require(g1["native_size"] == [meta["width"], meta["height"]], "G1 native size differs")
    ranges = g1["fitting_coordinate_range"]
    if set(ranges) == {"x_normalized", "y_top_normalized"}:
        ranges = {"head_x_norm": ranges["x_normalized"], "head_y_norm": ranges["y_top_normalized"]}
    model = event_mod.make_height_model(g1["coefficients"], ranges)
    return g1, geoms, model


def _events(ctx, request, meta, geoms, model, api, observations, files):
    counts = []
    for geom in geoms:
        lid = geom["line_id"]
        ctx.budget.check("event extraction " + lid)
        result = api.evaluate_sequence_gate(observations, sequence=request.sequence, gate_id=lid,
            width=meta["width"], height=meta["height"], nb_frames=meta["seqLength"], fps=25,
            model=model, polygons=geom["polygons"])
        points = result.pop("observations")
        folder = Path(ctx.out) / "gates" / lid
        folder.mkdir(parents=True, exist_ok=False)
        pp, ep = folder / "points.jsonl.gz", folder / "events.json"
        with gzip.open(pp, "xt", encoding="utf-8") as stream:
            for point in points:
                _line(stream, point)
        _write_json(ep, result)
        files.extend([_file(ctx, ep, "gate_events", request.sequence, request.system, "gate_events:" + lid),
                      _file(ctx, pp, "gate_points", request.sequence, request.system, "gate_points:" + lid)])
        counts.append(dict(gate_id=lid, raw_candidates=len(result["raw_candidates"]),
            confirmed=len(result["raw_confirmed_events"]), final=len(result["final_events"])))
    return counts


def _consume_v11(ctx, request, meta, cache, np, imports, audit, point_for, g1, geoms):
    require(ctx.approval.get("m4_policy_interpretation") == "preparation_scope_header_separate_execution_authorization",
            "M4 no_test_set_execution policy interpretation has not been explicitly decided")
    require(_json_asset(ctx, "tracker_parameters", system=request.system) == V11_PARAMETERS, "v11 parameters changed")
    # Both files are explicit assets even though the frozen loader reads them by
    # its original source-relative paths; Ctx checks path membership again.
    for role in ("code_tracker_backend", "code_idxfix"):
        path, raw = _source(ctx, role, audit)
        if role == "code_tracker_backend":
            _assert_import_safe(ast.parse(raw.decode("utf-8-sig"), path))
            audit[-1]["top_level_data_io_absent_static_check"] = True
    inference = _ast_module(ctx, "code_inference", "r15e24_inference",
        ["SEED", "TRACKER_ADAPTER_SHA", "IDXFIX_SHA", "_require", "_root", "_bound_bytes",
         "_load_adapter", "_register_packages", "_seed", "_native_bgr", "ByteTrackTracker"], audit)
    imports.seed("r15e24_inference", inference)
    tracker_mod = _ast_module(ctx, "code_method_tracker", "_production_method_tracker",
        ["VARIANTS", "RAW_REUSE_VARIANTS", "spec", "MethodTracker", "fresh_raw"], audit,
        {"require": require, "copy": copy, "math": math,
         "FROZEN": {"r15_tracker_idxfix.py": SOURCE_SHA256["code_idxfix"]}})
    m4 = _pure_module(ctx, "code_m4", "_production_m4", audit)
    policy = _json_asset(ctx, "m4_policy")
    tracker = tracker_mod.MethodTracker(ctx, .1)
    require(dict(tracker.base.backend.args) == V11_PARAMETERS["association_parameters"], "Actual tracker arguments changed")
    raw_binding = ctx.asset("crowddet_cache", sequence=request.sequence, system="v11") if cache is None else None
    saved = iter(_rows(ctx, raw_binding, "Explicit complete CrowdDet raw replay")) if raw_binding else None
    detector_metadata = _json_asset(ctx, "detector_lineage", sequence=request.sequence, system="v11") if saved is not None else cache.metadata
    if saved is not None:
        require(detector_metadata["kind"] == "P2" and detector_metadata["raw_threshold"] == "score > 0.01"
            and detector_metadata["max_det"] is None, "CrowdDet raw lineage is not the frozen P2 detector")
        author = detector_metadata["author"]
        require(author["short_size"] == 1280 and author["max_size"] == 2240 and author["set_nms_threshold"] == .5,
            "CrowdDet author parameter lineage differs")
    pre = Path(ctx.out) / "frames_pre_stitch.jsonl.gz"
    totals = collections.Counter()
    with gzip.open(pre, "xt", encoding="utf-8") as stream:
        for frame in range(meta["seqLength"]):
            ctx.budget.check("v11 frame")
            if saved is not None:
                row = next(saved)
                require(row["frame"] == frame and row["source_frame"] == frame + 1 and row["time_s"] == frame / 25, "CrowdDet replay frame/time mismatch")
                raw = tracker_mod.fresh_raw(row["detections"])
                dm = copy.deepcopy(row.get("detector_frame_metadata") or {})
            else:
                raw, dm = cache.next(request.sequence, frame)
            detections, tracker_rows = tracker.update(raw, (meta["height"], meta["width"]))
            for detection in detections:
                point, reason, outside = point_for(detection["box"], meta["width"], meta["height"])
                detection.update(frame=frame, source_frame=frame + 1, point=point,
                    point_source="box_bottom_center", point_invalid_reason=reason, point_outside_image=outside)
            _line(stream, dict(frame=frame, source_frame=frame + 1, time_s=frame / 25,
                detections=detections, tracker_rows=tracker_rows, detector_frame_metadata=dm,
                tracker_frame_metadata=tracker.last_frame_metadata))
            totals.update(frames=1, raw_boxes=len(detections),
                tracker_input_boxes=sum(d["tracking_eligible"] for d in detections),
                low_pool_input_boxes=sum(.1 <= d["confidence"] < .25 for d in detections))
    if saved is not None:
        require(next(saved, None) is None, "Extra CrowdDet source frame")
    else:
        cache.finish()
    pre_item = _file(ctx, pre, "frames_pre_stitch", request.sequence, request.system)
    stitch = m4.stitch_frame_rows(_rows(ctx, pre_item["binding"], "New pre-M4 frames"),
        namespace={"sequence": request.sequence, "block": "full_sequence"}, fps=25,
        gates=geoms, g1=g1, clarification=policy, checkpoint=ctx.budget.check)
    frames = stitch.pop("frames")
    sp, fp = Path(ctx.out) / "stitch.json", Path(ctx.out) / "frames.jsonl.gz"
    _write_json(sp, stitch)
    observations, track_ids = [], set()
    with gzip.open(fp, "xt", encoding="utf-8") as stream:
        for frame, row in enumerate(frames):
            ctx.budget.check("serialize M4 output")
            require(row["frame"] == frame and row["source_frame"] == frame + 1, "M4 frame order changed")
            _line(stream, row)
            for detection in row["detections"]:
                if detection.get("track_id") is not None:
                    require("original_track_id" in detection, "Missing pre-M4 ID")
                    track_ids.add(detection["track_id"])
                    # Event path intentionally remains raw detection feet. The
                    # scorer independently uses the actual post-M4 tracker_rows.
                    observations.append({k: detection[k] for k in ("frame", "source_frame", "track_id",
                        "box", "confidence", "raw_detection_index", "point", "point_source")})
    require(len(frames) == meta["seqLength"], "M4 did not preserve complete frames")
    files = [pre_item, _file(ctx, fp, "frames", request.sequence, request.system),
             _file(ctx, sp, "stitch", request.sequence, request.system)]
    detail = {"frame_format": "idxfix_post_m4", "tracker_metadata": tracker.metadata,
        "detector_metadata": detector_metadata, "totals": dict(totals), "M4_pairs": len(stitch["links"]),
        "unique_track_ids": len(track_ids), "event_box_source": "raw_detection_box",
        "identity_box_source": "post_M4_tracker_rows",
        "configuration": tracker_mod.spec("v11_P2_M3_M4") if saved is not None else None,
        "detector_substitution": None if saved is not None else "YOLOX-X instead of CrowdDet; same v11 association and M4"}
    return files, observations, detail


def _consume_panel(ctx, request, meta, cache, audit, point_for):
    system = request.system
    require(_json_asset(ctx, "tracker_parameters", system=system) == panel_parameters(system), "Panel parameters changed")
    panel = _pure_module(ctx, "code_panel", "_production_panel", audit)
    event_view = _pure_module(ctx, "code_event_view", "_production_event_view", audit).event_view
    require(panel.PARAMETERS == PANEL_PARAMETERS and panel.ADMISSION == ADMISSION, "Panel source parameter contract differs")
    files, bot_root = [], None
    if system == "bot":
        b = ctx.asset("bot_gmc", sequence=request.sequence, system="bot")
        payload = _asset_bytes(ctx, b, "Explicit current-sequence GMC; no discovery or extraction")
        bot_root = Path(ctx.out) / "gmc_sandbox"
        path = bot_root / "tracker" / "GMC_files" / "MOTChallenge" / ("GMC-" + request.sequence + ".txt")
        path.parent.mkdir(parents=True, exist_ok=False)
        with path.open("xb") as stream:
            stream.write(payload)
        files.append(_file(ctx, path, "bot_gmc_materialized", request.sequence, system))
    tracker = panel.PanelTracker(system, request.sequence, (meta["height"], meta["width"]),
        bot_root=bot_root, package="sota83d.vendor")
    observations, totals, track_ids = [], collections.Counter(), set()
    fp = Path(ctx.out) / "observations.jsonl.gz"
    try:
        with gzip.open(fp, "xt", encoding="utf-8") as stream:
            for frame in range(meta["seqLength"]):
                ctx.budget.check("panel frame")
                raw, _dm = cache.next(request.sequence, frame)
                actual = tracker.update(raw, frame + 1)
                actual.update(method_id=system, sequence=request.sequence, frame=frame, source_frame=frame + 1, time_s=frame / 25)
                for output in actual["outputs"]:
                    point, reason, outside = point_for(output["box"], meta["width"], meta["height"])
                    output.update(point=point, point_source="box_bottom_center", point_invalid_reason=reason, point_outside_image=outside)
                    observations.append(event_view(output, frame))
                    track_ids.add(output["track_id"])
                _line(stream, actual)
                totals.update(frames=1, raw_boxes=len(raw), tracker_input_boxes=len(actual["admission_raw_indices"]),
                    outputs=len(actual["outputs"]), update_calls=int(actual["update_called"]))
        cache.finish()
        tracker_metadata = {"author_parameters": tracker.args, "internal_frame": tracker.internal_frame,
            "calls": tracker.calls, "native_fps": 25, "constructor_frame_rate": None if system == "oc" else 30,
            "empty_admission_update": False, "M4": False,
            "gmc_calls": tracker.gmc.calls if tracker.gmc is not None else None}
    finally:
        tracker.close()
    files.append(_file(ctx, fp, "frames", request.sequence, system))
    return files, observations, {"frame_format": "panel_outputs", "tracker_metadata": tracker_metadata,
        "detector_metadata": cache.metadata, "totals": dict(totals), "unique_track_ids": len(track_ids),
        "event_box_source": "author_emitted_tracker_xyxy", "identity_box_source": "author_emitted_tracker_xyxy"}


def consume(ctx, request):
    """One independently reset CPU consumer; event and identity paths stay distinct."""
    _begin(ctx, request, "consume")
    require(request.system in ("yolox_v11", "v11", "byte", "oc", "bot"), "Unsupported consumer")
    seq, audit = request.sequence, []
    meta = _metadata(ctx, seq)
    started = time.perf_counter()
    with _BoundImports(ctx, "consume", audit) as imports:
        threads = _runtime_environment(ctx, request)
        names = ("numpy", "torch", "cv2", "scipy", "lap", "yaml", "ultralytics") if request.system in ("v11", "yolox_v11") else ("numpy", "torch", "cv2", "scipy", "lap", "filterpy", "matplotlib")
        _runtime_packages(ctx, names)
        import numpy as np
        import torch
        import cv2
        torch.set_num_threads(threads)
        torch.set_num_interop_threads(1)
        cv2.setNumThreads(0)
        point_for = _ast_module(ctx, "code_point_for", "_production_point", ["point_for"], audit, {"math": math}).point_for
        event_mod = _pure_module(ctx, "code_events", "_production_events", audit)
        api = event_mod.load_frozen(ctx.read_bytes, ctx.ROOT, numpy_module=np)
        g1, geoms, model = _geometry(ctx, seq, meta, event_mod)
        cache, cache_binding = (None, None) if request.system == "v11" else _export_cache(ctx, request, meta, np, audit)
        if request.system in ("v11", "yolox_v11"):
            files, observations, detail = _consume_v11(ctx, request, meta, cache, np, imports, audit, point_for, g1, geoms)
        else:
            files, observations, detail = _consume_panel(ctx, request, meta, cache, audit, point_for)
        counts = _events(ctx, request, meta, geoms, model, api, observations, files)
        event_audit = api.function_audit
    ap = Path(ctx.out) / "source_audit.json"
    _write_json(ap, {"sources": audit, "frozen_event_functions": event_audit,
        "scientific_arithmetic_reimplemented": False, "new_orchestration_requires_development_regression": True})
    files.append(_file(ctx, ap, "source_audit", seq, request.system))
    return _finish(ctx, request, {"metadata": meta, "gate_counts": counts,
        "elapsed_s": time.perf_counter() - started, "cache_binding": cache_binding,
        "actual_cpu_threads": threads, "no_GT_read": True, "no_scoring": True, **detail}, files)
