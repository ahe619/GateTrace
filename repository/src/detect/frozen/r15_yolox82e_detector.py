"""Approved YOLOX-X/MOT17 detector-only adapter for #82e.

Importing this module performs no file I/O, imports no Torch/vendor package,
initializes no CUDA context and changes no environment. The caller owns all
output files, source authorization, dependency setup and downstream tracking.
"""
from __future__ import annotations

import hashlib
from pathlib import Path


UPSTREAM_COMMIT = "d1bf0191adff59bc8fcfeaa0b33d3d1642552a99"
TEST_SIZE = (800, 1440)  # height, width
RGB_MEAN = (0.485, 0.456, 0.406)
RGB_STD = (0.229, 0.224, 0.225)
DETECT_CONF = 0.01  # effective tools/track.py default, not exp.test_conf
NMS_IOU = 0.7


def _floating_dtype_check(model, dtype, stage: str) -> None:
    wrong = [(name, str(value.dtype))
             for name, value in list(model.named_parameters()) + list(model.named_buffers())
             if value.is_floating_point() and value.dtype != dtype]
    if wrong:
        raise RuntimeError(f"{stage}: floating dtype mismatch: {wrong[:10]}")


def build_model():
    """Construct the exact one-class author network on CPU in FP32; no weights."""
    import torch
    from r15_yolox82e_vendor.models.yolo_pafpn import YOLOPAFPN
    from r15_yolox82e_vendor.models.yolo_head import YOLOXHead
    from r15_yolox82e_vendor.models.yolox import YOLOX

    if torch.get_default_dtype() != torch.float32:
        raise RuntimeError("Author construction/fusion requires default dtype float32")
    channels = [256, 512, 1024]
    model = YOLOX(YOLOPAFPN(1.33, 1.25, in_channels=channels),
                  YOLOXHead(1, 1.25, in_channels=channels))
    batchnorms = []
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.BatchNorm2d):
            module.eps = 1e-3
            module.momentum = 0.03
            batchnorms.append((name, module))
    if not batchnorms:
        raise RuntimeError("Expected author BatchNorm2d layers before fusion")
    if any(module.eps != 1e-3 or module.momentum != 0.03 for _, module in batchnorms):
        raise RuntimeError("BN hyperparameters do not match init_yolo")
    model.head.initialize_biases(1e-2)
    model.eval()
    if model.head.num_classes != 1 or not model.head.decode_in_inference:
        raise RuntimeError("Single-class decoded author head required")
    _floating_dtype_check(model, torch.float32, "constructed_model")
    return model


