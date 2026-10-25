"""Inspect derived GT support and an existing tracker's event-level evidence, offline.

No detection/tracking/learning; --tracks invokes the existing frozen CPU scorer.
Use --event-id ID or --list-misses [--bin low|mid_low|mid_high|high|all].
"""
import sys
sys.dont_write_bytecode = True
import argparse
import json
from pathlib import Path
import time
import traceback

from reproduce import verify_package, input_paths, verify_rebuilt_labels, save
from score_tracker import track_paths
from src.inspection import Inspector, render_event
from src.evidence_seal import seal_score_evidence


def preserve_failure(out, exc, reads, started, cpu_started):
    """Best effort only: logging failures must never replace the primary error."""
    payloads = [
        ('read_ledger.json' if not (out/'read_ledger.json').exists() else 'failure_read_ledger.json', reads),
        ('FAILED.json', dict(error=repr(exc), traceback=traceback.format_exc(),
            reads=reads, cpu_s=time.process_time()-cpu_started,
            elapsed_s=time.monotonic()-started))]
    errors = []
    for name, payload in payloads:
        try:
            save(out/name, payload)
        except BaseException as logging_error:
            errors.append(dict(file=name, error=repr(logging_error)))
    if errors:
        message = 'Could not preserve all failure evidence: ' + repr(errors)
        if hasattr(exc, 'add_note'):
            exc.add_note(message)
        try:
            print(message, file=sys.stderr)
        except BaseException:
            pass
    return errors


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gt-root',required=True);p.add_argument('--seqinfo-root')
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--event-id');mode.add_argument('--list-misses',action='store_true')
    p.add_argument('--bin',choices=['all','low','mid_low','mid_high','high'],default='all')
    p.add_argument('--tracks');p.add_argument('--out',required=True)
    p.add_argument('--images',help='Optional exact local MOT20-01/img1 or MOT20-02/img1 directory')
    p.add_argument('--render-out',help='New directory for PNGs outside the package')
    a=p.parse_args(argv)
    if sys.flags.optimize:raise ValueError('Run without -O')
    if a.list_misses and not a.tracks:raise ValueError('--list-misses needs --tracks')
    if bool(a.images)!=bool(a.render_out) or (a.images and not a.event_id):
        raise ValueError('Rendering needs --event-id, --images and --render-out together')
    package=Path(__file__).resolve().parent;out=Path(a.out).resolve()
    if out.exists() or out.is_relative_to(package) or package.is_relative_to(out):
        raise ValueError('Use a new output directory outside package')
    _,digest=verify_package(package)
    gt=input_paths(a.gt_root,'gt');seq=input_paths(a.seqinfo_root or a.gt_root,'seqinfo')
    tracks=None if not a.tracks else track_paths(a.tracks)
    out.mkdir(parents=True,exist_ok=False);start=time.monotonic();cpu=time.process_time()
    save(out/'started.json',dict(command=sys.orig_argv,package_manifest_sha256=digest,no_inference=True))
    reads=[]
    try:
        from src.labels import build_labels
        from src.lineage import enrich_labels
        build_labels(gt,seq,out/'labels')
        enrich_labels(out/'labels',out/'labels/lineage_enrichment.jsonl.gz')
        verify_rebuilt_labels(package/'labels',out/'labels')
        score_dir=None
        seal=None
        if tracks:
            from src.tracker_score import score_tracks
            score_dir=out/'tracker'
            score_tracks(gt,out/'labels',tracks,score_dir,package,'tracker')
            seal=seal_score_evidence(score_dir,digest)
            save(out/'evidence_binding.json',seal)
        inspector=Inspector(package,gt,tracks,score_dir,read_ledger=reads,
            evidence_manifest_sha256=None if seal is None else seal['sha256'])
        if a.list_misses:
            rows=inspector.list_events(a.bin)
            with (out/'misses.jsonl').open('x',encoding='utf-8') as f:
                for row in rows:
                    line=json.dumps(row,ensure_ascii=False);f.write(line+'\n');print(line)
        else:
            detail=inspector.detail(a.event_id);save(out/'event.json',detail)
            if a.images:render_event(inspector,detail,a.images,a.render_out)
            print(json.dumps(dict(event_id=a.event_id,rule_confirmed=detail['confirmation_status'],
                found=None if detail['system_evidence'] is None else detail['system_evidence']['found'],
                evidence_file=str(out/'event.json')),ensure_ascii=False))
        save(out/'read_ledger.json',reads)
        save(out/'complete.json',dict(status='COMPLETE_PENDING_QC',cpu_s=time.process_time()-cpu,
            elapsed_s=time.monotonic()-start,human_qc='not_reviewed',
            evidence_binding=seal,frame_integrity=inspector.frame_integrity))
        return 0
    except BaseException as exc:
        preserve_failure(out,exc,reads,start,cpu)
        raise


if __name__=='__main__':
    raise SystemExit(main())
