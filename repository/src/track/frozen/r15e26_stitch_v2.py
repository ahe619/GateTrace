"""Frozen M4 one-pass trajectory stitching. Pure CPU module; no data or file I/O.

Schema and remapping behavior follow r15e26_stitch.py, reimplemented here so the
old pending module remains unchanged. Native points are not shifted or invented.
The caller must hash the policy bytes before passing its decoded object; this
module additionally verifies the exact canonical policy contents before rows are
consumed. Candidate decisions use only the original, unstiched tracks.
"""
from __future__ import annotations

from bisect import bisect_right
from collections import Counter, defaultdict
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import math
from typing import Mapping

IMPLEMENTATION_READY = True
METHOD_PROTOCOL_SHA256 = '5304a022591b18883d6852b8d11db36cf090fc3f3c0b00c325f5edf932523406'
AMENDMENT1_SHA256 = 'b88fad4fbd74737d58dee12ea5ee7bf64d10defc3ab46af33a62a904dc307017'
FROZEN_POLICY_SHA256 = 'fd35e954c763bb72df73ae161892a8a8de575d58fb5aa9180943c4a6b1284bb9'
POLICY_CANONICAL_SHA256 = '1efd1449b9b1090f0c455d3d7188ff01a8082f1401a5d701dc04ac4298de185f'
CLARIFICATION_DOCUMENT_SHA256 = '81fc6d5ba0bb870fd670f959628773267ec5027ef78ea70a11676335fb49dc0c'
EXPECTED_ALGORITHM = {
    'gap_distance': 'finite_rectangle_euclidean',
    'velocity_window_s': .5,
    'velocity_frames_rounding': 'floor',
    'velocity_estimator': 'endpoint_displacement_over_actual_dt',
    'require_exact_window_endpoints': True,
    'allow_short_window': False,
    'max_valid_observation_dt_s': .2,
    'invalid_points_are_missing': True,
    'max_link_delay_s': 1.0,
    'max_gap_distance_hmid': 1.0,
    'max_prediction_error_local_height': 1.0,
    'match_cost': 'native_pixel_euclidean',
    'mutual_unique': True,
    'tie_policy': 'reject_exact_ties',
    'update_policy': 'one_pass_original_tracks_then_chain_root',
    'endpoint_policy': 'raw_tracked_detection_endpoints',
    'namespace_keys': ['sequence', 'block'],
}


class ClarificationRequired(RuntimeError):
    """Production policy differs from the independently frozen declaration."""


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf8')


def require_production_ready(clarification):
    """Reject missing/changed policy before an input iterator is consumed."""
    if not isinstance(clarification, Mapping):
        raise ClarificationRequired('The exact frozen M4 policy is required')
    expected_header = dict(schema='r15e26_m4_policy_v1', frozen=True,
        sequence_whitelist=['01', '02'], parent_protocol_sha256=METHOD_PROTOCOL_SHA256,
        amendment_1_sha256=AMENDMENT1_SHA256, protocol_sha256=CLARIFICATION_DOCUMENT_SHA256,
        no_training=True, no_scoring=True, no_test_set_execution=True,
        new_real_variant_results_seen=False)
    try:
        if any(_canonical(clarification.get(k)) != _canonical(v) for k, v in expected_header.items()):
            raise ClarificationRequired('M4 policy header or scope differs')
        if _canonical(clarification.get('algorithm')) != _canonical(EXPECTED_ALGORITHM):
            raise ClarificationRequired('M4 algorithm fields differ from frozen policy')
        if hashlib.sha256(_canonical(dict(clarification))).hexdigest() != POLICY_CANONICAL_SHA256:
            raise ClarificationRequired('M4 policy content differs from frozen canonical contents')
    except (TypeError, ValueError) as exc:
        raise ClarificationRequired('M4 policy is not valid canonical JSON') from exc


def _integer(value, label):
    if type(value) is not int:
        raise ValueError(label + ' must be an integer')
    return value


