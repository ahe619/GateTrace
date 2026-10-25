"""Supplementary label lineage; no scientific event field is modified.

Import has no I/O. ``lineage_record`` is pure; ``enrich_labels`` reads only the
new sample's derived transitions/geometry and writes a separate metadata table.
"""
import gzip
import hashlib
import json
from pathlib import Path
import time


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def lineage_record(event, geometry):
    """Project an observed target point along its gate, without interpolation."""
    if (event['sequence'], event['line_id']) != (geometry['sequence'], geometry['line_id']):
        raise ValueError('Gate/sequence lineage mismatch')
    if event['audit']['human_qc'] != 'not_reviewed':
        raise ValueError('This release candidate has no completed human QC')
    axis = 0 if geometry['orientation'] == 'H' else 1
    lo, hi = geometry['line_extent_px']
    if hi <= lo:
        raise ValueError('Invalid gate extent')
    point = event['position_native_px']
    u = (point[axis] - lo) / (hi - lo)
    transition = event['frozen_transition']
    source, target = transition['endpoints']
    confirming = event['confirmation']['first_confirming_observation']
    return dict(
        schema='crossing_label_lineage_v0', event_id=event['event_id'],
        sequence=event['sequence'], line_id=event['line_id'],
        gate_position_u=u,
        gate_position_u_semantics='Unclipped along-gate projection of first observed target-region point; NOT an estimated physical crossing point.',
        gate_position_u_axis='native_x' if axis == 0 else 'native_y',
        gate_position_u_reference_extent_px=[lo, hi],
        observed_target_position_native_px=point,
        actual_line_intersection_native_px=None,
        actual_line_intersection_status='not_estimated',
        source_annotation_interpolation='unknown_not_provided',
        derivation_interpolation_used=False,
        support_frame_interval_one_based=[source['gt_frame_1based'], target['gt_frame_1based']],
        support_time_interval_s=transition['transition_bracket_s'],
        support_interval_semantics='Observed source/target bracket, not a calibrated confidence interval for physical crossing.',
        source_GT_line=source['gt_file_physical_line'],
        target_GT_line=target['gt_file_physical_line'],
        confirming_GT_line=None if confirming is None else confirming['gt_file_physical_line'],
        confirming_frame_one_based=None if confirming is None else confirming['gt_frame_1based'],
        unobserved_native_frames_in_support=transition['unobserved_native_frames'],
        invalid_point_observations_in_support=transition['excluded_point_observations'],
        gap_region_observations_in_support=transition['gap_zone_observations'],
        maximum_raw_observation_gap_s=transition['maximum_raw_observation_gap_s'],
        missing_frame_positions='not_expanded; count and supporting endpoints are preserved from frozen derivation',
        rule_confirmed=event['confirmed'], human_qc='not_reviewed',
        source_visibility_gt_frames_inclusive=event['attributes']['visibility_gt_frames_inclusive'],
        source_visibility_rows=event['attributes']['visibility_observed_rows'])


def enrich_labels(labels_dir, out_path):
    """Return provenance metadata after writing a separate JSONL.gz table."""
    labels_dir, out_path = Path(labels_dir), Path(out_path)
    cpu_start, wall_start = time.process_time(), time.monotonic()
    inputs = []

    def read(name):
        data = (labels_dir / name).read_bytes()
        inputs.append(dict(asset=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
        return data

    geometry = json.loads(read('geometry.json'))
    gates = {(g['sequence'], g['line_id']): g for g in geometry['lines']}
    if set(s for s, _ in gates) != {'MOT20-01', 'MOT20-02'}:
        raise ValueError('Development-only geometry required')
    rows = [json.loads(line) for line in gzip.decompress(read('transitions.jsonl.gz')).splitlines()]
    if len({row['event_id'] for row in rows}) != len(rows):
        raise ValueError('Duplicate event ID')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('xb') as raw:
        with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as stream:
            for row in rows:
                if time.process_time()-cpu_start>900 or time.monotonic()-wall_start>900:
                    raise TimeoutError('900 second metadata limit')
                stream.write(_canonical(lineage_record(row, gates[row['sequence'], row['line_id']])) + b'\n')
    content = out_path.read_bytes()
    return dict(schema='crossing_lineage_build_v0', rows=len(rows), inputs=inputs,
        output=dict(asset=out_path.name, bytes=len(content), sha256=hashlib.sha256(content).hexdigest()),
        original_scientific_files_unchanged=True, no_external_data_read=True,
        no_interpolation=True, human_qc='not_reviewed',
        cpu_s=time.process_time()-cpu_start,elapsed_s=time.monotonic()-wall_start)
