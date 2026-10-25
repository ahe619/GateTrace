"""One-command synthetic engineering checks; no dataset, model or human answers.

Use: python -B check_inspector.py --out /new/directory
This verifies package integrity before loading the synthetic tests. Passing is
not a scientific reproduction or independent annotation/Claude verification.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
import unittest

sys.dont_write_bytecode = True
from reproduce import save, verify_package


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, help='New directory outside the package')
    parser.add_argument('--stdlib-only',action='store_true',
                        help='Run with -S; omit Pillow rendering tests and forbid third-party imports')
    args = parser.parse_args(argv)
    if args.stdlib_only and not sys.flags.no_site:
        raise ValueError('Use python -S -B check_inspector.py --stdlib-only ...')
    root = Path(__file__).resolve().parent
    out = Path(args.out).resolve()
    if out.exists() or out.is_relative_to(root) or root.is_relative_to(out):
        raise ValueError('Use a new output directory outside the package')
    _, digest = verify_package(root)
    out.mkdir(parents=True, exist_ok=False)
    wall, cpu = time.monotonic(), time.process_time()
    save(out/'started.json', dict(package_manifest_sha256=digest, python=sys.version,
        synthetic_only=True, no_dataset=True, no_gpu=True, no_scientific_scoring=True))
    log = io.StringIO()
    scratch = out/'scratch'
    scratch.mkdir(exist_ok=False)
    previous_scratch = os.environ.get('INSPECTOR_TEST_SCRATCH')
    os.environ['INSPECTOR_TEST_SCRATCH'] = str(scratch)
    try:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            suite = unittest.TestSuite()
            for test_file in sorted((root/'tests').glob('test_*.py')):
                if args.stdlib_only and test_file.name=='test_rendering_round2.py':
                    continue
                suite.addTests(unittest.defaultTestLoader.discover(str(root/'tests'),pattern=test_file.name))
            result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    finally:
        if previous_scratch is None:
            os.environ.pop('INSPECTOR_TEST_SCRATCH',None)
        else:
            os.environ['INSPECTOR_TEST_SCRATCH'] = previous_scratch
    raw = log.getvalue().encode('utf-8')
    with (out/'tests.log').open('xb') as sink:
        sink.write(raw)
    forbidden = sorted(n for n in sys.modules if n.split('.')[0] in ('numpy','PIL','cv2','torch')) if args.stdlib_only else []
    passed = result.wasSuccessful() and not forbidden
    report = dict(status='PASS_SYNTHETIC_ENGINEERING_ONLY' if passed else 'FAIL',
        package_manifest_sha256=digest, tests_run=result.testsRun,
        failures=len(result.failures), errors=len(result.errors),
        skipped=[dict(test=str(test),reason=reason) for test,reason in result.skipped],
        elapsed_s=time.monotonic()-wall,cpu_s=time.process_time()-cpu,
        log_sha256=hashlib.sha256(raw).hexdigest(),no_dataset=True,no_gpu=True,
        independent_scientific_recompute=False,
        mode='stdlib_only' if args.stdlib_only else 'including_synthetic_rendering',
        rendering_tested=not args.stdlib_only,forbidden_imports=forbidden)
    save(out/'receipt.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