def _fps(value):
    if isinstance(value, bool):
        raise ValueError('fps must be a positive rational')
    try:
        result = value if isinstance(value, Fraction) else Fraction(str(value))
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise ValueError('fps must be a positive rational') from exc
    if result <= 0:
        raise ValueError('fps must be positive')
    return result


def _namespace(value):
    if not isinstance(value, Mapping) or set(value) != {'sequence', 'block'}:
        raise ValueError('Explicit sequence and block namespace required')
    if any(not isinstance(value[k], str) or not value[k].strip() for k in value):
        raise ValueError('Nonempty namespace strings required')
    return dict(value)


def _point(value):
    """Invalid points are missing observations, never a new trimmed endpoint."""
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    try:
        point = tuple(float(v) for v in value)
    except (ValueError, TypeError, OverflowError):
        return None
    return point if all(math.isfinite(v) for v in point) else None


def gap_rectangle(gate):
    """census.make_lines fields: H/V, coordinate, finite extent, gap half width."""
    orientation = gate['orientation']
    c = float(gate['line_coordinate_px'])
    lo, hi = map(float, gate['line_extent_px'])
    gap = float(gate['gap_half_width'])
    hmid = float(gate['h_mid'])
    if (orientation not in ('H', 'V') or not all(math.isfinite(x) for x in (c, lo, hi, gap, hmid))
            or lo >= hi or gap < 0 or hmid <= 0):
        raise ValueError('Invalid finite gap geometry')
    return (lo, c-gap, hi, c+gap) if orientation == 'H' else (c-gap, lo, c+gap, hi)


def distance_to_gap(point, gate):
    point = _point(point)
    if point is None:
        raise ValueError('Gap distance requires a valid point')
    xmin, ymin, xmax, ymax = gap_rectangle(gate)
    x, y = point
    return math.hypot(max(xmin-x, 0., x-xmax), max(ymin-y, 0., y-ymax))


def height_at_point(g1, point):
    """G1 inverse at the successor's first foot point, unchanged from census."""
    point = _point(point)
    if point is None:
        raise ValueError('G1 requires a valid point')
    a, b, c = map(float, g1['coefficients'])
    width, height = map(float, g1['native_size'])
    if not all(math.isfinite(v) for v in (a, b, c, width, height)) or width <= 0 or height <= 0:
        raise ValueError('Invalid G1 parameters')
    denom = 1 + c / height
    if not math.isfinite(denom) or denom == 0:
        raise ValueError('Invalid G1 inverse denominator')
    value = (a + b * point[0] / width + c * point[1] / height) / denom
    if not math.isfinite(value) or value <= 0:
        raise ValueError('G1 height is nonpositive/nonfinite; no fallback')
    return value


def _checkpoint(callback, stage):
    if callback is not None:
        callback(stage)


def collect_tracks(frame_rows, *, namespace, checkpoint=None):
    """Copy all raw tracked detections; preserve invalid points in original rows."""
    ns = _namespace(namespace)
    rows, tracks = [], defaultdict(list)
    previous = -1
    for raw in frame_rows:
        _checkpoint(checkpoint, 'M4 collect native frame')
        row = deepcopy(dict(raw))
        frame = _integer(row['frame'], 'frame')
        if frame < 0 or frame <= previous:
            raise ValueError('Frame rows must be strictly increasing native ordinals')
        previous = frame
        if 'stitch_namespace' in row and row['stitch_namespace'] != ns:
            raise ValueError('Input frame crosses sequence/block namespace')
        raw_ids, track_ids = set(), set()
        for detection in row['detections']:
            rid = _integer(detection['raw_detection_index'], 'raw_detection_index')
            if rid < 0 or rid in raw_ids:
                raise ValueError('Duplicate/negative raw detection index')
            raw_ids.add(rid)
            if 'stitch_namespace' in detection and detection['stitch_namespace'] != ns:
                raise ValueError('Input detection crosses sequence/block namespace')
            if 'frame' in detection and detection['frame'] != frame:
                raise ValueError('Detection frame differs from row frame')
            if 'original_track_id' in detection:
                raise ValueError('Refuse to restitch already mapped detections')
            tid = detection['track_id']
            if tid is None:
                continue
            tid = _integer(tid, 'track_id')
            if tid in track_ids:
                raise ValueError('Duplicate track ID in a native frame')
            track_ids.add(tid)
            tracks[tid].append(dict(frame=frame, point=_point(detection.get('point')),
                                    row_index=len(rows), raw_detection_index=rid))
        rows.append(row)
    return rows, dict(tracks)


