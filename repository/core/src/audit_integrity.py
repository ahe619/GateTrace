"""Fail-closed structural validation of saved per-frame identity evidence.

This module is an integrity adapter, not a scorer. It neither assigns identities
nor recomputes IoU. It consumes the exact JSON schema written by tracker_score.py
and the sparse frame-to-rows mapping returned by motchallenge.parse_results.
Import and validation perform no I/O; caller owns input hashes and output seals.
"""
from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping
from fractions import Fraction


class FrameIdentityIntegrityError(ValueError):
    """The saved evidence does not faithfully cover the parsed tracker rows."""


def _fail(path, message):
    raise FrameIdentityIntegrityError(f'{path}: {message}')


def _integer(value, path, minimum=None):
    if type(value) is not int or (minimum is not None and value < minimum):
        _fail(path, 'expected integer' + (f' >= {minimum}' if minimum is not None else ''))
    return value


def _number(value, path):
    if type(value) not in (int, float):
        _fail(path, 'expected finite number (not bool/string)')
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        _fail(path, 'non-finite number')
    return value


def _required(obj, keys, path):
    if not isinstance(obj, Mapping):
        _fail(path, 'expected object')
    missing = set(keys) - set(obj)
    if missing:
        _fail(path, 'missing fields: ' + ', '.join(sorted(missing)))


def _finite_json(value, path):
    """Reject non-JSON containers and NaN/Inf even in auxiliary audit fields."""
    if value is None or type(value) in (bool, str, int):
        return
    if type(value) is float:
        _number(value, path)
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                _fail(path, 'object keys must be strings')
            _finite_json(item, f'{path}.{key}')
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _finite_json(item, f'{path}[{i}]')
    else:
        _fail(path, 'expected JSON-compatible value')


def _box(value, path):
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        _fail(path, 'expected four xyxy coordinates')
    for i, coordinate in enumerate(value):
        _number(coordinate, f'{path}[{i}]')
    if value[2] <= value[0] or value[3] <= value[1]:
        _fail(path, 'box must have positive width and height')
    return value


def _identity_fields(obs, path):
    status = obs['status']
    if type(status) is not str or status not in ('valid', 'ambiguous', 'unmatched'):
        _fail(path + '.status', 'unknown per-frame identity status')
    if status == 'unmatched':
        for field in ('gt_id', 'gt_class', 'gt_line', 'assigned_iou', 'margin'):
            if obs[field] is not None:
                _fail(path + '.' + field, 'unmatched observation must contain null')
        return
    # e1.assign sets gt_id only for strong/valid assignments. Ambiguous rows
    # still retain the assigned GT class/line and scores, but gt_id is null.
    _integer(obs['gt_class'], path + '.gt_class')
    if obs['gt_class'] not in (1, 6, 7):
        _fail(path + '.gt_class', 'class absent from frozen identity GT pool')
    _integer(obs['gt_line'], path + '.gt_line', 1)
    iou = _number(obs['assigned_iou'], path + '.assigned_iou')
    margin = _number(obs['margin'], path + '.margin')
    if iou < 0.5:
        _fail(path + '.assigned_iou', 'below assigned-IoU threshold of frozen writer')
    # The writer neither clips IoU nor asserts <= 1. Do not add theoretical
    # range bounds that could reject its finite floating-point roundoff.
    if status == 'valid':
        _integer(obs['gt_id'], path + '.gt_id')
        if margin < 0.10:
            _fail(path + '.margin', 'valid status contradicts saved margin')
    else:
        if obs['gt_id'] is not None:
            _fail(path + '.gt_id', 'ambiguous observation must have null gt_id')
        if margin >= 0.10:
            _fail(path + '.margin', 'ambiguous status contradicts saved margin')


def _assignment(audit, observations, path):
    """Check the writer's assignment envelope without solving its matching."""
    _required(audit, ('pairs', 'cardinality', 'exact_cost', 'iou_edges',
                      'containment_edges', 'residual_containment'), path)
    for field in ('pairs', 'iou_edges', 'containment_edges', 'residual_containment'):
        if not isinstance(audit[field], list):
            _fail(path + '.' + field, 'expected list')
    cardinality = _integer(audit['cardinality'], path + '.cardinality', 0)
    if cardinality != len(audit['pairs']):
        _fail(path, 'cardinality does not equal pair count')
    if type(audit['exact_cost']) is not str:
        _fail(path + '.exact_cost', 'expected serialized Fraction string')
    try:
        Fraction(audit['exact_cost'])
    except (ValueError, ZeroDivisionError, OverflowError):
        _fail(path + '.exact_cost', 'invalid serialized Fraction')
    indices, gids = set(), set()
    for i, pair in enumerate(audit['pairs']):
        if not isinstance(pair, list) or len(pair) != 2:
            _fail(f'{path}.pairs[{i}]', 'expected [output_row_index, gt_id]')
        index = _integer(pair[0], f'{path}.pairs[{i}][0]', 0)
        gid = _integer(pair[1], f'{path}.pairs[{i}][1]')
        if index >= len(observations) or index in indices or gid in gids:
            _fail(f'{path}.pairs[{i}]', 'out-of-range or duplicate assignment endpoint')
        indices.add(index)
        gids.add(gid)
        obs = observations[index]
        if obs['status'] == 'unmatched' or (obs['status'] == 'valid' and obs['gt_id'] != gid):
            _fail(f'{path}.pairs[{i}]', 'pair contradicts observation identity')
    expected = {i for i, obs in enumerate(observations) if obs['status'] != 'unmatched'}
    if indices != expected:
        _fail(path + '.pairs', 'assigned observations and pair indices differ')


