"""#50 tracking-only adapters; no detector, media reader, downloads or writes.

Callers configure cache/network isolation before construction. Every explicit
source/configuration read goes through the supplied gate. Returned detections
retain their original boxes/keypoints; tracker rows are diagnostic output only.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import math
from pathlib import Path


BYTE_YAML_SHA = 'eaefad899964d7a12a13090d5da32bcdae8f0109968ffca982fdba2c60ad3c38'
BYTE_CODE_SHA = 'fa2d318cca1bd35f5ad062512da298fd18b11e71ed03485b7f1f43f97c224aff'
IDXFIX_SHA = '477c3041fed126903e8e18de967e14da4a98775fef5ac4a4cf48a5eb611ac0d3'
BYTE_DEFAULTS = dict(tracker_type='bytetrack', track_high_thresh=.25,
    track_low_thresh=.1, new_track_thresh=.25, track_buffer=30,
    match_thresh=.8, fuse_score=True)
BOT_DEFAULTS = dict(BYTE_DEFAULTS, tracker_type='botsort',
    gmc_method='sparseOptFlow', proximity_thresh=.5, appearance_thresh=.8,
    with_reid=False, model='auto')
TRACKER_COLUMNS = ['x1', 'y1', 'x2', 'y2', 'track_id', 'score', 'class',
                   'input_detection_index']


def _read_binding(gate, path, purpose, expected_sha=None):
    path = Path(path).resolve()
    data = gate.read(path, expected_sha=expected_sha, purpose=purpose)
    if not isinstance(data, bytes):
        raise TypeError('gate.read must return bytes')
    digest = hashlib.sha256(data).hexdigest()
    if expected_sha is not None and digest != expected_sha:
        raise ValueError('Frozen source/configuration SHA differs: '+str(path))
    return data, dict(path=str(path), bytes=len(data), sha256=digest)


class SmokeTracker:
    """One independent native-frame tracker per instance/clip.

    ``update`` returns ``(original_detection_dicts_with_track_id, tracker_rows)``.
    The last tracker column indexes the *passed list*, not a pre-filter proposal
    list. Existing raw_detection_index fields are retained without reinterpretation.
    No event extraction or point selection occurs here.
    """

    def __init__(self, kind, fps, gate):
        if kind not in ('P2', 'P1-BoT'):
            raise ValueError('kind must be P2 or P1-BoT')
        self.kind = kind
        self.fps = float(fps)
        if not math.isfinite(self.fps) or self.fps <= 0 or round(self.fps) < 1:
            raise ValueError('Finite positive native fps is required')
        self.frame_rate = round(self.fps)
        self.gate = gate
        self.bindings = {}
        _, self.bindings['adapter'] = _read_binding(gate, Path(__file__),
            'Bind #50 tracking-only adapter source')

        # Import LAP directly first: fail here instead of letting Ultralytics'
        # matching.py enter its check_requirements/automatic-install fallback.
        lap_spec = importlib.util.find_spec('lap')
        if lap_spec is None or lap_spec.origin is None:
            raise RuntimeError('Existing LAP dependency missing; installation is forbidden')
        _, self.bindings['lap_python_entry'] = _read_binding(gate, lap_spec.origin,
            'Check existing LAP dependency source before importing tracker')
        import lap
        if not getattr(lap, '__version__', None) or not callable(getattr(lap, 'lapjv', None)):
            raise RuntimeError('Existing LAP dependency is unusable; do not install a replacement')

        spec = importlib.util.find_spec('ultralytics')
        if spec is None or spec.origin is None:
            raise RuntimeError('Existing Ultralytics package missing')
        package = Path(spec.origin).resolve().parent
        for key, relative, digest in (
            ('ultralytics_entry', '__init__.py', None),
            ('byte_tracker', 'trackers/byte_tracker.py', BYTE_CODE_SHA),
            ('matching', 'trackers/utils/matching.py', None),
            ('results_boxes', 'engine/results.py', None),
        ):
            _, self.bindings[key] = _read_binding(gate, package/relative,
                'Bind installed tracker/Boxes implementation without modification', digest)
        if kind == 'P1-BoT':
            for key, relative in (('bot_sort', 'trackers/bot_sort.py'),
                                  ('gmc', 'trackers/utils/gmc.py')):
                _, self.bindings[key] = _read_binding(gate, package/relative,
                    'Bind installed default BoT-SORT/GMC implementation')
        yaml_path = package/'cfg/trackers'/('bytetrack.yaml' if kind == 'P2' else 'botsort.yaml')
        data, self.bindings['yaml'] = _read_binding(gate, yaml_path,
            'Read frozen/default tracker YAML; no parameter changes',
            BYTE_YAML_SHA if kind == 'P2' else None)

        import numpy as np
        import yaml
        import ultralytics
        from types import SimpleNamespace
        from ultralytics.engine.results import Boxes
        if ultralytics.__version__ != '8.3.192':
            raise RuntimeError('Expected installed Ultralytics 8.3.192')
        self.args = yaml.safe_load(data)
        expected = BYTE_DEFAULTS if kind == 'P2' else BOT_DEFAULTS
        if self.args != expected:
            raise RuntimeError('Installed tracker YAML differs from frozen/default parameters')
        self.np, self.Boxes = np, Boxes
        self.versions = dict(ultralytics=ultralytics.__version__, lap=lap.__version__,
                             numpy=np.__version__)
        if kind == 'P2':
            helper = Path(__file__).resolve().parent/'r15_tracker_idxfix.py'
            _, self.bindings['idxfix'] = _read_binding(gate, helper,
                'Bind explicitly adopted global-index adapter', IDXFIX_SHA)
            from r15_tracker_idxfix import make_index_preserving_tracker_class
            from ultralytics.trackers.byte_tracker import BYTETracker
            cls = make_index_preserving_tracker_class(BYTETracker)
        else:
            from ultralytics.trackers.bot_sort import BOTSORT
            cls = BOTSORT
        self.tracker = cls(SimpleNamespace(**self.args), frame_rate=self.frame_rate)
        self.reset()
        if kind == 'P1-BoT':
            if self.tracker.encoder is not None or self.tracker.args.with_reid:
                raise RuntimeError('ReID must remain disabled')
            self._original_gmc_apply = self.tracker.gmc.apply
            self.tracker.gmc.apply = self._observe_gmc_apply

    def reset(self):
        """Fresh IDs, Kalman/tracker state and GMC state; counters start at zero."""
        self.tracker.reset()
        self.counts = Counter(frames=0, empty_frames=0, input_detections=0,
            returned_tracks=0, frames_with_all_high_pool=0,
            gmc_calls=0, gmc_successful_returns=0, gmc_exception_identity_fallbacks=0,
            gmc_identity_returns=0, gmc_nonfinite_or_invalid_returns=0,
            gmc_observer_errors=0, validated_index_frames=0)
        self.gmc_exception_types = Counter()
        self.image_shapes = Counter()

    def _observe_gmc_apply(self, *args, **kwargs):
        """Observe only; rethrow so BYTETracker's original fallback stays intact."""
        self.counts['gmc_calls'] += 1
        try:
            warp = self._original_gmc_apply(*args, **kwargs)
        except Exception as error:
            self.counts['gmc_exception_identity_fallbacks'] += 1
            self.gmc_exception_types[type(error).__name__] += 1
            raise
        self.counts['gmc_successful_returns'] += 1
        try:
            matrix = self.np.asarray(warp)
            valid = matrix.shape == (2, 3) and self.np.isfinite(matrix).all()
            if not valid:
                self.counts['gmc_nonfinite_or_invalid_returns'] += 1
            elif self.np.array_equal(matrix, self.np.eye(2, 3)):
                self.counts['gmc_identity_returns'] += 1
        except Exception:
            # Instrumentation itself must not change the original warp result.
            self.counts['gmc_observer_errors'] += 1
        return warp

    def update(self, raw_detections, bgr):
        np = self.np
        if not isinstance(raw_detections, (list, tuple)):
            raise TypeError('raw_detections must preserve the input list order')
        if not isinstance(bgr, np.ndarray) or bgr.ndim != 3 or bgr.shape[2] != 3 or bgr.dtype != np.uint8:
            raise ValueError('Supply the matching native uint8 BGR frame, including empty-detection frames')
        if bgr.shape[0] < 1 or bgr.shape[1] < 1:
            raise ValueError('Empty source image')
        rows = []
        for detection in raw_detections:
            box = detection['box']; score = float(detection['confidence']); cls = float(detection['class_id'])
            if len(box) != 4 or not all(math.isfinite(float(x)) for x in box):
                raise ValueError('Detector box must contain four finite native coordinates')
            if not math.isfinite(score) or not .25 <= score <= 1:
                raise ValueError('Tracker input must already satisfy frozen conf >= .25')
            if not math.isfinite(cls) or not cls.is_integer():
                raise ValueError('Detector class_id must be an integer')
            rows.append([*box, score, cls])
        # Saved float32 detections round-trip through JSON without changing their
        # tracker arithmetic. Original dictionaries remain at their saved values.
        array = np.asarray(rows, dtype=np.float32).reshape((-1, 6))
        boxes = self.Boxes(array, orig_shape=bgr.shape[:2])
        tracks = self.tracker.update(boxes, bgr)
        matrix = np.asarray(tracks)
        if matrix.size == 0:
            matrix = np.empty((0, 8), dtype=np.float32)
        if matrix.ndim != 2 or matrix.shape[1] != 8 or not np.isfinite(matrix).all():
            raise RuntimeError('Unexpected native tracker output schema')
        by_index = {}; track_ids = set()
        for row in matrix:
            raw_index, track_id = float(row[-1]), float(row[4])
            if not raw_index.is_integer() or not 0 <= raw_index < len(raw_detections):
                raise RuntimeError('Returned tracker index is not an input detection')
            if not track_id.is_integer() or track_id <= 0:
                raise RuntimeError('Returned track ID is invalid')
            j, tid = int(raw_index), int(track_id)
            if j in by_index or tid in track_ids:
                raise RuntimeError('Returned tracker indices/IDs are not one-to-one')
            # All inputs are in the high pool. Check identity of the original
            # score/class too; do not substitute a smoothed tracker rectangle.
            if row[5] != array[j, 4] or row[6] != array[j, 5]:
                raise RuntimeError('Returned score/class does not agree with indexed input')
            by_index[j] = tid; track_ids.add(tid)
        output = []
        for j, detection in enumerate(raw_detections):
            item = deepcopy(detection); item['track_id'] = by_index.get(j); output.append(item)
        self.counts.update(frames=1, empty_frames=int(not raw_detections),
            input_detections=len(raw_detections), returned_tracks=len(matrix),
            frames_with_all_high_pool=1, validated_index_frames=1)
        self.image_shapes[str(tuple(bgr.shape[:2]))] += 1
        return output, matrix.tolist()

    def metadata(self):
        return dict(kind=self.kind, native_fps=self.fps, tracker_constructor_frame_rate=self.frame_rate,
            reset_each_clip=True, tracker_class=type(self.tracker).__name__, parameters=deepcopy(self.args),
            versions=deepcopy(self.versions), source_bindings=deepcopy(self.bindings),
            counts=dict(self.counts), gmc_exception_types=dict(self.gmc_exception_types),
            image_shapes=dict(self.image_shapes), tracker_output_columns=list(TRACKER_COLUMNS),
            output_points='Original raw detector boxes/keypoints retained; only track_id assigned',
            index_contract='Last tracker column indexes the full passed detection list; conf >= .25 makes default BoT high-pool indices global',
            gmc_note='Exception counts observe the original BYTETracker identity fallback; identity returns also include initialization/insufficient features and are not all errors',
            no_detector_or_reid_model_loaded=True)