def endpoint_velocity(observations, fps):
    """One original track; full discrete window and both endpoints mandatory."""
    rate = _fps(fps)
    k = (rate / 2).numerator // (rate / 2).denominator
    if k <= 0:
        raise ValueError('fps gives an empty discrete velocity window')
    if not observations:
        return dict(valid=False, reason='no_observations', k=k)
    end = observations[-1]['frame']
    start = end-k
    if observations[-1]['point'] is None:
        return dict(valid=False, reason='invalid_raw_last_point', k=k)
    by_frame = {o['frame']: o for o in observations}
    if start not in by_frame:
        return dict(valid=False, reason='missing_exact_velocity_start', k=k)
    if by_frame[start]['point'] is None:
        return dict(valid=False, reason='invalid_exact_velocity_start', k=k)
    valid = [o for o in observations if start <= o['frame'] <= end and o['point'] is not None]
    gaps = [(a['frame'], b['frame']) for a, b in zip(valid, valid[1:])
            if Fraction(b['frame']-a['frame']) / rate > Fraction(1, 5)]
    if gaps:
        return dict(valid=False, reason='velocity_valid_observation_gap_gt_0p2s', k=k, gaps=gaps)
    dt = Fraction(k) / rate
    p0, p1 = by_frame[start]['point'], observations[-1]['point']
    velocity = ((p1[0]-p0[0])/float(dt), (p1[1]-p0[1])/float(dt))
    if not all(math.isfinite(v) for v in velocity):
        return dict(valid=False, reason='nonfinite_velocity', k=k)
    return dict(valid=True, k=k, start_frame=start, end_frame=end,
                actual_dt_s=float(dt), actual_dt_fraction=str(dt), velocity_px_s=list(velocity))


def select_mutual_unique(candidates, *, checkpoint=None):
    """Exact float equality rejects cost ties; no epsilon or greedy iteration."""
    by_before, by_after = defaultdict(list), defaultdict(list)
    seen = set()
    for row in candidates:
        _checkpoint(checkpoint, 'M4 group candidate pair')
        key = row['before_track_id'], row['after_track_id']
        if key in seen or key[0] == key[1]:
            raise ValueError('Duplicate/self candidate pair')
        seen.add(key)
        if not math.isfinite(row['error_px']) or row['error_px'] < 0:
            raise ValueError('Candidate error must be nonnegative and finite')
        by_before[key[0]].append(row)
        by_after[key[1]].append(row)
    def unique(rows):
        lowest = min(r['error_px'] for r in rows)
        winners = [r for r in rows if r['error_px'] == lowest]
        return winners[0] if len(winners) == 1 else None
    outgoing = {k: unique(v) for k, v in by_before.items()}
    incoming = {k: unique(v) for k, v in by_after.items()}
    links, rejected = [], []
    for row in sorted(candidates, key=lambda r: (r['before_track_id'], r['after_track_id'])):
        _checkpoint(checkpoint, 'M4 mutually unique minima')
        a, b = row['before_track_id'], row['after_track_id']
        if outgoing[a] is row and incoming[b] is row:
            links.append(deepcopy(row))
        else:
            reasons = []
            if outgoing[a] is None: reasons.append('outgoing_exact_cost_tie')
            elif outgoing[a] is not row: reasons.append('not_unique_outgoing_minimum')
            if incoming[b] is None: reasons.append('incoming_exact_cost_tie')
            elif incoming[b] is not row: reasons.append('not_unique_incoming_minimum')
            rejected.append(dict(before_track_id=a, after_track_id=b, reasons=reasons))
    return links, rejected


