"""Explicit-input, development-only derivation of MOT20 crossing labels.

The scientific functions are exact frozen source excerpts. This module only
orchestrates inputs/outputs and adds provenance/QC fields. Import performs no I/O.
"""
from __future__ import annotations
from bisect import bisect_left, bisect_right
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import time

from . import frozen_labels_census as census
from . import frozen_labels_regions as regions

SEQUENCES = ('MOT20-02', 'MOT20-01')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def _json(path, value):
    with Path(path).open('xb') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2,
                                allow_nan=False).encode('utf-8') + b'\n')


def build_labels(gt_files, seqinfo_files, out):
    """Build complete transitions, including unconfirmed events, from 01/02 GT.

    Maps must have exactly MOT20-01 and MOT20-02 keys. Inputs are hash-bound to
    the official development files. No source GT rows are copied to the package.
    Returns metadata also saved as summary.json. An existing output fails closed.
    """
    if set(gt_files) != set(SEQUENCES) or set(seqinfo_files) != set(SEQUENCES):
        raise ValueError('Exactly MOT20-01 and MOT20-02 are authorized')
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    cpu_start, wall_start = time.process_time(), time.monotonic()

    def budget():
        if time.process_time() - cpu_start > 900 or time.monotonic() - wall_start > 900:
            raise TimeoutError('900 second label reconstruction limit')
        if shutil.disk_usage(out).free < 20 * 1024**3:
            raise RuntimeError('Less than20GiB free')

    inputs = []

    def read_source(seq, kind, path):
        budget()
        path = Path(path)
        before = path.stat()
        data = path.read_bytes()
        after = path.stat()
        actual = digest(data)
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError('Source changed during read')
        if actual != census.EXPECTED_INPUTS[seq][kind]:
            raise ValueError('Unexpected source bytes for ' + seq + ':' + kind)
        row = dict(sequence=seq, kind=kind, bytes=len(data), sha256=actual,
                   purpose='derive_labels_from_official_GT' if kind == 'gt' else 'native_metadata')
        inputs.append(row)
        with (out / 'read_ledger.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
        return data

    api = {name: getattr(regions, name) for name in
           ('signed_distance', 'zone_from_distances', 'extract_region_events')}
    import numpy as np
    geometry, models, summaries, all_items = [], {}, {}, []
    logical_line = 0
    try:
        for sequence in SEQUENCES:
            budget()
            seq = sequence[-2:]
            meta = census.parse_seqinfo(read_source(sequence, 'seqinfo', seqinfo_files[sequence]), seq)
            rows, static, input_stats = census.parse_gt(read_source(sequence, 'gt', gt_files[sequence]), meta)
            model = census.fit_model(rows, meta, np)
            lines = census.make_lines(seq, meta, model)
            windows = census.windows_for(seq)
            geometry.extend(lines)
            models[sequence] = model
            tracks, frame_rows = defaultdict(list), defaultdict(list)
            for row in rows:
                tracks[row.track_id].append(row)
                frame_rows[row.frame].append(row)
            track_frames = {tid: [row.frame for row in track] for tid, track in tracks.items()}
            seq_items, line_stats = [], []
            for line in lines:
                budget()
                polys = line['polygons']
                transitions, fragments, extraction_stats = api['extract_region_events'](
                    (census.observation(row, meta, polys, api) for row in rows), margin=0, max_gap_s=.5)
                gate_items = []
                for event in transitions:
                    budget()
                    tid = event['track_id']
                    fg = event['endpoints'][-1]['gt_frame_1based']
                    fzero = fg - 1
                    confirmation = census.truth_confirmation(event, tracks[tid], track_frames[tid], polys, meta, api)
                    attrs = census.attributes(event, tracks[tid], track_frames[tid], frame_rows, static)
                    members = [w['window_id'] for w in windows
                               if w['frame_interval_zero_based_half_open'][0] <= fzero < w['frame_interval_zero_based_half_open'][1]]
                    census.require(len(members) <= 1, 'Overlapping scoring windows')
                    logical_line += 1
                    item = dict(sequence=sequence, line_id=line['line_id'],
                        event_id=f'{seq}_{line["line_id"]}_{event["prediction_id"]}',
                        jsonl_logical_line=logical_line, gt_frame_1based=fg, frame_zero_based=fzero,
                        direction=event['direction'], track_id=tid, time_s=event['time_s'],
                        position_native_px=event['endpoints'][-1]['point'], window_id=members[0] if members else None,
                        in_scoring_window=bool(members), confirmed=confirmation['confirmed'],
                        truth_status='confirmed' if confirmation['confirmed'] else 'dont_care',
                        confirmation=confirmation, attributes=attrs, frozen_transition=event)
                    nearby = tracks[tid][bisect_left(track_frames[tid], fg - 25):bisect_right(track_frames[tid], fg + 25)]
                    item['audit'] = dict(
                        schema='crossing_label_audit_v0', human_qc='not_reviewed',
                        rule_confirmation_is_not_human_validation=True,
                        geometry_id=sequence + ':' + line['line_id'],
                        coordinate_origin='native_zero_based_GT_left_top_minus_one',
                        frame_origin='GT_one_based_and_function_zero_based_explicit',
                        source_gt_asset=sequence + ':gt',
                        source_support=dict(gt_frame_1based=event['endpoints'][0]['gt_frame_1based'],
                                            gt_file_physical_line=event['endpoints'][0]['gt_file_physical_line']),
                        target_support=dict(gt_frame_1based=fg,
                                            gt_file_physical_line=event['endpoints'][-1]['gt_file_physical_line']),
                        temporal_support_interval_s=event['transition_bracket_s'],
                        event_time_semantics=event['time_semantics'],
                        interpolation_used=False,
                        interpolation_policy='No filling or interpolation; first observed target-region entry.',
                        visibility_observations=[dict(gt_frame_1based=row.frame,
                            gt_file_physical_line=row.source_line, visibility=row.visibility) for row in nearby])
                    seq_items.append(item)
                    gate_items.append(item)
                line_stats.append(dict(line_id=line['line_id'], transitions=len(transitions),
                    fragments=len(fragments), extraction_stats=extraction_stats,
                    whole_sequence=census.summarize_population(gate_items, np)))
            scoring_items = [item for item in seq_items if item['in_scoring_window']]
            summary = dict(metadata=meta, input_counts=input_stats, windows=windows,
                whole_sequence=census.summarize_population(seq_items, np),
                scoring_windows=census.summarize_population(scoring_items, np), lines=line_stats)
            target = census.EXPECTED[seq]
            for key in ('transitions', 'confirmed', 'AB_share_3dp'):
                census.require(summary['scoring_windows'][key] == target[key], 'Frozen census target differs: ' + sequence + ':' + key)
            census.require(all(abs(a-b) <= .001 for a, b in zip(model['coefficients'], target['coefficients'])), 'G1 target differs')
            census.require(all(line['h_mid_absolute_error'] <= .01 for line in lines), 'Geometry target differs')
            summaries[sequence] = summary
            all_items.extend(seq_items)
        budget()
        with (out / 'transitions.jsonl.gz').open('xb') as raw:
            with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as stream:
                for item in all_items:
                    stream.write(canonical(item) + b'\n')
        _json(out / 'geometry.json', dict(schema='crossing_geometry_v0', line_count=len(geometry),
              polygon_count=len(geometry)*2, lines=geometry))
        _json(out / 'height_models.json', models)
        _json(out / 'source_manifest.json', dict(schema='label_inputs_v0', inputs=inputs,
              raw_GT_redistributed=False, no_image_or_video_inputs=True,
              scientific_source_files=census.SOURCE_BINDINGS + regions.SOURCE_BINDINGS))
        summary = dict(schema='crossing_labels_summary_v0', sequences=summaries,
            complete=True, sequence_order=list(SEQUENCES), transitions=len(all_items),
            confirmed=sum(item['confirmed'] for item in all_items),
            human_qc='not_reviewed', source_GT_copied=False,
            derivation_uses_interpolation=False, numpy_version=np.__version__,
            scientific_fields_preserved=True, label_license='CC BY-NC-SA 3.0')
        _json(out / 'summary.json', summary)
        _json(out / 'build_run.json', dict(cpu_s=time.process_time()-cpu_start,
              elapsed_s=time.monotonic()-wall_start, no_inference=True, no_tracking=True,
              no_scoring=True, no_human_verification=True))
        if sum(p.stat().st_size for p in out.rglob('*') if p.is_file()) > 2*1024**3:
            raise RuntimeError('Label output exceeds2GiB')
        return summary
    except BaseException as exc:
        _json(out / 'STOP.json', dict(complete=False, error=repr(exc),
              cpu_s=time.process_time()-cpu_start, elapsed_s=time.monotonic()-wall_start,
              partial_output_preserved=True))
        raise
