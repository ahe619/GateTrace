"""Offline development sample: public GT -> crossing labels -> cached-system score.

No detector, tracker, model, network client or project-root import is used.
See README.md for the supported scope and limitations.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import threading
import time
import traceback


SEQUENCES = ('MOT20-01', 'MOT20-02')
LIMIT_S = 900
LIMIT_BYTES = 2 * 1024 ** 3


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def safe_member(root, member):
    """Resolve a manifest member without absolute paths, traversal or symlink escape."""
    if not isinstance(member, str) or not member or '\\' in member or ':' in member:
        raise ValueError('Invalid package member')
    posix = PurePosixPath(member)
    if posix.is_absolute() or '..' in posix.parts or str(posix) != member:
        raise ValueError('Noncanonical or escaping package member')
    root = Path(root).resolve()
    target = root.joinpath(*posix.parts).resolve()
    if not target.is_relative_to(root) or target == root:
        raise ValueError('Package member escapes root')
    return target


def verify_package(root):
    root = Path(root).resolve()
    manifest_path = root / 'MANIFEST.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('schema') != 'mot20_crossing_events_sample_manifest_v0':
        raise ValueError('Unknown package manifest schema')
    if manifest.get('sequences') != list(SEQUENCES):
        raise ValueError('Sample scope must be exactly MOT20-01/02')
    seen = set()
    for entry in manifest['files']:
        member = entry['path']
        if member in seen or member == 'MANIFEST.json':
            raise ValueError('Duplicate or recursive manifest member')
        seen.add(member)
        p = safe_member(root, member)
        if not p.is_file() or p.stat().st_size != entry['bytes']:
            raise ValueError(f'Missing or size-mismatched member: {member}')
        if digest(p) != entry['sha256']:
            raise ValueError(f'SHA256 mismatch: {member}')
    required = {'reproduce.py', 'src/labels.py', 'src/score.py'}
    if not required.issubset(seen):
        raise ValueError('Executable members missing from integrity manifest')
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual != seen | {'MANIFEST.json'}:
        raise ValueError('Unexpected/unregistered package files: ' + repr(sorted(actual - seen - {'MANIFEST.json'})))
    return manifest, digest(manifest_path)


def save(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        f.write('\n')


def verify_rebuilt_labels(reference, generated):
    """Compare label data, not gzip headers or measured runtime."""
    checked = []
    for name in ('transitions.jsonl.gz', 'geometry.json', 'height_models.json', 'lineage_enrichment.jsonl.gz'):
        a, b = Path(reference) / name, Path(generated) / name
        if name.endswith('.gz'):
            with gzip.open(a, 'rt', encoding='utf-8') as f:
                expected = [json.loads(line) for line in f]
            with gzip.open(b, 'rt', encoding='utf-8') as f:
                actual = [json.loads(line) for line in f]
        else:
            expected = json.loads(a.read_text(encoding='utf-8'))
            actual = json.loads(b.read_text(encoding='utf-8'))
        if actual != expected:
            raise ValueError('Reconstructed scientific label content differs: ' + name)
        checked.append({'file': name, 'status': 'EXACT_CONTENT_EQUAL',
                        'reference_sha256': digest(a), 'generated_sha256': digest(b)})
    return {'status': 'PASS', 'comparisons': checked, 'float_rounding': False}


def check_budget(out, started):
    if time.monotonic() - started > LIMIT_S:
        raise TimeoutError('900 second sample limit exceeded')
    if shutil.disk_usage(out).free < 20 * 1024 ** 3:
        raise RuntimeError('Less than 20 GiB free disk space')
    if sum(p.stat().st_size for p in Path(out).rglob('*') if p.is_file()) > LIMIT_BYTES:
        raise RuntimeError('2 GiB output limit exceeded')


def input_paths(root, kind):
    root = Path(root).resolve()
    # This CLI is deliberately scoped to the development example, not a test runner.
    banned = ('mot20-03', 'mot20-05', 'ht21', 'e18', 'sealed', 'e25_timeline', 'review/labels')
    if any(x in root.as_posix().lower() for x in banned):
        raise ValueError('Source root is outside the development sample scope')
    paths = {}
    for seq in SEQUENCES:
        expected_relative = Path(seq) / ('gt/gt.txt' if kind == 'gt' else 'seqinfo.ini')
        p = (root / expected_relative).resolve()
        # Even an in-root symlink/junction may point to a different sequence.
        # Reject that redirection before opening or hashing its content.
        if (not p.is_relative_to(root) or p.relative_to(root) != expected_relative
                or not p.is_file()):
            raise ValueError(f'Missing or escaping {kind} asset for {seq}')
        paths[seq] = p
    return paths


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gt-root', required=True, help='train directory containing MOT20-01/gt/gt.txt and MOT20-02/gt/gt.txt')
    parser.add_argument('--seqinfo-root', help='train directory containing both seqinfo.ini files; defaults to --gt-root')
    parser.add_argument('--out', required=True, help='New output directory; existing paths are rejected')
    args = parser.parse_args(argv)
    package = Path(__file__).resolve().parent
    out = Path(args.out).resolve()
    if out.exists() or out.is_relative_to(package) or package.is_relative_to(out):
        raise ValueError('Use a new output directory outside the package')
    manifest, manifest_sha = verify_package(package)
    gt_files = input_paths(args.gt_root, 'gt')
    seqinfo_files = input_paths(args.seqinfo_root or args.gt_root, 'seqinfo')
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    save(out / 'started.json', {
        'schema': 'mot20_crossing_events_sample_run_v0', 'command': sys.orig_argv,
        'executable': sys.executable, 'prefix': sys.prefix, 'python': sys.version,
        'package_manifest_sha256': manifest_sha, 'sequences': list(SEQUENCES),
        'max_seconds': LIMIT_S, 'max_new_bytes': LIMIT_BYTES, 'no_inference': True,
        'human_qc': 'not_reviewed', 'independent_reproduction': False,
    })

    def timeout():
        try:
            save(out / 'timeout.json', {'status': 'FAILED_TIMEOUT', 'limit_s': LIMIT_S})
        finally:
            os._exit(124)

    timer = threading.Timer(LIMIT_S, timeout)
    timer.daemon = True
    timer.start()
    try:
        check_budget(out, started)
        # The verified package supplies all imported project-authored code.
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(package))
        from src.labels import build_labels
        from src.lineage import enrich_labels
        from src.score import score
        import numpy
        if numpy.__version__ != '2.2.6':
            raise ValueError('Reference package requires NumPy 2.2.6; no automatic installation')
        label_summary = build_labels(gt_files, seqinfo_files, out / 'labels')
        lineage_summary = enrich_labels(out / 'labels', out / 'labels' / 'lineage_enrichment.jsonl.gz')
        label_parity = verify_rebuilt_labels(package / 'labels', out / 'labels')
        save(out / 'label_parity.json', label_parity)
        check_budget(out, started)
        scoring_summary = score(gt_files, out / 'labels', package / 'examples' / 'yolox_v11', out / 'scores')
        check_budget(out, started)
        save(out / 'complete.json', {
            'status': 'COMPLETE_PENDING_INDEPENDENT_REPRODUCTION_AND_HUMAN_QC',
            'package_manifest_sha256': manifest_sha,
            'elapsed_s': time.monotonic() - started,
            'labels': label_summary, 'scoring': scoring_summary,
            'lineage': lineage_summary,
            'label_parity': label_parity,
            'no_inference': True, 'no_training': True,
        })
        print(json.dumps({'status': 'COMPLETE_PENDING_INDEPENDENT_REPRODUCTION_AND_HUMAN_QC',
                          'output': str(out), 'elapsed_s': round(time.monotonic() - started, 3)}, ensure_ascii=False))
        return 0
    except BaseException as exc:
        save(out / 'FAILED.json', {'type': type(exc).__name__, 'message': str(exc),
                                 'traceback': traceback.format_exc(), 'elapsed_s': time.monotonic() - started})
        raise
    finally:
        timer.cancel()


if __name__ == '__main__':
    raise SystemExit(main())
