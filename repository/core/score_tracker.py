"""Score a tracker's MOTChallenge output on the MOT20-01/02 crossing-event sample (v0.1).

python -B score_tracker.py --gt-root GT --seqinfo-root SEQINFO --tracks DIR --out NEW_DIR
python -B score_tracker.py --self-test --gt-root GT --seqinfo-root SEQINFO --out NEW_DIR

DIR must contain MOT20-01.txt and MOT20-02.txt (frame,id,x,y,w,h,conf,-1,-1,-1;
1-based frame and pixel coordinates). Events are derived by the frozen event
chain from output-box bottom-centres; identities are rebuilt from the same boxes.
No detector, tracker, model, network client or project-root import is used.
See README.md for the interface and its limits.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse
import json
import os
from pathlib import Path
import shutil
import threading
import time
import traceback

from reproduce import verify_package, input_paths, verify_rebuilt_labels, save

SEQUENCES = ('MOT20-01', 'MOT20-02')
PANEL = ('byte', 'oc', 'bot')
LIMIT_BYTES = 2 * 1024 ** 3
BANNED = ('mot20-03', 'mot20-05', 'ht21', 'e18', 'sealed', 'e25_timeline', 'review/labels')


def track_paths(root):
    """Exactly DIR/MOT20-01.txt and DIR/MOT20-02.txt; no search, no redirection."""
    root = Path(root).resolve()
    if any(x in root.as_posix().lower() for x in BANNED):
        raise ValueError('Track root is outside the development sample scope')
    paths = {}
    for seq in SEQUENCES:
        p = (root / (seq + '.txt')).resolve()
        if not p.is_relative_to(root) or p.relative_to(root) != Path(seq + '.txt') or not p.is_file():
            raise ValueError(f'Missing or escaping track file {seq}.txt in {root}')
        paths[seq] = p
    return paths


def check_budget(out, started, limit_s):
    if time.monotonic() - started > limit_s:
        raise TimeoutError(f'{limit_s} second limit exceeded')
    if shutil.disk_usage(out).free < 20 * 1024 ** 3:
        raise RuntimeError('Less than 20 GiB free disk space')
    if sum(p.stat().st_size for p in Path(out).rglob('*') if p.is_file()) > LIMIT_BYTES:
        raise RuntimeError('2 GiB output limit exceeded')


def table(report):
    agg = report['main']['aggregate']
    rows = ['bin        matched/confirmed_GT']
    for b in ('low', 'mid_low', 'mid_high', 'high'):
        rows.append(f"{b:<10} {agg['bins'][b]['numerator']}/{agg['bins'][b]['denominator']}")
    rows.append(f"all        {agg['correct']}/{agg['GT']}")
    rows.append(f"precision  {agg['correct']}/{agg['final_events']} (identity-correct / all final events)")
    return '\n'.join(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--gt-root', required=True, help='train directory containing MOT20-01/gt/gt.txt and MOT20-02/gt/gt.txt')
    parser.add_argument('--seqinfo-root', help='train directory containing both seqinfo.ini files; defaults to --gt-root')
    parser.add_argument('--tracks', help='directory containing MOT20-01.txt and MOT20-02.txt in MOTChallenge result format')
    parser.add_argument('--name', default='tracker', help='label for the scored tracker (output subdirectory name)')
    parser.add_argument('--self-test', action='store_true',
                        help='score the three bundled panel examples and compare with expected/panel_*.json')
    parser.add_argument('--out', required=True, help='New output directory; existing paths are rejected')
    args = parser.parse_args(argv)
    if sys.flags.optimize:
        raise SystemExit('Run without -O: the frozen functions rely on assert statements')
    if args.self_test == (args.tracks is not None):
        raise SystemExit('Give exactly one of --tracks DIR or --self-test')
    if not args.name.isidentifier() or args.name in ('labels',):
        raise SystemExit('--name must be a simple identifier other than "labels"')
    package = Path(__file__).resolve().parent
    out = Path(args.out).resolve()
    if out.exists() or out.is_relative_to(package) or package.is_relative_to(out):
        raise ValueError('Use a new output directory outside the package')
    manifest, manifest_sha = verify_package(package)
    gt_files = input_paths(args.gt_root, 'gt')
    seqinfo_files = input_paths(args.seqinfo_root or args.gt_root, 'seqinfo')
    if args.self_test:
        jobs = [(m, track_paths(package / 'examples' / 'panel' / m), package / 'expected' / f'panel_{m}.json') for m in PANEL]
    else:
        jobs = [(args.name, track_paths(args.tracks), None)]
    limit_s = 900 + 900 * len(jobs)
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    save(out / 'started.json', {
        'schema': 'mot20_crossing_events_tracker_run_v0_1', 'command': sys.orig_argv,
        'executable': sys.executable, 'python': sys.version, 'package_manifest_sha256': manifest_sha,
        'package_version': manifest.get('package_version'), 'sequences': list(SEQUENCES),
        'mode': 'self_test' if args.self_test else 'score', 'trackers': [j[0] for j in jobs],
        'max_seconds': limit_s, 'max_new_bytes': LIMIT_BYTES, 'no_inference': True,
        'human_qc': 'not_reviewed', 'independent_reproduction': False,
    })

    def timeout():
        try:
            save(out / 'timeout.json', {'status': 'FAILED_TIMEOUT', 'limit_s': limit_s})
        finally:
            os._exit(124)

    timer = threading.Timer(limit_s, timeout)
    timer.daemon = True
    timer.start()
    try:
        check_budget(out, started, limit_s)
        sys.path.insert(0, str(package))
        from src.labels import build_labels
        from src.lineage import enrich_labels
        from src.tracker_score import score_tracks
        from src.regression import compare
        import numpy
        if numpy.__version__ != '2.2.6':
            raise ValueError('Reference package requires NumPy 2.2.6; no automatic installation')
        label_summary = build_labels(gt_files, seqinfo_files, out / 'labels')
        enrich_labels(out / 'labels', out / 'labels' / 'lineage_enrichment.jsonl.gz')
        label_parity = verify_rebuilt_labels(package / 'labels', out / 'labels')
        save(out / 'label_parity.json', label_parity)
        results = {}
        for name, track_files, expected_path in jobs:
            check_budget(out, started, limit_s)
            report, units, events = score_tracks(gt_files, out / 'labels', track_files, out / name, package, name)
            entry = dict(summary_table=report['summary_table'], cpu_s=report['cpu_s'], elapsed_s=report['elapsed_s'])
            if expected_path is not None:
                expected = json.loads(expected_path.read_text(encoding='utf-8'))
                if expected.get('schema') != 'panel_regression_expected_v0_1' or expected.get('tracker') != name:
                    raise ValueError('Unexpected regression expectation file: ' + expected_path.name)
                regression = compare(expected, report, units, events)
                save(out / name / 'regression.json', regression)
                entry['regression'] = {k: regression[k] for k in ('status', 'checks', 'observed_primary',
                                                                  'crossing_position_max_abs_diff_px',
                                                                  'final_events_compared', 'mismatch_count')}
            results[name] = entry
            print(f'== {name}\n' + table(report) + (f"\nregression: {entry['regression']['status']}" if expected_path else ''),
                  flush=True)
        check_budget(out, started, limit_s)
        status = 'COMPLETE'
        if args.self_test:
            status = 'SELF_TEST_PASS' if all(r['regression']['status'] == 'PASS' for r in results.values()) else 'SELF_TEST_FAIL'
        save(out / 'complete.json', {
            'status': status, 'package_manifest_sha256': manifest_sha,
            'elapsed_s': time.monotonic() - started, 'labels': label_summary['confirmed'],
            'label_parity': label_parity['status'], 'results': results,
            'no_inference': True, 'no_training': True, 'human_qc': 'not_reviewed',
        })
        print(json.dumps({'status': status, 'output': str(out), 'elapsed_s': round(time.monotonic() - started, 3)},
                         ensure_ascii=False))
        return 0 if status in ('COMPLETE', 'SELF_TEST_PASS') else 1
    except BaseException as exc:
        save(out / 'FAILED.json', {'type': type(exc).__name__, 'message': str(exc),
                                 'traceback': traceback.format_exc(), 'elapsed_s': time.monotonic() - started})
        raise
    finally:
        timer.cancel()


if __name__ == '__main__':
    raise SystemExit(main())
