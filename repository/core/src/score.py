"""Recompute whole-sequence E1-v2 identity scoring from explicit public inputs.

This module performs no I/O at import. It does not run detection, tracking,
M4 or the event decoder. Its examples are already emitted boxes/final events.
The 724-event main population is separate from the unimplemented 671-event core.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from fractions import Fraction
import gzip
import hashlib
import importlib
import json
import math
from pathlib import Path
import shutil
import sys
import time

SEQS=('MOT20-01','MOT20-02')
GATES=('H_30','H_50','H_70','V_25','V_50','V_75')
BINS=('low','mid_low','mid_high','high')

def _serial(value):
    if isinstance(value,Fraction):return str(value)
    if isinstance(value,dict):return {str(k):_serial(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [_serial(v) for v in value]
    if isinstance(value,set):return sorted(_serial(v) for v in value)
    return value

def _write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(_serial(value),stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')

def _relative(root,name):
    if not isinstance(name,str) or '\\' in name or Path(name).is_absolute():raise ValueError('Expected portable relative path')
    path=(root/name).resolve()
    if not path.is_relative_to(root.resolve()):raise ValueError('Path escapes explicit root')
    return path

def _integer(x):
    if isinstance(x,bool) or not isinstance(x,int):raise ValueError('Expected JSON integer')
    return x

def _pool(row):
    """Public sanitized cache preserves the frozen raw-index identity tie order."""
    if set(row)!= {'frame','source_frame','time_s','outputs'}:raise ValueError('Unexpected frame fields')
    out=[];seen_ids=set();seen_indices=set()
    for x in row['outputs']:
        if set(x)!={'raw_detection_index','track_id','box','original_track_id'}:raise ValueError('Unexpected output-box fields')
        idx=_integer(x['raw_detection_index']);tid=_integer(x['track_id']);_integer(x['original_track_id'])
        if idx<0 or tid in seen_ids or idx in seen_indices:raise ValueError('Duplicate or negative output key')
        seen_ids.add(tid);seen_indices.add(idx)
        out.append(dict(key=idx,index=idx,tid=tid,box=x['box']))
    return sorted(out,key=lambda r:r['key'])

def _optimal_ranges(audit,truths,matching):
    """Bounds over all first-two-objective optima, not uncertainty intervals."""
    answer={}
    for mode in ('identity','anonymous_all_final'):
        if mode=='identity':edges=audit['edges']
        else:edges=[dict(left=e['left'],right=e['right'],cost=e['time_cost']) for e in audit['anonymous_legal_edges']]
        left,right=audit['pred_keys'],audit['gt_keys']
        canonical=matching.solve(left,right,edges)
        assigned={r for _,r in canonical['pairs']}
        bins={}
        for b in BINS:
            selected={right[i] for i,g in enumerate(truths) if g['bin']==b}
            weights={(e['left'],e['right']):1 for e in edges if e['right'] in selected}
            bounds=matching.optimal_secondary_range(left,right,edges,weights)
            bins[b]=dict(minimum=int(bounds['minimum']),maximum=int(bounds['maximum']),
                canonical=sum(r in assigned for r in selected),denominator=len(selected),
                min_witness=bounds['min_solution']['pairs'],max_witness=bounds['max_solution']['pairs'])
        answer[mode]=dict(cardinality=canonical['cardinality'],exact_time_cost=canonical['total_cost'],
            canonical_pairs=canonical['pairs'],bins=bins)
    return answer

def _aggregate_ranges(units):
    # Sequence/gate graphs are disjoint: a global optimum is their Cartesian
    # product. Summing per-graph bounds is exactly attainable, not a relaxation.
    return {mode:dict(cardinality=sum(u['ranges'][mode]['cardinality'] for u in units),
        exact_time_cost=sum((u['ranges'][mode]['exact_time_cost'] for u in units),Fraction(0)),
        bins={b:dict(minimum=sum(u['ranges'][mode]['bins'][b]['minimum'] for u in units),
                    maximum=sum(u['ranges'][mode]['bins'][b]['maximum'] for u in units),
                    canonical=sum(u['ranges'][mode]['bins'][b]['canonical'] for u in units),
                    denominator=sum(u['ranges'][mode]['bins'][b]['denominator'] for u in units)) for b in BINS})
        for mode in ('identity','anonymous_all_final')}

def score(gt_files:dict, labels_dir:Path, example_root:Path, out:Path):
    """Rebuild frame/event identities and exact matching; raise on any old parity failure.

    gt_files maps exactly MOT20-01/02 to their caller-supplied gt.txt paths.
    labels_dir must be the output of build_labels. example_root points to this
    package's examples/yolox_v11, and out must be a fresh directory. The original
    GT files are read but never copied. All scientific source functions are
    verified frozen copies, with zero algorithm changes.
    """
    if set(gt_files)!=set(SEQS):raise ValueError('Exactly development sequences 01/02 are required')
    labels_dir=Path(labels_dir);example_root=Path(example_root);out=Path(out)
    out.mkdir(parents=True,exist_ok=False)
    cpu=time.process_time();started=time.monotonic();reads=[]
    def budget():
        if time.process_time()-cpu>900 or time.monotonic()-started>900:raise TimeoutError('Scoring exceeds900s; partial outputs preserved')
        if shutil.disk_usage(out).free<20*1024**3:raise OSError('Below20GiB free')
    def read(path,alias,expected=None):
        budget();raw=Path(path).read_bytes();actual=dict(path=alias,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        reads.append(actual)
        if expected and any(actual[k]!=expected[k] for k in ('bytes','sha256')):raise ValueError('Bound input changed: '+alias)
        return raw
    _write(out/'started.json',dict(schema='release85_score_start_v1',scopes=list(SEQS),
        population='whole_sequence',cpu_limit_s=900,no_inference=True,no_tracking=True,
        no_stored_identity_used=True,seed=None,command=sys.orig_argv,python=sys.executable,
        prefix=sys.prefix,base_prefix=sys.base_prefix))
    try:
        src=Path(__file__).resolve().parent;package=src.parent
        frozen_doc=json.loads(read(src/'frozen_score/provenance.json','code:frozen_score/provenance.json'))
        for mod in frozen_doc['modules']:
            ref=mod['output'];read(_relative(package,ref['path']),'code:'+ref['path'],ref)
        prefix=(__package__+'.') if __package__ else ''
        e1=importlib.import_module(prefix+'frozen_score.e1')
        identity=importlib.import_module(prefix+'frozen_score.identity')
        matching=importlib.import_module(prefix+'frozen_score.matching')
        view=importlib.import_module(prefix+'frozen_score.labels_view')
        aggregation=importlib.import_module(prefix+'frozen_score.aggregate')
        import numpy as np
        cache=json.loads(read(example_root/'cache_manifest.json','examples:cache_manifest.json'))
        if cache['schema']!='release85_example_cache_v1' or set(cache['sequences'])!=set(SEQS):raise ValueError('Cache scope/schema mismatch')
        expected_ref=cache['expected']
        expected=json.loads(read(_relative(package,expected_ref['path']),'expected:'+expected_ref['path'],expected_ref))
        summary=json.loads(read(labels_dir/'summary.json','labels:summary.json'))
        transitions=[json.loads(line) for line in gzip.decompress(read(labels_dir/'transitions.jsonl.gz','labels:transitions.jsonl.gz')).decode('utf-8-sig').splitlines() if line.strip()]
        if any(t['sequence'] not in SEQS for t in transitions):raise ValueError('Label sequence outside development scope')
        gtviews=[view.gt_row(r,'labels/transitions.jsonl.gz',i) for i,r in enumerate(transitions,1)]
        if sum(bool(t['confirmed']) for t in transitions)!=724:raise ValueError('Whole-sequence population must be724; do not substitute core671')
        units=[];range_units=[]
        for seq in SEQS:
            meta=cache['sequences'][seq]['metadata'];length=meta['seqLength']
            lm=summary['sequences'][seq]['metadata']
            if any(meta[k]!=lm[k] for k in ('fps','width','height','seqLength')) or meta['fps']!=25:raise ValueError('Rebuilt label/cache metadata mismatch')
            gtbytes=read(Path(gt_files[seq]),'gt:'+seq)
            if hashlib.sha256(gtbytes).hexdigest()!=cache['sequences'][seq]['GT_sha256']:raise ValueError('GT differs from development source binding')
            gt,classes=identity.parse_gt(gtbytes.decode('utf-8-sig'),length);del gtbytes
            files=cache['sequences'][seq]['files'];ref=files['frames']
            compact=read(_relative(example_root,ref['path']),'example:'+ref['path'],ref)
            outputobs=defaultdict(list);n=0
            with gzip.open(out/(seq+'_frame_identity.jsonl.gz'),'xt',encoding='utf-8') as sink:
                for text in gzip.decompress(compact).decode('utf-8').splitlines():
                    budget();r=json.loads(text);sf=n+1
                    if r['source_frame']!=sf or r['frame']!=n or abs(r['time_s']-n/25)>1e-9:raise ValueError('Cache frame order/time differs')
                    records,_,audit=e1.assign(_pool(r),gt.get(sf,[]),matching.solve,np)
                    observations=[dict(source_frame=sf,track_id=z['tid'],raw_detection_index=z['index'],
                        gt_id=z['gt_id'],gt_class=z['gt_class'],gt_line=z['gt_line'],status=z['status'],
                        box=z['box'],assigned_iou=z['assigned_iou'],margin=z['margin']) for z in records]
                    for o in observations:outputobs[o['track_id']].append(o)
                    # Retain exact identity evidence without copying the original full GT.
                    sink.write(json.dumps(_serial(dict(source_frame=sf,observations=observations,output_assignment=audit)),separators=(',',':'),allow_nan=False)+'\n')
                    n+=1
            if n!=length:raise ValueError('Incomplete output-box cache')
            del compact
            seq_evidence=[]
            for gate in GATES:
                budget();ref=files[gate+'_events'];doc=json.loads(read(_relative(example_root,ref['path']),'example:'+ref['path'],ref))
                if doc['sequence']!=seq or doc['gate_id']!=gate or doc['metadata']['nb_frames']!=length or doc['metadata']['fps']!=25:raise ValueError('Final event metadata mismatch')
                preds=doc['final_events']
                if len({p['prediction_id'] for p in preds})!=len(preds):raise ValueError('Duplicate final event ID')
                for p in preds:
                    if p['sequence']!=seq or p['gate_id']!=gate or p['target_frame']+1!=p['source_frame']:raise ValueError('Event frame contract')
                    if p['track_id'] not in outputobs or not 1<=p['source_frame']<=length:raise ValueError('Event lacks emitted track/anchor')
                    if abs(p['time_s']-(p['source_frame']-1)/25)>1e-9:raise ValueError('Event time mismatch')
                    if '_identity' in p or 'identity_association' in p:raise ValueError('Cached old identity answer prohibited')
                    p['_identity']=identity.event_identity(outputobs[p['track_id']],p['source_frame'],classes)
                selected=[(r,g) for r,g in zip(transitions,gtviews) if r['sequence']==seq and r['line_id']==gate and r['confirmed']]
                selected.sort(key=lambda z:(z[0]['gt_frame_1based'],z[0]['track_id'],z[0]['event_id']))
                truths=[dict(id=r['event_id'],frame=int(r['gt_frame_1based']),gid=int(r['track_id']),direction=r['direction'],
                    position=r['position_native_px'],h=g['h'],bin=g['bin']) for r,g in selected]
                matched,_,_,audit=e1.event_matching(preds,truths,matching.solve,matching.can_match_right_optimally)
                units.append(dict(sequence=seq,gate=gate,N_GT=len(truths),N_final=len(preds),correct=len(matched),
                    identity_statuses=dict(Counter(p['_identity']['status'] for p in preds)),
                    bins={b:dict(correct=sum(j in matched for j,g in enumerate(truths) if g['bin']==b),GT=sum(g['bin']==b for g in truths)) for b in BINS}))
                range_units.append(dict(sequence=seq,gate=gate,ranges=_optimal_ranges(audit,truths,matching)))
                seq_evidence.append(dict(gate=gate,**audit))
            _write(out/(seq+'_event_matching.json'),seq_evidence)
        main=dict(name='E1 v2 whole sequence',aggregate=aggregation.aggregate(units),
             by_sequence={s:aggregation.aggregate([u for u in units if u['sequence']==s]) for s in SEQS})
        comparison=dict(main_equal=_serial(main)==expected['main'],units_equal=_serial(units)==expected['units'])
        parity=dict(status='PASS' if all(comparison.values()) else 'FAIL',checks=comparison,
             coverage='All saved main aggregate, per-sequence summaries and12 gate units; no core671 claim',
             new_ranges_not_compared_to_legacy_numbers=True)
        report=dict(schema='release85_score_result_v1',status='TECHNICAL_REPRODUCTION_NOT_INDEPENDENT_QC',
             main=main,parity=parity,population='whole_sequence_724_not_core_671',
             identity_pool='actual post-M4 output boxes; raw index determines frozen tie ordering',
             unknown_precision_policy='Unknown, ambiguous, mixed and ignore outputs remain in ALL-final denominator',
             secondary_core_671='NOT_COMPUTED_IN_V0',human_QC='not_reviewed',
             range_semantics='All globally max-cardinality/minimum-exact-time matchings, independently per sequence/gate; not confidence intervals',
             anonymous_range_policy='All final events satisfy frozen legal time/direction/position gates; no ignore/neutral deletion. This is not T3 clean anonymous scoring.',
             matching_ranges=dict(aggregate=_aggregate_ranges(range_units),
                 by_sequence={s:_aggregate_ranges([u for u in range_units if u['sequence']==s]) for s in SEQS}),
             numpy=np.__version__,cpu_s=time.process_time()-cpu,elapsed_s=time.monotonic()-started,
             no_inference=True,no_tracking=True,no_test_data=True,seed=None)
        _write(out/'units.json',dict(main=units));_write(out/'matching_ranges.json',range_units)
        _write(out/'scores.json',report);_write(out/'read_ledger.json',reads)
        if not all(comparison.values()):raise AssertionError('Saved whole-sequence parity failed; preserve outputs; do not change science')
        budget();_write(out/'complete.json',dict(status='PASS_TECHNICAL_PARITY',parity=parity,
             no_independent_Claude_recompute_claim=True,human_QC='not_reviewed',cpu_s=time.process_time()-cpu,elapsed_s=time.monotonic()-started))
        return _serial(report)
    except BaseException as exc:
        _write(out/'FAIL.json',dict(status='FAIL_PRESERVED',error=repr(exc),reads=reads,
             cpu_s=time.process_time()-cpu,elapsed_s=time.monotonic()-started))
        raise
