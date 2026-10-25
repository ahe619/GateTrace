"""Generate complete bound commands, or collect explicit completed-unit receipts.

Generation reads only its explicit control manifest and local production code.
Collection requires the same separately approved controls as production stages.
Neither mode invokes a detector, tracker, event extractor, or scorer.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from production_v1.manifest import (ROOT, Ctx, Request, SYSTEMS, HANDOFF_SCHEMA,
    binding_for, canonical, guarded_path, json_bytes, require, sha_bytes,
    validate_manifest, valid_sha, utc)


def quote_ps(value):
    return "'" + str(value).replace("'", "''") + "'"


def local_worker_status():
    result = {}
    for filename, functions in (('workers.py', ('export_yolox', 'consume')),
                                ('reference_score.py', ('import_reference', 'seal', 'score'))):
        p = Path(__file__).with_name(filename)
        present = set()
        ref = None
        if p.is_file():
            raw = p.read_bytes()
            tree = ast.parse(raw.decode('utf-8-sig'), filename=str(p))
            present = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            ref = dict(path=str(p.resolve()), bytes=len(raw), sha256=sha_bytes(raw))
        result[filename] = dict(binding=ref, functions={f: f in present for f in functions})
    return result


def generate(manifest_path, expected_sha, approval_path, approval_sha, out):
    require(valid_sha(expected_sha) and valid_sha(approval_sha), 'Full manifest/approval hashes required')
    p = guarded_path(manifest_path, control=True)
    raw = p.read_bytes()
    require(sha_bytes(raw) == expected_sha, 'Manifest hash mismatch')
    manifest = validate_manifest(json_bytes(raw))
    # Approval is only rendered as a future explicit input here, never opened.
    approval_path = guarded_path(approval_path, control=True)
    out = guarded_path(out)
    require(out.is_relative_to(ROOT / 'data/r15/confirmation85'), 'Command artifacts must stay in project confirmation85')
    out.mkdir(parents=True, exist_ok=False)
    run_root = guarded_path(manifest['run_root'], scope=manifest['scope'])
    entry = Path(__file__).with_name('run.py').resolve()
    code_status = local_worker_status()
    all_exist = all(all(row['functions'].values()) for row in code_status.values())
    common = ['--manifest', str(p), '--manifest-sha256', expected_sha,
              '--freeze-sha256', manifest['freeze']['sha256'], '--approval', str(approval_path),
              '--approval-sha256', approval_sha]
    py_det, py_cpu = [manifest['interpreters'][k]['path'] for k in ('detector', 'cpu')]
    steps, script = [], [
        '# Generated contract; external execution authorization remains mandatory.',
        '# No scientific stage is launched by command generation.',
        "$ErrorActionPreference = 'Stop'",
        'function Invoke-Checked { param([string]$Python, [object[]]$Argv)',
        '  & $Python @Argv',
        "  if ($LASTEXITCODE -ne 0) { throw ('Stage stopped with exit code ' + $LASTEXITCODE) }",
        '}',
    ]

    def emit(step_id, python, arguments, dependencies=(), runtime=None, control=False):
        tokens = []
        for token in arguments:
            if isinstance(token, dict):
                tokens.append(token['powershell_variable'])
            else:
                tokens.append(quote_ps(token))
        script.append('Invoke-Checked -Python ' + quote_ps(python) + ' -Argv @(' + ', '.join(tokens) + ')')
        item = dict(step_id=step_id, interpreter=python, argv=arguments,
                    depends_on=list(dependencies), runtime_hash_sources=runtime or {},
                    control_step=control)
        if not control:
            steps.append(item)
        return item

    for seq in manifest['sequences']:
        dest = run_root / 'export_yolox' / seq
        export = seq + ':export_yolox'
        emit(export, py_det, ['-B', str(entry), '--stage', 'export_yolox', '--sequence', seq,
                             *common, '--out', str(dest)])
        variable = '$handoffSha' + seq[-2:]
        handoff = dest / 'handoff.json'
        script.append(variable + ' = (Get-FileHash -Algorithm SHA256 -LiteralPath ' + quote_ps(handoff) + ').Hash.ToLowerInvariant()')
        for system in SYSTEMS:
            stage = 'import_reference' if system in ('p2', 'o1') else 'consume'
            args = ['-B', str(entry), '--stage', stage, '--system', system, '--sequence', seq, *common]
            deps, hashes = (), {}
            if system in ('yolox_v11', 'byte', 'oc', 'bot'):
                args += ['--handoff', str(handoff), '--handoff-sha256',
                         {'powershell_variable': variable, 'source': str(handoff), 'algorithm': 'SHA256'}]
                deps, hashes = (export,), {'handoff': str(handoff)}
            args += ['--out', str(run_root / 'systems' / system / seq)]
            emit(seq + ':' + system, py_cpu, args, deps, hashes)
    index_path = run_root / '_handoff' / 'all_units.json'
    index_cmd = emit('collect_receipts', py_cpu, ['-B', str(Path(__file__).resolve()), 'collect-receipts',
        *common, '--index-out', str(index_path)], control=True)
    script.append('$indexSha = (Get-FileHash -Algorithm SHA256 -LiteralPath ' + quote_ps(index_path) + ').Hash.ToLowerInvariant()')
    emit('seal_all', py_cpu, ['-B', str(entry), '--stage', 'seal', *common,
        '--run-root', str(run_root), '--handoff', str(index_path), '--handoff-sha256',
        {'powershell_variable': '$indexSha', 'source': str(index_path), 'algorithm': 'SHA256'},
        '--out', str(run_root / 'seal')], [s['step_id'] for s in steps if ':export_' not in s['step_id']],
        {'unit_index': str(index_path)})
    seal_path = run_root / 'seal' / 'complete.json'
    script.append('$sealSha = (Get-FileHash -Algorithm SHA256 -LiteralPath ' + quote_ps(seal_path) + ').Hash.ToLowerInvariant()')
    emit('score_all', py_cpu, ['-B', str(entry), '--stage', 'score', *common,
        '--run-root', str(run_root), '--seal', str(seal_path), '--seal-sha256',
        {'powershell_variable': '$sealSha', 'source': str(seal_path), 'algorithm': 'SHA256'},
        '--out', str(run_root / 'score')], ['seal_all'], {'seal': str(seal_path)})
    require(len(steps) == 18, 'Expected exactly 18 production stages')
    plan = dict(schema='r15_confirmation85_executable_command_contract_v1',
        status='WORKERS_PRESENT_NOT_REAL_RUN_VALIDATED' if all_exist else 'WORKER_IMPLEMENTATION_MISSING',
        production_authorization_verified=False, referenced_asset_paths_opened=False,
        stages_executed=False, scientific_stages=steps, control_steps=[index_cmd],
        worker_code_status=code_status, manifest=dict(path=str(p), bytes=len(raw), sha256=expected_sha),
        approval_path_rendered_not_read=str(approval_path), approval_sha256_rendered=approval_sha,
        notes=['Commands invoke real entrypoint; worker completeness is checked statically only.',
               'Runtime hashes are calculated from explicit completed paths, not placeholders.',
               'No unknown partial run is automatically resumed or rerun.',
               'P2/O1 import_existing is explicit; no rebuild fallback.'])
    with (out / 'commands.json').open('xb') as f:
        f.write(json.dumps(plan, ensure_ascii=False, indent=2, allow_nan=False).encode('utf-8') + b'\n')
    with (out / 'commands.ps1').open('xb') as f:
        f.write(('\n'.join(script) + '\n').encode('utf-8'))
    return plan


def collect_receipts(args):
    # Ctx validates controls/code/interpreter without claiming or reading data.
    raw = guarded_path(args.manifest, control=True).read_bytes()
    require(sha_bytes(raw) == args.manifest_sha256, 'Manifest hash differs')
    doc = validate_manifest(json_bytes(raw))
    run_root = guarded_path(doc['run_root'], scope=doc['scope'])
    index_path = guarded_path(args.index_out, scope=doc['scope'])
    require(index_path == run_root / '_handoff/all_units.json', 'Runtime index path differs from fixed contract')
    require(not index_path.exists(), 'Receipt index exists; never overwrite')
    request = Request('seal', handoff=str(index_path), handoff_sha256='0'*64, run_root=str(run_root))
    ctx = Ctx(manifest_path=args.manifest, manifest_sha256=args.manifest_sha256,
        freeze_sha256=args.freeze_sha256, approval_path=args.approval,
        approval_sha256=args.approval_sha256, request=request, out=run_root / 'seal')
    # Hash-check this additional control program, which Ctx does not execute itself.
    ctx.read_bytes(__file__, purpose='Receipt collector code binding')
    units, files, reads = [], [], list(ctx.control_reads)
    for seq in doc['sequences']:
        for system in SYSTEMS:
            ctx.budget.check('collect completion')
            p = guarded_path(run_root / 'systems' / system / seq / 'complete.json', scope=doc['scope'])
            payload = p.read_bytes()
            value = json_bytes(payload)
            require(value.get('complete') is True and value.get('manifest_sha256') == args.manifest_sha256
                    and value.get('freeze_sha256') == args.freeze_sha256
                    and value.get('approval_sha256') == args.approval_sha256, 'Completion not bound to approved run')
            expected_stage = 'import_reference' if system in ('p2', 'o1') else 'consume'
            require(value.get('stage') == expected_stage and value.get('sequence') == seq and value.get('system') == system,
                    'Completion unit identity differs')
            ref = dict(path=str(p), bytes=len(payload), sha256=sha_bytes(payload))
            units.append(dict(sequence=seq, system=system, binding=ref))
            files.append(dict(id=seq+'.'+system+'.complete', role='unit_complete',
                              sequence=seq, system=system, binding=ref))
            reads.append(dict(binding=ref, purpose='Explicit completed unit receipt', utc=utc()))
    require(len(units) == 14, 'Incomplete receipt population')
    result = ctx.header(dict(schema=HANDOFF_SCHEMA, complete=True, stage='collect_receipts',
                            sequence=None, system=None, units=units, files=files,
                            collector_code=binding_for(__file__), read_ledger=reads))
    ctx.budget.check('write receipt index')
    ctx.budget.output_check()
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open('xb') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False).encode('utf-8') + b'\n')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('generate')
    p.add_argument('--manifest', required=True, type=Path)
    p.add_argument('--manifest-sha256', required=True)
    p.add_argument('--approval', required=True, type=Path)
    p.add_argument('--approval-sha256', required=True)
    p.add_argument('--out', required=True, type=Path)
    p = sub.add_parser('collect-receipts')
    for flag in ('manifest', 'manifest-sha256', 'freeze-sha256', 'approval', 'approval-sha256', 'index-out'):
        p.add_argument('--'+flag, required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == 'generate':
            result = generate(args.manifest, args.manifest_sha256, args.approval, args.approval_sha256, args.out)
        else:
            result = collect_receipts(args)
        print(result.get('status', 'RECEIPT_INDEX_COMPLETE'))
        return 0
    except Exception as exc:
        print('STOP '+type(exc).__name__+': '+str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
