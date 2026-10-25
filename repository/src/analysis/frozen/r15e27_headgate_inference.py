"""Prepared HeadGate stream integration; no top-level I/O or real-data runner.

Caller responsibilities: native frame decoding, source authorization/auditing,
loading already-frozen calibration/geometry/model dictionaries, detector weight
loading, runtime/cache policy and persistence. No fitting, scoring or labels are
used here. A lazy detector is optional when detections are supplied in memory.

MOT uses a head-box bottom anchor and calibration.json coefficients_a_b. Stadium
requires explicit anchor='head_box_center_proxy': its existing affine model was
fit to a mean of pose head keypoints, NOT to a head-box center or bottom. This
proxy is an uncalibrated anchor approximation, not an exact reuse or a claimed
performance improvement. No fallback anchor is chosen automatically.

The MOT executor bridges the E24 frozen sequence/gate API. The stadium executor
bridges the multi-camera E17 run adapter, preserving its independent processing
and evaluation grouping. Neither bridge constructs an old I/O-owning runner.
Synthetic validation does not validate a real detector, tracker runtime, actual
calibration artifact, actual stadium geometry or held-out-video performance.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import math
from pathlib import Path
import types


BYTE_PARAMETERS = dict(tracker_type="bytetrack", track_high_thresh=.25,
    track_low_thresh=.1, new_track_thresh=.25, track_buffer=30,
    match_thresh=.8, fuse_score=True)
TRACKER_SOURCE_SHA = "fceb7352bca9c75061371e6c6e27ad8c243a293a770010fae0a5e819a2b97599"
TRACKER_SOURCE = "scripts/r15e17_trackers.py"
C1_KEY = "C1_q0p2_observed"
STADIUM_PROXY_LIMITATION = (
    "The frozen stadium model expects the mean of valid pose head keypoints "
    "0-4. A head-box center is only a proxy; its anchor error is not calibrated "
    "or validated, and these projected feet are not equivalent to pose input.")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def _box(box):
    require(isinstance(box, (list, tuple)) and len(box) == 4, "Native xyxy box required")
    require(all(finite(x) for x in box), "Finite numeric native box required")
    box = list(map(float, box))
    require(box[0] < box[2] and box[1] < box[3], "Positive head-box width and height required")
    return box


class LazyHeadDetector:
    """loader(weights_path) -> callable(image) or object with predict(image).

    Construction neither opens the path nor loads weights. The caller-supplied
    loader is invoked on the first predict call, once per instance. Its output
    must already be native xyxy dictionaries with confidence and class_id.
    This interface does not guess resize/unletterbox rules for an arbitrary
    detector and never downloads or installs a model.
    """

    def __init__(self, weights_path, loader):
        require(callable(loader), "Explicit callable detector loader required")
        self.weights_path = weights_path
        self.loader = loader
        self.backend = None
        self.calls = 0

    def predict(self, image):
        if self.backend is None:
            backend = self.loader(self.weights_path)
            require(callable(backend) or callable(getattr(backend, "predict", None)),
                    "Detector loader must return a callable or predict object")
            self.backend = backend
        self.calls += 1
        function = self.backend.predict if callable(getattr(self.backend, "predict", None)) else self.backend
        return function(image)

    def metadata(self):
        return dict(lazy=True, loaded=self.backend is not None, prediction_calls=self.calls,
                    weight_reference=str(self.weights_path), coordinate_contract="caller-normalized native xyxy",
                    loading_and_download_policy="caller loader responsibility; this module never downloads")


def make_frozen_bytetrack(gate, project_root, fps):
    """Explicit runtime construction of the existing P1-parameter idxfix tracker.

    SmokeTracker calls this ByteTrack branch 'P2'; the name selects the identical
    frozen P1 ByteTrack parameters, not a detector. The gate owns source/runtime
    reads. Installed dependencies must already exist. Calling this function is
    a real runtime action; preparation and synthetic tests need not call it.
    """
    path = Path(project_root) / TRACKER_SOURCE
    raw = gate.read(path, expected_sha=TRACKER_SOURCE_SHA,
                    purpose="HeadGate reuse of frozen ByteTrack idxfix adapter")
    require(isinstance(raw, bytes) and hashlib.sha256(raw).hexdigest() == TRACKER_SOURCE_SHA,
            "Pinned tracker adapter source mismatch")
    module = types.ModuleType("_r15e27_pinned_bytetrack")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    require(module.BYTE_DEFAULTS == BYTE_PARAMETERS, "Frozen ByteTrack defaults differ")
    return module.SmokeTracker(kind="P2", fps=fps, gate=gate)


class HeadProjection:
    """Explicit, immutable-in-use head anchor and already-frozen projection."""

    def __init__(self, *, mode, anchor, size, calibration=None, pose_model=None):
        require(len(size) == 2 and all(type(x) is int and x > 1 for x in size), "Native (W,H) required")
        self.size = list(size)
        self.mode, self.anchor = mode, anchor
        self.pose_model = deepcopy(pose_model)
        if mode == "mot":
            require(anchor == "head_box_bottom_center", "MOT calibration requires head_box_bottom_center")
            require(isinstance(calibration, dict), "Already-loaded MOT calibration.json dictionary required")
            coefficients = calibration.get("coefficients_a_b")
            require(isinstance(coefficients, (list, tuple)) and len(coefficients) == 2
                    and all(finite(x) for x in coefficients), "Finite calibration coefficients_a_b required")
            self.coefficients = list(map(float, coefficients))
            self.limitations = ["Uses supplied frozen MOT calibration; no refitting or independent generalization validation."]
        elif mode == "stadium":
            require(anchor == "head_box_center_proxy", "Stadium requires explicit head_box_center_proxy acknowledgement")
            require(isinstance(pose_model, dict) and pose_model.get("available") is True,
                    "Available frozen stadium pose-head model required")
            coefficients = pose_model.get("coefficients")
            require(isinstance(coefficients, (list, tuple)) and len(coefficients) == 3
                    and all(finite(x) for x in coefficients), "Three finite frozen pose-model coefficients required")
            self.coefficients = list(map(float, coefficients))
            self.limitations = [STADIUM_PROXY_LIMITATION]
        else:
            raise ValueError("Projection mode must be mot or stadium")

    def point(self, detection):
        x0, y0, x1, y1 = _box(detection["box"])
        width, height = self.size
        x = (x0+x1)/2
        if self.mode == "mot":
            anchor = [x, y1]
            a, b = self.coefficients
            offset = a*(y1-y0)+b
            point = [x, y1+offset]
            invalid = x0 <= 0 or x1 >= width-1 or y1 >= height-1 or not (0 < point[0] < width-1 and 0 < point[1] < height-1)
            reason = "MOT_boundary_or_projected_foot_invalid" if invalid else None
            source = "head_bottom_MOT_frozen_projection"
        else:
            anchor = [x, (y0+y1)/2]
            a, b, c = self.coefficients
            offset = a+b*anchor[0]/width+c*anchor[1]/height
            point = [anchor[0], anchor[1]+offset]
            invalid = not math.isfinite(offset) or offset <= 0
            reason = "pose_proxy_height_nonpositive_or_nonfinite" if invalid else None
            source = "head_box_center_proxy_for_pose_head_mean"
        if not all(math.isfinite(x) for x in point):
            invalid, reason = True, "projected_point_nonfinite"
        outside = not (0 <= point[0] < width and 0 <= point[1] < height) if not invalid else False
        return dict(point=None if invalid else point, point_source=source,
                    exclusion_reason=reason, out_of_frame=outside, anchor_xy=anchor,
                    anchor_kind=self.anchor, predicted_height_px=offset if math.isfinite(offset) else None,
                    anchor_is_proxy=self.mode == "stadium")

    def metadata(self):
        return dict(mode=self.mode, anchor=self.anchor, native_size=self.size,
                    coefficients=self.coefficients,
                    original_model_anchor="mean_pose_head_keypoints_0_to_4" if self.mode == "stadium" else "head_box_bottom_center",
                    boundary_policy="retain_finite_out_of_frame_like_E17" if self.mode == "stadium" else "MOT_head_box_and_projected_foot_boundary_mask",
                    limitations=list(self.limitations))


def _check_result(result, keys):
    require(isinstance(result, dict), "Frozen executor must return a dictionary")
    require(all(key in result for key in keys), "Frozen extraction/C1/R1R2 evidence fields missing")
    require(all(isinstance(result[key], list) for key in keys), "Frozen evidence stages must be lists")
    for event in result["final_events"]:
        require(all(key in event for key in ("track_id", "direction", "time_s", "crossing_position_native_px")),
                "Final event lacks identity, direction, clock or scoring position")


class MOTEventExecutor:
    """Bridge an already-loaded E24 FrozenEvents; whole native sequence only."""

    mode = "mot"

    def __init__(self, frozen_events, *, sequence, gates, model):
        require(callable(getattr(frozen_events, "evaluate_sequence_gate", None)), "E24 frozen event API required")
        require(isinstance(sequence, str) and bool(sequence), "Explicit sequence identifier required")
        self.engine, self.sequence = frozen_events, sequence
        self.gates, self.model = deepcopy(gates), deepcopy(model)
        require(bool(self.gates) and len({g["line_id"] for g in self.gates}) == len(self.gates), "Unique nonempty gate list required")

    def finalize(self, raw_rows, point_rows, source, metadata):
        start, end = metadata["source_interval_half_open"]
        require(start == 0 and metadata["evaluation_source_interval_half_open"] == [start, end],
                "MOT E24 bridge requires complete sequence, not an implicitly truncated evaluation window")
        require(metadata["fps"] == 25, "MOT E24 event API requires 25 fps")
        observations = []
        for raw, points in zip(raw_rows, point_rows):
            for detection, projected in zip(raw["detections"], points["detections"]):
                if detection["track_id"] is not None:
                    point = projected["versions"]["hybrid"]
                    observations.append(dict(frame=raw["frame"], track_id=detection["track_id"],
                        raw_detection_index=detection["raw_detection_index"], box=deepcopy(detection["box"]),
                        confidence=detection["confidence"], point=deepcopy(point["point"]), point_source=point["point_source"]))
        outputs = {}
        for gate in self.gates:
            result = self.engine.evaluate_sequence_gate(observations, sequence=self.sequence, gate_id=gate["line_id"],
                width=metadata["width"], height=metadata["height"], nb_frames=end, fps=25,
                model=self.model, polygons=gate["polygons"])
            _check_result(result, ("raw_candidates", "c1_evidence", "raw_confirmed_events", "groups", "group_details", "final_events"))
            require(result.get("dedup_variant") == "R1+R2", "MOT executor dedup variant differs")
            require(result["event_parameters"]["conditions"] == [dict(key=C1_KEY, rule="C1", coefficient=.2, coverage="observed")],
                    "MOT executor C1 definition differs")
            outputs[gate["line_id"]] = result
        return dict(schema="headgate_MOT_frozen_events_v1", gates=outputs, sequence=self.sequence,
                    chain=["frozen_region_FSM", C1_KEY, "R1+R2"], source=deepcopy(source))


class StadiumEventExecutor:
    """Bridge already-loaded r15e17_run_events.FrozenEvents, cameras A-F.

    The caller constructs that engine with an authorized read gate. This wrapper
    never loads its config/parameter bundle/model/regions. Precomputed HeadGate
    points enter its exact finalize path, bypassing its pose/box point selector.
    """

    mode = "stadium"

    def __init__(self, frozen_engine):
        self.engine = frozen_engine
        require(frozen_engine.camera in "ABCDEF" and len(frozen_engine.camera) == 1, "Registered stadium camera A-F required")
        require(list(frozen_engine.size) == [3840, 2160], "Frozen stadium geometry requires native 3840x2160")
        require(callable(getattr(frozen_engine, "finalize", None)), "General E17 run event executor required")
        require({"_frozen_public", "_frozen_project", "transform_events"} <= set(frozen_engine.api),
                "General E17 context/evaluation frozen functions required")
        require(frozen_engine.protocol["variant"] == "R1+R2", "Frozen R1+R2 required")
        require(frozen_engine.ecfg["window_s"] == 2 and frozen_engine.ecfg["conditions"] == [
            dict(key=C1_KEY, coefficient=.2, rule="C1", coverage="observed")], "Frozen observed C1 q=.2 required")

    def finalize(self, raw_rows, point_rows, source, metadata):
        require(metadata["fps"] == self.engine.fps and metadata["camera"] == self.engine.camera,
                "Stadium engine clock/camera differs from stream")
        points = deepcopy(point_rows)
        for row in points:
            for detection in row["detections"]:
                point = detection["versions"]["hybrid"]
                point["signed_distances"] = self.engine.classifier.signed_distances(self.engine.camera, point["point"])
        result = self.engine.finalize(raw_rows, points, source, metadata)
        _check_result(result, ("candidates", "confirmation_evidence", "raw_confirmed_events", "groups", "group_details", "final_events"))
        require(all(key in result for key in ("processing_final_events", "processing_groups", "processing_raw_confirmed_events")),
                "Independent processing-context output missing")
        result["headgate_anchor_limitation"] = STADIUM_PROXY_LIMITATION
        result["headgate_chain"] = ["frozen_region_FSM", C1_KEY, "R1+R2"]
        return result


class HeadGateInference:
    """One complete native stream -> frozen tracker -> explicit points -> events.

    Each frame packet is {'frame': zero_based_processing_ordinal, 'image':
    native_uint8_BGR, optional 'detections': list}. Missing detections invoke
    the optional LazyHeadDetector. Empty lists are observed empty frames and
    still update the tracker. Metadata has fps,width,height,unit_id,camera,
    source_interval_half_open and evaluation_source_interval_half_open; source
    frame ordinals here are zero-based. MOT bridge emits its usual one-based
    source_frame field separately. Neither clock is inferred from filenames.

    All proposals remain in raw_detections. Only confidence >= .25 enters the
    tracker; low-score ByteTrack association stays inactive as in frozen P1.
    raw_detector_index preserves proposal index; raw_detection_index indexes
    the admitted list, matching the E17 finalize contract. One reset per run.
    """

    def __init__(self, *, tracker, projection, event_executor, detector=None):
        require(callable(getattr(tracker, "update", None)) and callable(getattr(tracker, "reset", None)),
                "Explicit tracker update/reset interface required")
        require(event_executor.mode == projection.mode, "Projection and event executor domains differ")
        self.tracker, self.projection, self.executor, self.detector = tracker, projection, event_executor, detector
        metadata = tracker.metadata() if callable(getattr(tracker, "metadata", None)) else tracker.metadata
        require(metadata.get("parameters") == BYTE_PARAMETERS, "Injected tracker must attest exact frozen ByteTrack parameters")
        if projection.mode == "stadium":
            require(projection.pose_model == event_executor.engine.model, "Projection and C1 must use the same frozen stadium model")
        self.tracker_binding = deepcopy(metadata)

    def run(self, frames, *, metadata, source):
        meta = deepcopy(metadata)
        fps = meta.get("fps")
        require(finite(fps) and fps > 0, "Finite native fps required")
        require([meta.get("width"), meta.get("height")] == self.projection.size, "Native projection/stream dimensions differ")
        for name in ("source_interval_half_open", "evaluation_source_interval_half_open"):
            interval = meta.get(name)
            require(isinstance(interval, (list, tuple)) and len(interval) == 2
                    and all(type(v) is int for v in interval) and 0 <= interval[0] < interval[1], "Explicit native half-open interval required")
            meta[name] = list(interval)
        start, end = meta["source_interval_half_open"]
        ef, ee = meta["evaluation_source_interval_half_open"]
        require(start <= ef < ee <= end, "Evaluation must lie within processing context")
        require(isinstance(meta.get("unit_id"), str) and bool(meta["unit_id"]), "Nonempty explicit unit_id required")
        require(self.tracker_binding.get("native_fps") == fps, "Tracker and stream native fps differ")
        self.tracker.reset()
        raw_rows, point_rows = [], []
        for i, packet in enumerate(frames):
            require(i < end-start and packet.get("frame") == i, "Every native frame must occur once, in order")
            require(packet.get("source_frame", start+i) == start+i, "Packet source-frame mapping differs")
            image = packet.get("image")
            require(getattr(image, "shape", None) == (meta["height"], meta["width"], 3)
                    and str(getattr(image, "dtype", None)) == "uint8", "Native uint8 BGR image required")
            if "detections" in packet:
                proposals = packet["detections"]
            else:
                require(self.detector is not None, "Frame has no detections and no explicit lazy detector")
                proposals = self.detector.predict(image)
            require(isinstance(proposals, (list, tuple)), "Detector must return an ordered list of native dictionaries")
            raw, inputs = [], []
            for j, original in enumerate(proposals):
                require(original.get("track_id") is None, "Detector must not supply tracking or GT identity")
                require(original.get("raw_detection_index", j) == j, "Raw proposal index must preserve list order")
                box = _box(original["box"])
                confidence, cls = original.get("confidence"), original.get("class_id")
                require(finite(confidence) and 0 <= confidence <= 1, "Finite confidence in [0,1] required")
                require(type(cls) is int, "Explicit integer detector class_id required")
                proposal = dict(raw_detection_index=j, box=box, confidence=float(confidence), class_id=cls, track_id=None)
                raw.append(proposal)
                if confidence >= .25:
                    inputs.append(dict(deepcopy(proposal), raw_detector_index=j, raw_detection_index=len(inputs)))
            tracked, tracker_rows = self.tracker.update(deepcopy(inputs), image)
            require(len(tracked) == len(inputs), "Tracker dropped admitted raw detections")
            ids = set()
            for original, detection in zip(inputs, tracked):
                require(all(detection.get(key) == value for key, value in original.items() if key != "track_id"),
                        "Tracker substituted detector geometry, score, class or indices")
                tid = detection.get("track_id")
                require(tid is None or type(tid) is int and tid > 0 and tid not in ids, "Track IDs must be positive and one-to-one per frame")
                if tid is not None:
                    ids.add(tid)
            returned_indices = set()
            for row in tracker_rows:
                require(len(row) == 8 and all(finite(x) for x in row), "Eight-column finite idxfix tracker output required")
                j, tid = row[-1], row[4]
                require(int(j) == j and 0 <= j < len(tracked) and j not in returned_indices, "Tracker index is not one-to-one in admitted detections")
                require(tracked[int(j)]["track_id"] == tid, "Tracker row ID/index differs from returned detection")
                returned_indices.add(j)
            require(returned_indices == {j for j,d in enumerate(tracked) if d["track_id"] is not None}, "Tracked detections and index rows disagree")
            clock = dict(frame=i, time_s=i/fps, source_frame=start+i, source_time_s=(start+i)/fps)
            raw_rows.append(dict(**clock, detections=tracked, raw_detections=raw, tracker_output=deepcopy(tracker_rows)))
            projected = [dict(deepcopy(d), versions={"hybrid": self.projection.point(d)}) for d in tracked]
            point_rows.append(dict(**clock, detections=projected))
        require(len(raw_rows) == end-start, "Missing native frame rows; empty detections must be explicit")
        result = self.executor.finalize(raw_rows, point_rows, source, meta)
        return dict(schema="r15e27_headgate_inference_prepared_v1", metadata=meta,
                    projection=self.projection.metadata(), raw_rows=raw_rows, point_rows=point_rows, event_result=result,
                    tracker=self.tracker.metadata() if callable(self.tracker.metadata) else deepcopy(self.tracker.metadata),
                    detector=self.detector.metadata() if self.detector is not None else {"input": "caller-supplied detections"},
                    tracker_index_semantics="returned rows index admitted detections; raw_detector_index maps to complete proposals",
                    validation_status="synthetic preparation; future real detector/tracker/data integration still required",
                    no_fitting_or_scoring=True)