def resolve_chain_roots(track_ids, links, *, checkpoint=None):
    keys = set(track_ids)
    parents, children = {}, {}
    for link in links:
        _checkpoint(checkpoint, 'M4 link topology')
        a, b = link['before_track_id'], link['after_track_id']
        if a not in keys or b not in keys or a == b or b in parents or a in children:
            raise ValueError('Accepted links must be a one-to-one known-track chain forest')
        if 'before_namespace' in link or 'after_namespace' in link:
            if link.get('before_namespace') != link.get('after_namespace'):
                raise ValueError('Accepted link crosses namespaces')
        parents[b], children[a] = a, b
    roots = {}
    for key in sorted(keys):
        _checkpoint(checkpoint, 'M4 chain root mapping')
        root, visited = key, set()
        while root in parents:
            if root in visited:
                raise ValueError('Cycle in accepted links')
            visited.add(root)
            root = parents[root]
        roots[key] = root
    return roots


def _remap(rows, roots, ns, checkpoint):
    for row in rows:
        _checkpoint(checkpoint, 'M4 remap native frame')
        row['stitch_namespace'] = dict(ns)
        used = set()
        for detection in row['detections']:
            old = detection['track_id']
            detection['original_track_id'] = old
            if old is not None:
                new = roots[old]
                if new in used:
                    raise ValueError('Stitching creates simultaneous duplicate track IDs')
                used.add(new)
                detection['track_id'] = new
        if 'tracker_rows' in row:
            if 'original_tracker_rows' in row:
                raise ValueError('Refuse to overwrite original tracker matrix')
            row['original_tracker_rows'] = deepcopy(row['tracker_rows'])
            mapped = []
            for original in row['tracker_rows']:
                value = list(original)
                if len(value) < 5:
                    raise ValueError('Tracker row lacks ID column 4')
                tid = value[4]
                if isinstance(tid, bool) or not isinstance(tid, (int, float)) or not math.isfinite(tid) or int(tid) != tid:
                    raise ValueError('Tracker ID is not an exact integer')
                if int(tid) not in roots:
                    raise ValueError('Tracker row refers to unknown detection track')
                value[4] = roots[int(tid)]
                mapped.append(value)
            row['tracker_rows'] = mapped


