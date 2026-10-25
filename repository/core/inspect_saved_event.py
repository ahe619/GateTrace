"""Inspect already scored and externally hash-bound evidence without rescoring.

Pass the SHA256 retained separately in the fresh inspector's evidence_binding.json
as --evidence-sha256. This command will not create or trust a new evidence seal.
It writes only inspection output, not a new score, labels, tracks or detections.
"""
import sys
sys.dont_write_bytecode = True

import argparse
import json
from pathlib import Path
import time

from reproduce import verify_package, input_paths, save
from score_tracker import track_paths
from inspect_event import preserve_failure
from src.inspection import Inspector, render_event


def _sha256(value):
    if len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise argparse.ArgumentTypeError('Provide the retained lowercase 64-character evidence SHA256')
    return value


def _separate_output(path, package, score_dir):
    resolved = Path(path).resolve()
    if resolved.exists():
        raise ValueError('Use a new inspection output directory')
    for protected in (package, score_dir):
        if resolved.is_relative_to(protected) or protected.is_relative_to(resolved):
            raise ValueError('Inspection output must be separate from package and original scoring evidence')
    return resolved


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gt-root', required=True)
    parser.add_argument('--tracks', required=True)
    parser.add_argument('--score-dir', required=True)
    parser.add_argument('--evidence-sha256', required=True, type=_sha256)
    parser.add_argument('--out', required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--event-id')
    mode.add_argument('--list-misses', action='store_true')
    parser.add_argument('--bin', choices=['all', 'low', 'mid_low', 'mid_high', 'high'], default='all')
    parser.add_argument('--images', help='Optional exact local MOT20-01/img1 or MOT20-02/img1 directory')
    parser.add_argument('--render-out', help='New render directory outside the package and saved score')
    args = parser.parse_args(argv)
    if sys.flags.optimize:
        raise ValueError('Run without -O')
    if bool(args.images) != bool(args.render_out) or (args.images and not args.event_id):
        raise ValueError('Rendering needs --event-id, --images and --render-out together')
    package = Path(__file__).resolve().parent
    score_dir = Path(args.score_dir).resolve(strict=True)
    if not score_dir.is_dir():
        raise ValueError('--score-dir must be the existing frozen scoring directory')
    out = _separate_output(args.out, package, score_dir)
    render_out = None
    if args.render_out:
        render_out = _separate_output(args.render_out, package, score_dir)
        if render_out == out or out.is_relative_to(render_out):
            raise ValueError('Render output must not equal or contain the inspection output directory')
    _, package_digest = verify_package(package)
    gt = input_paths(args.gt_root, 'gt')
    tracks = track_paths(args.tracks)
    out.mkdir(parents=True, exist_ok=False)
    start, cpu_start = time.monotonic(), time.process_time()
    reads = []
    try:
        save(out / 'started.json', dict(status='INSPECTION_STARTED', command=sys.orig_argv,
             package_manifest_sha256=package_digest,
             source_score_evidence_sha256=args.evidence_sha256,
             source_score_directory=str(score_dir), no_rescoring=True, no_inference=True))
        inspector = Inspector(package, gt, tracks, score_dir, read_ledger=reads,
                              evidence_manifest_sha256=args.evidence_sha256)
        if args.list_misses:
            rows = inspector.list_events(args.bin)
            count = 0
            with (out / 'misses.jsonl').open('x', encoding='utf-8') as sink:
                for row in rows:
                    line = json.dumps(row, ensure_ascii=False, allow_nan=False)
                    sink.write(line + '\n')
                    print(line)
                    count += 1
            selection = dict(mode='list_misses', bin=args.bin, inspected_event_count=count)
        else:
            detail = inspector.detail(args.event_id)
            save(out / 'event.json', detail)
            if args.images:
                render_event(inspector, detail, args.images, render_out)
            selection = dict(mode='event', event_id=args.event_id)
            print(json.dumps(dict(event_id=args.event_id,
                 rule_confirmed=detail['confirmation_status'],
                 found=None if detail['system_evidence'] is None else detail['system_evidence']['found'],
                 evidence_file=str(out / 'event.json'), no_rescoring=True), ensure_ascii=False))
        save(out / 'read_ledger.json', reads)
        save(out / 'inspection_receipt.json', dict(status='INSPECTION_COMPLETE_PENDING_QC',
             no_rescoring=True, no_inference=True, scientific_result_created=False,
             source_score_evidence_sha256=args.evidence_sha256,
             source_score_directory=str(score_dir), package_manifest_sha256=package_digest,
             frame_integrity=inspector.frame_integrity, selection=selection,
             human_qc='not_reviewed', cpu_s=time.process_time() - cpu_start,
             elapsed_s=time.monotonic() - start))
        return 0
    except BaseException as exc:
        preserve_failure(out, exc, reads, start, cpu_start)
        raise


if __name__ == '__main__':
    raise SystemExit(main())
