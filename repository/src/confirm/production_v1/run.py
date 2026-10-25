"""Run one explicitly authorized, frozen production stage.

No defaults discover data; missing approval/hash/resources/worker fails closed.
This CLI being implemented does not authorize confirmation-set execution.
"""
from __future__ import annotations

import argparse
import importlib
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from production_v1.manifest import Ctx, Request, STAGES, SYSTEMS, ContractError, require

WORKERS = {
    'export_yolox': ('workers', 'export_yolox'),
    'consume': ('workers', 'consume'),
    'import_reference': ('reference_score', 'import_reference'),
    'seal': ('reference_score', 'seal'),
    'score': ('reference_score', 'score'),
}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage', required=True, choices=STAGES)
    p.add_argument('--sequence')
    p.add_argument('--system', choices=SYSTEMS)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--manifest-sha256', required=True)
    p.add_argument('--freeze-sha256', required=True)
    p.add_argument('--approval', type=Path, required=True)
    p.add_argument('--approval-sha256', required=True)
    p.add_argument('--handoff', type=Path)
    p.add_argument('--handoff-sha256')
    p.add_argument('--seal', type=Path)
    p.add_argument('--seal-sha256')
    p.add_argument('--run-root', type=Path)
    p.add_argument('--out', type=Path, required=True)
    return p


def load_worker(ctx):
    module_name, function_name = WORKERS[ctx.request.stage]
    path = Path(__file__).with_name(module_name + '.py').resolve()
    require(path.is_file(), 'Production worker does not exist: ' + str(path))
    # Must be an actual bound source in the final freeze, not an invented argv.
    ctx.read_bytes(path, purpose='Hash-check production worker before import')
    # Bind the complete local production-source closure, including later helpers.
    # This enumeration inspects only this new code directory, never dataset roots.
    frozen = {Path(r['path']).resolve() if Path(r['path']).is_absolute()
              else (ctx.ROOT / r['path']).resolve() for r in ctx.freeze['code']}
    for sibling in sorted(path.parent.glob('*.py')):
        if sibling.name.startswith(('synthetic_', 'test_')) or sibling.name.endswith('_test.py'):
            continue
        require(sibling.resolve() in frozen, 'Production helper missing from final freeze: ' + sibling.name)
        ctx.read_bytes(sibling, purpose='Verify production source closure before worker import')
    module = importlib.import_module('production_v1.' + module_name)
    require(Path(module.__file__).resolve() == path, 'Imported worker path differs')
    function = getattr(module, function_name, None)
    require(callable(function), 'Production worker function missing: ' + function_name)
    return function


def main(argv=None):
    args = parser().parse_args(argv)
    request = Request(stage=args.stage, sequence=args.sequence, system=args.system,
        handoff=str(args.handoff) if args.handoff else None,
        handoff_sha256=args.handoff_sha256, seal=str(args.seal) if args.seal else None,
        seal_sha256=args.seal_sha256, run_root=str(args.run_root) if args.run_root else None)
    ctx = None
    try:
        ctx = Ctx(manifest_path=args.manifest, manifest_sha256=args.manifest_sha256,
            freeze_sha256=args.freeze_sha256, approval_path=args.approval,
            approval_sha256=args.approval_sha256, request=request, out=args.out)
        worker = load_worker(ctx)
        ctx.claim()
        result = worker(ctx, request)
        complete = ctx.complete(result)
        print('TECHNICAL_STAGE_COMPLETE ' + complete['sha256'])
        return 0
    except Exception as exc:
        if ctx is not None:
            ctx.fail(exc)
        print('STOP ' + type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        return 2
    finally:
        if ctx is not None:
            ctx.release_slot()


if __name__ == '__main__':
    raise SystemExit(main())
