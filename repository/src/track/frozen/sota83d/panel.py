"""Author MOT17 adapters; no top-level I/O, detector, M4 or interpolation."""
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import math
import os

METHODS = ('byte', 'oc', 'bot')
ADMISSION = {'byte': .01, 'oc': .1, 'bot': .09}
PARAMETERS = {
    'byte': dict(track_thresh=.6, track_buffer=30, match_thresh=.9, mot20=False),
    'oc': dict(det_thresh=.6, max_age=30, min_hits=3, iou_threshold=.3,
               delta_t=3, asso_func='iou', inertia=.2, use_byte=False),
    'bot': dict(track_high_thresh=.6, track_low_thresh=.1, new_track_thresh=.7,
                track_buffer=30, match_thresh=.8, proximity_thresh=.5,
                appearance_thresh=.25, cmc_method='file', with_reid=False,
                mot20=False, ablation=False),
}

def admission(raw, method, np):
    """Mask computed in FP16, tracker input product remains original FP32."""
    indices = []
    rows = []
    for i, d in enumerate(raw):
        assert d['raw_detection_index'] == i
        obj, cls = np.float16(d['objectness']), np.float16(d['class_confidence'])
        assert float(np.float32(obj)) == d['objectness']
        assert float(np.float32(cls)) == d['class_confidence']
        product = np.float16(obj * cls)
        if product >= np.float16(ADMISSION[method]):
            indices.append(i)
            rows.append([*d['box'], d['objectness'], d['class_confidence'], 0.])
    return np.asarray(rows, dtype=np.float32).reshape((-1, 7)), indices

@contextmanager
def in_directory(path):
    old = Path.cwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old)

class CheckedGMC:
    """Read-only observation of original file consumption; never seek/skip/fill."""
    def __init__(self, stream):
        self.stream = stream
        self.expected_source_frame = None
        self.last = None
        self.calls = 0

    def readline(self):
        line = self.stream.readline()
        tokens = line.rstrip('\r\n').split('\t')
        assert len(tokens) >= 7 and int(tokens[0]) == self.expected_source_frame - 1, 'GMC frame mismatch'
        values = [float(x) for x in tokens[1:7]]
        assert all(math.isfinite(v) for v in values)
        self.last = dict(file_frame_zero_based=int(tokens[0]), source_frame=self.expected_source_frame, transform=values)
        self.calls += 1
        return line

    def close(self):
        self.stream.close()

class PanelTracker:
    def __init__(self, method, sequence, native_hw, *, bot_root=None, package='sota83d.vendor'):
        import importlib
        import numpy as np
        import torch
        self.np, self.torch = np, torch
        self.method, self.sequence, self.native_hw = method, sequence, tuple(native_hw)
        self.args = dict(PARAMETERS[method])
        self.calls = 0
        self.gmc = None
        if method == 'byte':
            mod = importlib.import_module(package + '.byte.byte_tracker')
            mod.BaseTrack._count = 0
            self.tracker = mod.BYTETracker(SimpleNamespace(**self.args), frame_rate=30)
        elif method == 'oc':
            mod = importlib.import_module(package + '.oc.ocsort')
            self.tracker = mod.OCSort(**self.args)
        else:
            assert method == 'bot' and bot_root is not None
            mod = importlib.import_module(package + '.bot.bot_sort')
            self.args['name'] = sequence
            with in_directory(bot_root):
                self.tracker = mod.BoTSORT(SimpleNamespace(**self.args), frame_rate=30)
            self.gmc = CheckedGMC(self.tracker.gmc.gmcFile)
            self.tracker.gmc.gmcFile = self.gmc

    @property
    def internal_frame(self):
        return int(self.tracker.frame_count if self.method == 'oc' else self.tracker.frame_id)

    def update(self, raw, source_frame):
        arr, indices = admission(raw, self.method, self.np)
        before = self.internal_frame
        author_rows, emitted = [], []
        if len(arr):
            if self.method == 'bot':
                self.gmc.expected_source_frame = source_frame
                tracks = self.tracker.update(arr.copy(), None)
            else:
                tracks = self.tracker.update(self.torch.from_numpy(arr.copy()), self.native_hw, self.native_hw)
            self.calls += 1
            for idx, track in enumerate(tracks):
                if self.method == 'oc':
                    assert len(track) == 5
                    box = list(map(float, track[:4]))
                    tid = float(track[4])
                    score = None  # The author return API carries no score.
                    tlwh = [box[0], box[1], box[2]-box[0], box[3]-box[1]]
                else:
                    box = list(map(float, track.tlbr))
                    tid = float(track.track_id)
                    score = float(track.score)
                    tlwh = list(map(float, track.tlwh))
                assert math.isfinite(tid) and tid.is_integer() and tid > 0
                assert all(math.isfinite(x) for x in box + tlwh)
                assert box[2] > box[0] and box[3] > box[1], 'Non-positive emitted author box'
                area = tlwh[2]*tlwh[3]
                ratio = tlwh[2]/tlwh[3]
                keep = area > (10 if self.method == 'bot' else 100) and ratio <= 1.6
                row = dict(author_output_index=idx, track_id=int(tid), box=box, tlwh=tlwh,
                           score=score, area=area, aspect_ratio=ratio, output_keep=keep)
                author_rows.append(row)
                if keep:
                    emitted.append(dict(emitted_output_index=len(emitted), author_output_index=idx,
                                        track_id=int(tid), box=box, score=score,
                                        raw_detection_index=None,
                                        box_semantics='author_emitted_tracker_xyxy'))
        assert self.internal_frame == before + int(bool(len(arr)))
        assert self.internal_frame == self.calls
        assert len({x['track_id'] for x in emitted}) == len(emitted), 'Duplicate emitted track ID'
        return dict(update_called=bool(len(arr)), admission_raw_indices=indices,
                    tracker_internal_frame=self.internal_frame, author_output_rows=author_rows,
                    outputs=emitted, gmc=self.gmc.last if len(arr) and self.gmc else None)

    def close(self):
        if self.gmc:
            self.gmc.close()
