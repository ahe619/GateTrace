"""Score any tracker's MOTChallenge output with the frozen event chain and E1 v2 (v0.1).

For each development sequence: the output boxes are parsed strictly, the frozen
point rule and event chain derive final crossing events per gate, and the
package's frozen E1-v2 scorer rebuilds identities from the same output boxes and
matches them to the rule-confirmed GT events. The scoring loop is the v0
src/score.py loop with events produced here instead of read from a cache.
Import performs no I/O.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import time

from .score import _serial, _write, _optimal_ranges, _aggregate_ranges, _relative
from . import events as event_chain
from . import motchallenge
from . import frozen_labels_census as census

SEQS = ('MOT20-01', 'MOT20-02')
GATES = ('H_30', 'H_50', 'H_70', 'V_25', 'V_50', 'V_75')
BINS = ('low', 'mid_low', 'mid_high', 'high')
LIMIT_S = 900


def score_tracks(gt_files, labels_dir, track_files, out, package, tracker_name=None):
    """Score one tracker. All maps are keyed exactly by MOT20-01/02.

    gt_files/track_files map sequences to explicit files; labels_dir is the
    output of build_labels (parity-checked against the bundled labels by the
    caller); out must be new. Returns the serializable score report.
    """
    if set(gt_files) != set(SEQS) or set(track_files) != set(SEQS):
        raise ValueError('Exactly development sequences MOT20-01/02 are required')
    labels_dir = Path(labels_dir)
    out = Path(out)
    package = Path(package)
    out.mkdir(parents=True, exist_ok=False)
    cpu = time.process_time()
    started = time.monotonic()
    reads = []

    def budget():
        if time.process_time() - cpu > LIMIT_S or time.monotonic() - started > LIMIT_S:
            raise TimeoutError('Scoring exceeds 900 s; partial outputs preserved')
        if shutil.disk_usage(out).free < 20 * 1024 ** 3:
            raise OSError('Below 20 GiB free')

    def read(path, alias, expected=None):
        budget()
        raw = Path(path).read_bytes()
        actual = dict(path=alias, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        reads.append(actual)
        if expected and any(actual[k] != expected[k] for k in ('bytes', 'sha256')):
            raise ValueError('Bound input changed: ' + alias)
        return raw

    _write(out / 'started.json', dict(schema='tracker_score_start_v0_1', tracker=tracker_name, scopes=list(SEQS),
                                     population='whole_sequence', cpu_limit_s=LIMIT_S, no_inference=True,
                                     no_tracking=True, events_from='output-box bottom-centre, frozen point_for',
                                     command=sys.orig_argv, python=sys.executable))
    try:
        frozen_doc = json.loads(read(package / 'src/frozen_score/provenance.json', 'code:frozen_score/provenance.json'))
        for mod in frozen_doc['modules']:
            ref = mod['output']
            read(_relative(package, ref['path']), 'code:' + ref['path'], ref)
        prefix = (__package__ + '.') if __package__ else ''
        e1 = importlib.import_module(prefix + 'frozen_score.e1')
        identity = importlib.import_module(prefix + 'frozen_score.identity')
        matching = importlib.import_module(prefix + 'frozen_score.matching')
        view = importlib.import_module(prefix + 'frozen_score.labels_view')
        aggregation = importlib.import_module(prefix + 'frozen_score.aggregate')
        api, make_height_model, point_for, event_view = event_chain.load_api(package, read)
        import numpy as np

        summary = json.loads(read(labels_dir / 'summary.json', 'labels:summary.json'))
        geometry = json.loads(read(labels_dir / 'geometry.json', 'labels:geometry.json'))
        height_models = json.loads(read(labels_dir / 'height_models.json', 'labels:height_models.json'))
        transitions = [json.loads(line) for line in gzip.decompress(
            read(labels_dir / 'transitions.jsonl.gz', 'labels:transitions.jsonl.gz')).decode('utf-8-sig').splitlines()
            if line.strip()]
        if any(t['sequence'] not in SEQS for t in transitions):
            raise ValueError('Label sequence outside development scope')
        gtviews = [view.gt_row(r, 'labels/transitions.jsonl.gz', i) for i, r in enumerate(transitions, 1)]
        if sum(bool(t['confirmed']) for t in transitions) != 724:
            raise ValueError('Whole-sequence population must be 724; do not substitute core671')
        lines = {(g['sequence'], g['line_id']): g for g in geometry['lines']}
        if set(lines) != {(s, g) for s in SEQS for g in GATES}:
            raise ValueError('Geometry must contain exactly the 12 development gates')

        units, range_units, event_summaries, input_stats = [], [], {}, {}
        for seq in SEQS:
            meta = summary['sequences'][seq]['metadata']
            length = meta['seqLength']
            if meta['fps'] != 25:
                raise ValueError('Frozen protocol requires 25 fps')
            gtbytes = read(Path(gt_files[seq]), 'gt:' + seq)
            if hashlib.sha256(gtbytes).hexdigest() != census.EXPECTED_INPUTS[seq]['gt']:
                raise ValueError('GT differs from development source binding')
            gt, classes = identity.parse_gt(gtbytes.decode('utf-8-sig'), length)
            del gtbytes
            frames, stats = motchallenge.parse_results(read(Path(track_files[seq]), 'tracks:' + seq).decode('utf-8-sig'),
                                                       length)
            # Identity evidence from the actual output boxes; file row order within a frame is the tie key.
            outputobs = defaultdict(list)
            with gzip.open(out / (seq + '_frame_identity.jsonl.gz'), 'xt', encoding='utf-8') as sink:
                for sf in range(1, length + 1):
                    budget()
                    pool = [dict(key=i, index=i, tid=r['track_id'], box=r['box']) for i, r in enumerate(frames.get(sf, []))]
                    records, _, audit = e1.assign(pool, gt.get(sf, []), matching.solve, np)
                    observations = [dict(source_frame=sf, track_id=z['tid'], output_row_index=z['index'],
                                         gt_id=z['gt_id'], gt_class=z['gt_class'], gt_line=z['gt_line'], status=z['status'],
                                         box=z['box'], assigned_iou=z['assigned_iou'], margin=z['margin']) for z in records]
                    for o in observations:
                        outputobs[o['track_id']].append(o)
                    sink.write(json.dumps(_serial(dict(source_frame=sf, observations=observations, output_assignment=audit)),
                                          separators=(',', ':'), allow_nan=False) + '\n')
            # Frozen event chain on bottom-centre points of the same output boxes.
            chain_obs, point_totals = event_chain.build_observations(frames, meta['width'], meta['height'], length,
                                                                     point_for, event_view)
            input_stats[seq] = dict(stats, **point_totals)
            seq_evidence = []
            event_summaries[seq] = {}
            for gate in GATES:
                budget()
                event = event_chain.gate_events(api, make_height_model, chain_obs, sequence=seq, gate_id=gate,
                                                metadata=meta, height_model=height_models[seq],
                                                geometry_line=lines[(seq, gate)])
                folder = out / 'events' / seq
                folder.mkdir(parents=True, exist_ok=True)
                with gzip.open(folder / (gate + '_events.json.gz'), 'xt', encoding='utf-8') as sink:
                    json.dump(event, sink, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
                event_summaries[seq][gate] = event_chain.final_event_summary(event)
                preds = event['final_events']
                del event
                if event_summaries[seq][gate]['final'] != len(preds):
                    raise AssertionError('Event summary differs')
                if len({p['prediction_id'] for p in preds}) != len(preds):
                    raise ValueError('Duplicate final event ID')
                for p in preds:
                    if p['sequence'] != seq or p['gate_id'] != gate or p['target_frame'] + 1 != p['source_frame']:
                        raise ValueError('Event frame contract')
                    if p['track_id'] not in outputobs or not 1 <= p['source_frame'] <= length:
                        raise ValueError('Event lacks emitted track/anchor')
                    if abs(p['time_s'] - (p['source_frame'] - 1) / 25) > 1e-9:
                        raise ValueError('Event time mismatch')
                    if '_identity' in p or 'identity_association' in p:
                        raise ValueError('Unexpected identity field on a fresh event')
                    p['_identity'] = identity.event_identity(outputobs[p['track_id']], p['source_frame'], classes)
                selected = [(r, g) for r, g in zip(transitions, gtviews)
                            if r['sequence'] == seq and r['line_id'] == gate and r['confirmed']]
                selected.sort(key=lambda z: (z[0]['gt_frame_1based'], z[0]['track_id'], z[0]['event_id']))
                truths = [dict(id=r['event_id'], frame=int(r['gt_frame_1based']), gid=int(r['track_id']),
                               direction=r['direction'], position=r['position_native_px'], h=g['h'], bin=g['bin'])
                          for r, g in selected]
                matched, _, _, audit = e1.event_matching(preds, truths, matching.solve, matching.can_match_right_optimally)
                units.append(dict(sequence=seq, gate=gate, N_GT=len(truths), N_final=len(preds), correct=len(matched),
                                  identity_statuses=dict(Counter(p['_identity']['status'] for p in preds)),
                                  bins={b: dict(correct=sum(j in matched for j, g in enumerate(truths) if g['bin'] == b),
                                                GT=sum(g['bin'] == b for g in truths)) for b in BINS}))
                range_units.append(dict(sequence=seq, gate=gate, ranges=_optimal_ranges(audit, truths, matching)))
                seq_evidence.append(dict(gate=gate, **audit))
            _write(out / (seq + '_event_matching.json'), seq_evidence)
            del chain_obs, outputobs, frames
        main = dict(name='E1 v2 whole sequence', aggregate=aggregation.aggregate(units),
                    by_sequence={s: aggregation.aggregate([u for u in units if u['sequence'] == s]) for s in SEQS})
        agg = main['aggregate']
        table = dict(identity_recall_by_bin={b: dict(matched=agg['bins'][b]['numerator'],
                                                     confirmed_GT=agg['bins'][b]['denominator'])
                                             for b in BINS},
                     identity_recall_all=dict(matched=agg['correct'], confirmed_GT=agg['GT']),
                     identity_precision=dict(matched=agg['correct'], final_events=agg['final_events']))
        report = dict(schema='tracker_score_result_v0_1', status='TECHNICAL_RESULT_NOT_INDEPENDENT_QC',
                      tracker=tracker_name, summary_table=table, main=main,
                      population='whole_sequence_724_not_core_671',
                      event_source='frozen event chain on output-box bottom-centres (point_for); geometry and G1 from rebuilt labels',
                      identity_pool='the same output boxes; row order within a frame is the frozen tie key',
                      unknown_precision_policy='Unknown, ambiguous, mixed and ignore outputs remain in ALL-final denominator',
                      human_QC='not_reviewed',
                      range_semantics='All globally max-cardinality/minimum-exact-time matchings, independently per sequence/gate; not confidence intervals',
                      anonymous_range_policy='All final events satisfy frozen legal time/direction/position gates; no ignore/neutral deletion. This is not T3 clean anonymous scoring.',
                      matching_ranges=dict(aggregate=_aggregate_ranges(range_units),
                                           by_sequence={s: _aggregate_ranges([u for u in range_units if u['sequence'] == s])
                                                        for s in SEQS}),
                      input_stats=input_stats, numpy=np.__version__,
                      cpu_s=time.process_time() - cpu, elapsed_s=time.monotonic() - started,
                      no_inference=True, no_tracking=True, no_test_data=True, seed=None)
        _write(out / 'units.json', dict(main=units))
        _write(out / 'matching_ranges.json', range_units)
        _write(out / 'final_events.json', event_summaries)
        _write(out / 'scores.json', report)
        _write(out / 'read_ledger.json', reads)
        _write(out / 'complete.json', dict(status='COMPLETE', tracker=tracker_name, cpu_s=time.process_time() - cpu,
                                          elapsed_s=time.monotonic() - started, human_QC='not_reviewed'))
        return _serial(report), _serial(units), _serial(event_summaries)
    except BaseException as exc:
        _write(out / 'FAIL.json', dict(status='FAIL_PRESERVED', error=repr(exc), reads=reads,
                                      cpu_s=time.process_time() - cpu, elapsed_s=time.monotonic() - started))
        raise