def stitch_frame_rows(frame_rows, *, namespace, fps, gates, g1, clarification=None, checkpoint=None):
    require_production_ready(clarification)
    _checkpoint(checkpoint, 'M4 policy ready')
    ns, rate = _namespace(namespace), _fps(fps)
    if ns['sequence'] not in ('MOT20-01', 'MOT20-02'):
        raise ValueError('Frozen policy permits development sequences 01/02 only')
    gates = list(gates)
    gate_ids = set()
    for gate in gates:
        if gate.get('sequence') != ns['sequence']:
            raise ValueError('Gate sequence differs from track namespace')
        lid = gate.get('line_id')
        if not isinstance(lid, str) or not lid or lid in gate_ids:
            raise ValueError('Unique explicit gate IDs required')
        gate_ids.add(lid)
        gap_rectangle(gate)
    if not gates:
        raise ValueError('At least one finite gate is required')
    rows, tracks = collect_tracks(frame_rows, namespace=ns, checkpoint=checkpoint)
    starts = sorted((obs[0]['frame'], tid) for tid, obs in tracks.items())
    start_frames = [f for f, _ in starts]
    candidates, track_rejections, pair_rejections = [], [], []
    velocity_records = {}
    for tid, observations in sorted(tracks.items()):
        _checkpoint(checkpoint, 'M4 original predecessor')
        if observations[0]['point'] is None:
            track_rejections.append(dict(track_id=tid, role='successor', reason='invalid_raw_first_point'))
        end = observations[-1]
        velocity = endpoint_velocity(observations, rate)
        velocity_records[tid] = velocity
        if not velocity['valid']:
            track_rejections.append(dict(track_id=tid, role='predecessor', reason=velocity['reason']))
            continue
        nearby = [dict(line_id=gate['line_id'], distance_px=distance_to_gap(end['point'], gate), h_mid=float(gate['h_mid']))
                  for gate in gates if distance_to_gap(end['point'], gate) <= float(gate['h_mid'])]
        if not nearby:
            track_rejections.append(dict(track_id=tid, role='predecessor', reason='outside_all_finite_gap_neighborhoods'))
            continue
        first = bisect_right(start_frames, end['frame'])
        last = bisect_right(start_frames, Fraction(end['frame']) + rate)
        for start_frame, successor in starts[first:last]:
            _checkpoint(checkpoint, 'M4 original candidate pair')
            beginning = tracks[successor][0]
            if beginning['point'] is None:
                pair_rejections.append(dict(before_track_id=tid, after_track_id=successor, reason='invalid_raw_first_point'))
                continue
            delay = Fraction(start_frame-end['frame']) / rate
            predicted = [end['point'][i] + velocity['velocity_px_s'][i]*float(delay) for i in (0, 1)]
            error = math.hypot(predicted[0]-beginning['point'][0], predicted[1]-beginning['point'][1])
            try:
                height = height_at_point(g1, beginning['point'])
            except ValueError:
                pair_rejections.append(dict(before_track_id=tid, after_track_id=successor, reason='invalid_local_G1_height'))
                continue
            if not math.isfinite(error) or error > height:
                pair_rejections.append(dict(before_track_id=tid, after_track_id=successor, reason='prediction_error_exceeds_local_height'))
                continue
            candidates.append(dict(sequence=ns['sequence'], block=ns['block'], before_track_id=tid,
                after_track_id=successor, end_frame=end['frame'], start_frame=start_frame,
                delay_s=float(delay), delay_fraction=str(delay), error_px=error, local_height_px=height,
                predicted_point_native_px=predicted, successor_point_native_px=list(beginning['point']),
                eligible_gates=nearby, velocity=deepcopy(velocity)))
    links, mutual_rejections = select_mutual_unique(candidates, checkpoint=checkpoint)
    roots = resolve_chain_roots(tracks, links, checkpoint=checkpoint)
    _remap(rows, roots, ns, checkpoint)
    counts = Counter(r['reason'] for r in track_rejections + pair_rejections)
    counts.update(reason for row in mutual_rejections for reason in row['reasons'])
    k = (rate/2).numerator // (rate/2).denominator
    return dict(frames=rows, links=links,
        track_id_map=[dict(sequence=ns['sequence'], block=ns['block'], original_track_id=tid, stitched_track_id=roots[tid]) for tid in sorted(roots)],
        namespace=ns, candidate_decisions_performed=True, one_pass_original_tracks=True,
        policy_sha256=FROZEN_POLICY_SHA256, algorithm=deepcopy(EXPECTED_ALGORITHM),
        candidate_pairs=candidates, velocity_records=[dict(track_id=tid, **velocity_records[tid]) for tid in sorted(velocity_records)],
        rejections=dict(track_roles=track_rejections, pairs=pair_rejections, mutual_minima=mutual_rejections),
        statistics=dict(original_tracks=len(tracks), resulting_tracks=len(set(roots.values())), candidate_pairs=len(candidates),
                        accepted_links=len(links), rejection_reason_counts=dict(sorted(counts.items())),
                        velocity_window_frames=k, velocity_window_actual_s=float(Fraction(k)/rate),
                        velocity_window_actual_fraction=str(Fraction(k)/rate)),
        unchanged_fields='All raw detector fields and point values; only track IDs remapped, with original IDs/matrices saved')
