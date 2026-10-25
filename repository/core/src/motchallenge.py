"""Strict reader for MOTChallenge tracker result files (v0.1 interface).

Row format: frame,id,x,y,w,h,conf,a,b,c with a 1-based frame and 1-based
pixel left/top. Boxes are converted to the frozen native zero-based continuous
xyxy convention (x0=x-1, y0=y-1, x1=x0+w, y1=y0+h). Nothing is repaired,
clipped, interpolated or dropped: any invalid row fails the whole file.
Import performs no I/O.
"""
from __future__ import annotations

import math


def _integer(value, field, line_no):
    if not value.is_integer():
        raise ValueError(f'Non-integer {field} at line {line_no}')
    return int(value)


def parse_results(text, seq_length):
    """Return (frames, stats).

    frames maps the 1-based source frame to its rows in file order. Each row is
    dict(track_id, box=[x0, y0, x1, y1], conf, line). The position of a row
    inside its frame list is the identity tie key (the role of the panel's
    emitted_output_index).
    """
    if type(seq_length) is not int or seq_length <= 0:
        raise ValueError('Invalid sequence length')
    frames = {}
    seen = set()
    rows = 0
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        cells = line.split(',')
        if len(cells) != 10:
            raise ValueError(f'Expected 10 comma-separated MOTChallenge fields at line {line_no}, found {len(cells)}')
        try:
            values = [float(c) for c in cells]
        except ValueError:
            raise ValueError(f'Non-numeric field at line {line_no}') from None
        if not all(math.isfinite(v) for v in values):
            raise ValueError(f'Non-finite field at line {line_no}')
        frame = _integer(values[0], 'frame', line_no)
        track_id = _integer(values[1], 'id', line_no)
        x, y, w, h, conf = values[2:7]
        if not 1 <= frame <= seq_length:
            raise ValueError(f'Frame {frame} outside [1, {seq_length}] at line {line_no}')
        if track_id < 0:
            raise ValueError(f'Negative track id at line {line_no}')
        if not (w > 0 and h > 0):
            raise ValueError(f'Non-positive width/height at line {line_no}')
        if (frame, track_id) in seen:
            raise ValueError(f'Duplicate (frame, id) = ({frame}, {track_id}) at line {line_no}')
        seen.add((frame, track_id))
        x0 = x - 1
        y0 = y - 1
        box = [x0, y0, x0 + w, y0 + h]
        if not (box[2] > box[0] and box[3] > box[1]) or not all(math.isfinite(v) for v in box):
            raise ValueError(f'Degenerate converted box at line {line_no}')
        frames.setdefault(frame, []).append(dict(track_id=track_id, box=box, conf=conf, line=line_no))
        rows += 1
    stats = dict(rows=rows, frames_with_rows=len(frames), seq_length=seq_length,
                 unique_track_ids=len({tid for _, tid in seen}))
    return frames, stats