def validate_frame_identity(records, frames, seq_length):
    """Validate all frames and their one-to-one tracker-row correspondence.

    ``records`` is a single-pass iterable of parsed JSON objects, in frame order.
    ``frames`` is the sparse mapping returned by ``parse_results``: a missing
    frame means it genuinely contains no tracker output. In contrast, a missing
    identity frame/observation is an error, never evidence of an empty frame.
    Success returns counts only. Failure raises FrameIdentityIntegrityError;
    no input values, order, geometry, identities, or thresholds are changed.
    The checks establish structure and consistency, not correctness of the
    GT assignment: the caller must also verify the authoritative file hashes.
    """
    _integer(seq_length, 'seq_length', 1)
    if not isinstance(frames, Mapping):
        _fail('frames', 'expected sparse frame-to-rows mapping')
    total_rows = 0
    track_ids = set()
    for sf, rows in frames.items():
        _integer(sf, 'frames key', 1)
        if sf > seq_length:
            _fail(f'frames[{sf}]', 'frame outside sequence')
        if not isinstance(rows, list):
            _fail(f'frames[{sf}]', 'expected list of tracker rows')
        seen = set()
        for i, row in enumerate(rows):
            path = f'frames[{sf}][{i}]'
            _required(row, ('track_id', 'box'), path)
            tid = _integer(row['track_id'], path + '.track_id', 0)
            if tid in seen:
                _fail(path, 'duplicate tracker ID in one frame')
            seen.add(tid)
            track_ids.add(tid)
            _box(row['box'], path + '.box')
            if 'source_frame' in row:
                _integer(row['source_frame'], path + '.source_frame', 1)
                if row['source_frame'] != sf:
                    _fail(path + '.source_frame', 'input row belongs to another frame')
            if 'conf' in row:
                _number(row['conf'], path + '.conf')
            if 'line' in row:
                _integer(row['line'], path + '.line', 1)
        total_rows += len(rows)
    try:
        iterator = iter(records)
    except TypeError:
        _fail('records', 'expected iterable of identity frame records')
    frame_count = observation_count = empty_frames = 0
    statuses = Counter({s: 0 for s in ('valid', 'ambiguous', 'unmatched')})
    fields = ('source_frame', 'track_id', 'output_row_index', 'gt_id', 'gt_class',
              'gt_line', 'status', 'box', 'assigned_iou', 'margin')
    for expected_frame, record in enumerate(iterator, 1):
        path = f'records[{expected_frame - 1}]'
        if expected_frame > seq_length:
            _fail(path, 'extra identity frame after sequence end')
        _required(record, ('source_frame', 'observations', 'output_assignment'), path)
        _finite_json(record, path)
        sf = _integer(record['source_frame'], path + '.source_frame', 1)
        if sf != expected_frame:
            _fail(path + '.source_frame', f'expected {expected_frame}; missing, duplicate, or unordered frame')
        observations = record['observations']
        if not isinstance(observations, list):
            _fail(path + '.observations', 'expected list')
        rows = frames.get(sf, [])
        if len(observations) != len(rows):
            _fail(path + '.observations', 'count differs from input tracker rows')
        for i, (obs, row) in enumerate(zip(observations, rows)):
            opath = f'{path}.observations[{i}]'
            _required(obs, fields, opath)
            _integer(obs['output_row_index'], opath + '.output_row_index', 0)
            if obs['output_row_index'] != i:
                _fail(opath + '.output_row_index', 'expected unique input row index in original order')
            _integer(obs['source_frame'], opath + '.source_frame', 1)
            if obs['source_frame'] != sf:
                _fail(opath + '.source_frame', 'observation belongs to another frame')
            _integer(obs['track_id'], opath + '.track_id', 0)
            if obs['track_id'] != row['track_id']:
                _fail(opath + '.track_id', 'differs from input tracker row')
            box = _box(obs['box'], opath + '.box')
            if any(a != b for a, b in zip(box, row['box'])):
                _fail(opath + '.box', 'differs from input tracker row (no tolerance/repair)')
            _identity_fields(obs, opath)
            statuses[obs['status']] += 1
        _assignment(record['output_assignment'], observations, path + '.output_assignment')
        frame_count += 1
        observation_count += len(observations)
        empty_frames += not observations
    if frame_count != seq_length:
        _fail('records', f'expected {seq_length} identity frames, received {frame_count}')
    if observation_count != total_rows:
        _fail('records', 'total observations differ from input tracker rows')
    return dict(schema='frame_identity_integrity_v1', status='VALIDATED',
                seq_length=seq_length, frame_count=frame_count,
                observation_count=observation_count, input_row_count=total_rows,
                empty_frames=empty_frames, frames_with_observations=frame_count - empty_frames,
                unique_track_ids=len(track_ids), status_counts=dict(statuses))