def _sha256(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def load_model(weight, device="cuda:0", *, expected_sha256: str | None = None):
    """Safe FP32 strict load -> GPU FP32 author fusion -> half; no fallback.

    Returns a YOLOX82EDetector with predict_bgr(bgr). The caller must have
    separately approved/bound the checkpoint source and runtime dependencies.
    """
    import torch
    from r15_yolox82e_vendor.fusion import fuse_model
    from r15_yolox82e_vendor.models.network_blocks import BaseConv

    target = torch.device(device)
    if target.type != "cuda":
        raise RuntimeError("Approved FP16 inference path requires CUDA; no CPU/FP32 fallback")
    path = Path(weight).resolve(strict=True)
    weight_sha256 = _sha256(path)
    if expected_sha256 is not None and weight_sha256.lower() != expected_sha256.lower():
        raise RuntimeError("Weight sha256 does not match approved manifest")
    model = build_model()
    # Deliberately no exception handler that retries unsafe deserialization.
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    if not isinstance(checkpoint, dict) or "model" not in checkpoint:
        raise RuntimeError("Expected checkpoint dict with a model state dict")
    state = checkpoint["model"]
    if not isinstance(state, dict):
        raise RuntimeError("checkpoint['model'] must be a state dictionary")
    incompatible = model.load_state_dict(state, strict=True)
    if incompatible.missing_keys or incompatible.unexpected_keys:
        raise RuntimeError("Strict loading unexpectedly returned incompatible keys")
    del checkpoint, state
    model.eval()
    _floating_dtype_check(model, torch.float32, "loaded_before_transfer")
    model.to(target)
    _floating_dtype_check(model, torch.float32, "before_gpu_fusion")
    before = sum(type(module) is BaseConv and hasattr(module, "bn") for module in model.modules())
    if before == 0:
        raise RuntimeError("No unfused author BaseConv layers found")
    with torch.no_grad():
        model = fuse_model(model)
    if any(type(module) is BaseConv and hasattr(module, "bn") for module in model.modules()):
        raise RuntimeError("Author fusion left an unfused BaseConv")
    _floating_dtype_check(model, torch.float32, "after_gpu_fusion")
    model.half()
    model.eval()
    _floating_dtype_check(model, torch.float16, "after_half")
    torch.backends.cudnn.benchmark = True  # match author entry; not a determinism promise
    metadata = {
        "upstream_commit": UPSTREAM_COMMIT, "weight_path": str(path),
        "weight_bytes": path.stat().st_size, "weight_sha256": weight_sha256,
        "strict_missing_keys": 0, "strict_unexpected_keys": 0,
        "baseconv_layers_fused": before, "device": str(target),
        "test_size_hw": list(TEST_SIZE), "conf": DETECT_CONF, "nms_iou": NMS_IOU,
        "model_dtype": "float16", "fusion_dtype": "float32",
        "postprocess_dtype": "float32_after_original_cat",
        "cudnn_benchmark": True, "autocast_used": False,
        "bitwise_reproducibility_promised": False,
    }
    return YOLOX82EDetector(model, target, metadata)


class YOLOX82EDetector:
    """No tracking or event logic; row indices are per-frame pre-M3 indices."""

    def __init__(self, model, device, metadata):
        self.model = model
        self.device = device
        self.metadata = metadata

    def predict_bgr(self, bgr) -> dict:
        import numpy as np
        import torch
        from r15_yolox82e_vendor.preprocess import preproc
        from r15_yolox82e_vendor.postprocess import postprocess

        if not isinstance(bgr, np.ndarray) or bgr.dtype != np.uint8:
            raise TypeError("Expected native cv2 BGR uint8 ndarray")
        if bgr.ndim != 3 or bgr.shape[2] != 3 or min(bgr.shape[:2]) <= 0:
            raise ValueError("Expected non-empty HxWx3 BGR image")
        if self.model.training:
            raise RuntimeError("Model must stay in eval mode")
        prepared, ratio = preproc(bgr, TEST_SIZE, RGB_MEAN, RGB_STD)
        if prepared.shape != (3, *TEST_SIZE) or prepared.dtype != np.float32:
            raise RuntimeError("Author preproc shape/dtype mismatch")
        if not np.isfinite(prepared).all() or not np.isfinite(ratio) or ratio <= 0:
            raise RuntimeError("Non-finite input preprocessing")
        tensor = torch.from_numpy(prepared).unsqueeze(0).to(self.device).half()
        with torch.no_grad():
            output = self.model(tensor)
            expected_proposals = sum((TEST_SIZE[0] // stride) * (TEST_SIZE[1] // stride)
                                     for stride in (8, 16, 32))
            if output.shape != (1, expected_proposals, 6) or output.dtype != torch.float16:
                raise RuntimeError("Author decoded head output shape/dtype mismatch")
            if not torch.isfinite(output).all().item():
                raise RuntimeError("Non-finite decoded detections; no filtering fallback")
            # Original function: half conf_mask, then cat(class_pred.float())
            # promotes seven columns to float32 before NMS. Do not alter this.
            selected = postprocess(output, 1, DETECT_CONF, NMS_IOU)[0]

        if selected is None:
            rows = np.empty((0, 7), dtype=np.float32)
        else:
            if selected.ndim != 2 or selected.shape[1] != 7 or selected.dtype != torch.float32:
                raise RuntimeError("Expected FP32 Nx7 author postprocess output")
            rows = selected.detach().cpu().numpy().copy()
            if not np.isfinite(rows).all() or not np.all(rows[:, 6] == 0):
                raise RuntimeError("Invalid seven-column values or non-person class")
        native = rows[:, :4].copy()
        native /= ratio  # original coordinate frame, no clipping, exactly once
        obj = rows[:, 4].copy()
        cls = rows[:, 5].copy()
        scores = obj * cls  # one semantic product, not product times class again
        indices = np.arange(len(rows), dtype=np.int64)
        return {
            "native_shape_hw": list(bgr.shape[:2]), "scale_ratio": float(ratio),
            "boxes_native_xyxy": native, "obj_conf": obj, "class_conf": cls,
            "score": scores, "class_id": rows[:, 6].astype(np.int64),
            "global_raw_idx": indices, "raw_postprocess_7col_input_px": rows,
            "global_raw_idx_semantics": "per_frame_NMS_output_row_before_M3_filter_not_anchor_index",
            "raw_proposal_count": expected_proposals,
            "output_is_author_none": selected is None,
            "coordinate_contract": "native_0_based_xyxy_no_clipping",
        }
