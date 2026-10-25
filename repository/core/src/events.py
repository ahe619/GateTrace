"""Frozen crossing-event chain over tracker output boxes (v0.1).

Orchestration only. Every numerical rule (point rule, region membership,
transition extraction, C1 confirmation, R1+R2 de-duplication) is a verified
verbatim copy in src/frozen_events, assembled exactly as the panel run's
scripts/r15e24_events.py::load_frozen assembled it. Import performs no I/O.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import importlib
import json
import math
from pathlib import Path

# load_frozen compiled these members, in this order, into one namespace.
CHAIN_MEMBERS = ('nearest_boundary', 'signed_distance', 'zone_from_distances', 'extract_region_events',
                 'height_at_foot', 'edge_distance', 'evidence', 'VARIANTS', 'SOURCE_ZONE', 'TARGET_ZONE',
                 '_event_frame', '_event_key', '_valid_point', '_observation_detail', '_window',
                 'transform_events', 'finite_point', 'keypoint_mean', 'predict_height', 'select_point')


def _relative(root, name):
    if not isinstance(name, str) or '\\' in name or Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('Expected portable relative path')
    return Path(root) / name


def load_api(package, read):
    """Verify src/frozen_events bindings, then return (FrozenEvents api, make_height_model, point_for, event_view).

    read(path, alias, expected) must return bytes and verify a binding.
    """
    package = Path(package)
    doc = json.loads(read(package / 'src/frozen_events/provenance.json', 'code:frozen_events/provenance.json', None))
    if doc.get('schema') != 'frozen_events_source_v1' or doc.get('scientific_functions_changed') is not False:
        raise ValueError('Unexpected frozen_events provenance')
    outputs = {}
    for module in doc['modules']:
        ref = module['output']
        outputs[ref['path']] = ref
    if set(outputs) != {'src/frozen_events/chain.py', 'src/frozen_events/adapter.py',
                        'src/frozen_events/point.py', 'src/frozen_events/event_view.py'}:
        raise ValueError('Unexpected frozen_events module set')
    for path, ref in sorted(outputs.items()):
        read(_relative(package, path), 'code:' + path, ref)
    prefix = (__package__ + '.') if __package__ else ''
    chain = importlib.import_module(prefix + 'frozen_events.chain')
    adapter = importlib.import_module(prefix + 'frozen_events.adapter')
    point = importlib.import_module(prefix + 'frozen_events.point')
    view = importlib.import_module(prefix + 'frozen_events.event_view')
    import numpy
    if chain.np is not numpy or chain.math is not math or chain.deepcopy is not deepcopy \
            or chain.defaultdict is not defaultdict or chain.Counter is not Counter:
        raise ValueError('Frozen chain namespace differs from load_frozen')
    namespace = {'__name__': 'r15e24_exact_frozen_functions', 'math': math, 'defaultdict': defaultdict,
                 'Counter': Counter, 'deepcopy': deepcopy, 'np': numpy}
    for name in CHAIN_MEMBERS:
        namespace[name] = getattr(chain, name)
    audit = [dict(path=m['source']['path'], sha256=m['source']['sha256'], output=m['output']['path'],
                  exact_original_ast=True,
                  selected_members=[dict(name=f['name'], first_line=f['start_line'], last_line=f['end_line'],
                                         ast_source_segment_sha256_utf8=f['source_segment_sha256'])
                                    for f in m['functions']])
             for m in doc['modules']]
    return adapter.FrozenEvents(namespace, audit), adapter.make_height_model, point.point_for, view.event_view


def build_observations(frames, width, height, seq_length, point_for, event_view):
    """Panel-run observation construction (scripts/r15_sota83d_run_v2.py) from parsed MOT rows.

    For each frame in ascending order and each row in file order: an output
    record with the native box, point = point_for(box) (bottom-centre, frozen
    validity rule), point_source 'box_bottom_center', then event_view(output, frame0).
    """
    observations = []
    totals = Counter()
    for source_frame in range(1, seq_length + 1):
        frame = source_frame - 1
        for index, row in enumerate(frames.get(source_frame, [])):
            x = dict(emitted_output_index=index, track_id=row['track_id'], box=list(row['box']), score=row['conf'])
            point, reason, outside = point_for(x['box'], width, height)
            x.update(point=point, point_source='box_bottom_center', point_invalid_reason=reason, point_outside_image=outside)
            observations.append(event_view(x, frame))
            totals['outputs'] += 1
            totals['valid_points'] += int(point is not None)
            if reason is not None:
                totals['invalid_' + reason] += 1
    return observations, dict(totals)


def gate_events(api, make_height_model, observations, *, sequence, gate_id, metadata, height_model, geometry_line):
    """One sequence/gate through the frozen chain with the package geometry and G1 model."""
    if geometry_line['sequence'] != sequence or geometry_line['line_id'] != gate_id:
        raise ValueError('Geometry scope differs')
    ranges = height_model['fitting_coordinate_range']
    model = make_height_model(height_model['coefficients'],
                              {'head_x_norm': ranges['x_normalized'], 'head_y_norm': ranges['y_top_normalized']})
    event = api.evaluate_sequence_gate(observations, sequence=sequence, gate_id=gate_id,
                                       width=metadata['width'], height=metadata['height'],
                                       nb_frames=metadata['seqLength'], fps=25, model=model,
                                       polygons=geometry_line['polygons'])
    event.pop('observations')
    return event


def final_event_summary(event):
    """Compact, comparison-ready view of one gate's final events."""
    return dict(candidates=len(event['raw_candidates']), confirmed=len(event['raw_confirmed_events']),
                final=len(event['final_events']),
                final_events=[dict(prediction_id=p['prediction_id'], track_id=p['track_id'],
                                   fragment_index=p['fragment_index'], direction=p['direction'],
                                   source_frame=p['source_frame'], target_frame=p['target_frame'],
                                   group_id=p['group_id'], member_prediction_ids=list(p['member_prediction_ids']),
                                   crossing_position_native_px=list(p['crossing_position_native_px']))
                              for p in event['final_events']])
