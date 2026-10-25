"""Manifest-only import, complete-panel sealing and frozen E1-v2 scoring.

No import-time I/O, implicit glob, detector or tracker execution. The enclosing
manifest runner owns authorization, read allowlisting, deadlines and complete.json.
This is a new I/O wrapper, not evidence of a completed holdout regression.
"""
from __future__ import annotations

import ast
import collections
from collections.abc import Mapping
from fractions import Fraction
import gzip
import hashlib
from heapq import heappop, heappush
import io
import json
import math
from pathlib import Path
import re
from types import SimpleNamespace

SYSTEMS = ('yolox_v11', 'byte', 'oc', 'bot', 'p2', 'v11', 'o1')
PANELS = ('byte', 'oc', 'bot')
GATES = ('H_30', 'H_50', 'H_70', 'V_25', 'V_50', 'V_75')
BINS = ('low', 'mid_low', 'mid_high', 'high')
UNKNOWN = {'insufficient_observations', 'unidentified', 'ambiguous', 'mixed_unknown'}
SCIENCE = {
    'science_core': ('d6342df4fa8befca129d02124030e05205e6fb80a9e2f6c753a6782615aee11b',
                     ('valid_box', 'assign', 'pools', 'legal', 'event_matching')),
    'science_identity': ('da178ec822aef5d4a025197a4d33b1b95e68b8c555b1344ea9b39ce01208deee',
                         ('integer', 'valid_box', 'parse_gt', 'modal', 'event_identity')),
    'science_matching': ('18477ee6f47bf4d3198e6ee090c0fe34890c41cc765440fc80a5a0e3042b7ab5',
                         ('_exact', '_key', '_keys', '_prepare', '_components', '_integer_scale',
                          '_solve_component', 'solve', 'optimal_secondary_range', 'can_match_right_optimally')),
    'science_gt_view': ('5e42070be8b3ea744de940bfe766c93a254533364d5265fe6b2e4797930d0b9f',
                        ('number_suffix', 'stable', 'exact_time', 'position', 'gt_row')),
    'science_aggregate': ('281774d268424be02d5f1248262e38da6ba2dc352ca0ee3b042cd926ae9590b8',
                          ('aggregate',)),
    'science_panel_score': ('91d3082c10fcad8460a5c73c563822e486064a7c39daaa5bb9919df9bcf7a1be',
                            ('require', 'output_pool', 'validate_events')),
}


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _serial(value):
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _serial(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serial(v) for v in value]
    if isinstance(value, set):
        return sorted(_serial(v) for v in value)
    return value


def _loads(raw):
    def pairs(values):
        result = {}
        for key, value in values:
            _require(key not in result, 'Duplicate JSON member: ' + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('Nonfinite JSON constant: ' + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def _binding(value):
    _require(isinstance(value, dict), 'A byte/hash/path binding is required')
    _require(isinstance(value.get('path'), str) and value['path'], 'Missing bound path')
    _require(type(value.get('bytes')) is int and value['bytes'] >= 0, 'Missing bound byte count')
    _require(isinstance(value.get('sha256'), str) and re.fullmatch('[0-9a-f]{64}', value['sha256']), 'Invalid SHA256')
    return {k: value[k] for k in ('path', 'bytes', 'sha256')}


def _same_binding(a, b):
    a, b = _binding(a), _binding(b)
    return a == b


def _read(ctx, binding, purpose):
    binding = _binding(binding)
    raw = ctx.read_bytes(binding['path'], expected_sha=binding['sha256'], purpose=purpose)
    _require(len(raw) == binding['bytes'] and hashlib.sha256(raw).hexdigest() == binding['sha256'],
             'Bound bytes differ: ' + binding['path'])
    ctx.budget.check(purpose)
    return raw


def _json(ctx, binding, purpose):
    raw = _read(ctx, binding, purpose)
    if binding['path'].endswith('.gz'):
        raw = gzip.decompress(raw)
        return _loads(raw)
    strict = _loads(raw)
    # Register the verified parent JSON with Ctx before admitting its children.
    registered = ctx.json(binding['path'], expected_sha=binding['sha256'], purpose=purpose)
    _require(registered == strict, 'JSON parser disagreement')
    return strict


def _asset_items(ctx, role, sequence=None, system=None):
    return [x for x in ctx.manifest['assets'] if x['role'] == role
            and x.get('sequence') == sequence and x.get('system') == system]


def _asset(ctx, role, sequence=None, system=None):
    items = _asset_items(ctx, role, sequence, system)
    _require(len(items) == 1, 'Exactly one explicit asset required: ' + repr((role, sequence, system)))
    return _binding(items[0]['binding'])


def _listed_binding(ctx, binding):
    binding = _binding(binding)
    _require(any(_same_binding(x['binding'], binding) for x in ctx.manifest['assets']),
             'Referenced file is not explicitly listed in manifest: ' + binding['path'])
    return binding


def _sequences(ctx):
    value = ctx.manifest['sequences']
    _require(isinstance(value, list) and len(value) == 2 and len(set(value)) == 2,
             'Exactly two explicit sequences required')
    _require(all(isinstance(s, str) and re.fullmatch('MOT20-[0-9]{2}', s) for s in value),
             'Invalid MOT20 sequence namespace')
    return tuple(value)


def _header(ctx, doc, *, sequence=None, system=None, stages=None):
    _require(doc.get('complete') is True, 'Incomplete runtime artifact')
    _require(doc.get('manifest_sha256') == ctx.manifest_sha256, 'Runtime manifest differs')
    _require(doc.get('freeze_sha256') == ctx.freeze_sha256, 'Runtime freeze differs')
    if hasattr(ctx, 'approval_sha256'):
        _require(doc.get('approval_sha256') == ctx.approval_sha256, 'Runtime execution authorization differs')
    if sequence is not None:
        _require(doc.get('sequence') == sequence, 'Runtime sequence differs')
    if system is not None:
        _require(doc.get('system') == system, 'Runtime system differs')
    if stages is not None:
        _require(doc.get('stage') in stages, 'Runtime stage differs')


def _files(doc):
    files = doc.get('files')
    _require(isinstance(files, list), 'Explicit runtime files list required')
    _require(len({x.get('id') for x in files}) == len(files), 'Duplicate runtime file ID')
    for item in files:
        _require(isinstance(item.get('id'), str) and item['id'], 'Runtime file lacks stable ID')
        _binding(item['binding'])
    return files


def _file(files, role, gate=None):
    values = [x for x in files if x.get('role') == role
              and (gate is None or x.get('id') == role + ':' + gate)]
    _require(len(values) == 1, 'Missing/duplicate runtime file: ' + role + ':' + str(gate))
    return values[0]['binding']


def _output(ctx, path, role, sequence=None, system=None, gate=None):
    binding = _binding(ctx.record_output(path, role))
    return dict(id=role + (':' + gate if gate else ''), role=role,
                sequence=sequence, system=system, binding=binding)


def _save(ctx, name, obj, role, sequence=None, system=None):
    path = ctx.out / name
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(_serial(obj), stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write('\n')
    return _output(ctx, path, role, sequence, system)


def _metadata(doc):
    m = doc['metadata']
    length = m.get('nb_frames', m.get('seqLength'))
    _require(type(length) is int and length > 0, 'Invalid sequence frame count')
    _require(m.get('fps') == 25, 'Frozen E1-v2 MOT20 timing requires25fps')
    for name in ('width', 'height'):
        _require(type(m.get(name)) is int and m[name] > 0, 'Missing native image dimension')
    return dict(nb_frames=length, fps=25, width=m['width'], height=m['height'])


def import_reference(ctx, request):
    """Import explicitly selected old P2/O1 bytes; no reconstruction or scoring."""
    seq, system = request.sequence, request.system
    _require(seq in _sequences(ctx) and system in ('p2', 'o1'), 'Reference import scope differs')
    _require(ctx.manifest.get('reference_modes', {}).get(system) == 'import_existing',
             'P2/O1 mode unresolved: explicit import_existing is required')
    contract_ref = _asset(ctx, 'reference_contract', seq, system)
    contract = _json(ctx, contract_ref, 'Approved existing-reference import contract')
    cp = _asset(ctx, 'reference_complete', seq, system)
    _require(contract.get('source_complete_sha256') == cp['sha256'], 'Import contract completion mismatch')
    _require(contract.get('identity_pool') == 'actual_tracker_rows', 'No raw-box identity fallback allowed')
    expected = contract.get('expected_complete_fields')
    _require(isinstance(expected, dict) and {'protocol_sha256', 'clarification55_sha256'} <= set(expected),
             'Import contract must bind original protocol and clarification')
    lineage = contract.get('lineage_files')
    _require(isinstance(lineage, list) and lineage, 'Explicit source-code/parameter/weight lineage required')
    kinds = {x.get('role') for x in lineage}
    _require({'source_code', 'source_parameters'} <= kinds and (system == 'o1' or 'weight' in kinds),
             'Import lineage lacks code, parameters or P2 weight')
    for item in lineage:
        _read(ctx, _listed_binding(ctx, item['binding']), 'Reference lineage: ' + item['role'])
    old = _json(ctx, cp, 'Old completed reference record, not old identity answers')
    _require(old.get('complete') is True and old.get('pipeline') == system.upper()
             and old.get('sequence') in (seq, seq[-2:]), 'Old reference completion scope differs')
    for key, value in expected.items():
        _require(old.get(key) == value, 'Old completion contract differs: ' + key)
    _require(isinstance(old.get('files'), dict), 'Old completion files must be explicit dictionary')
    # Verify every old completion artifact only if separately manifest-authorized.
    # No path in an old JSON silently expands the reading boundary.
    for binding in old['files'].values():
        _read(ctx, _listed_binding(ctx, binding), 'Explicit complete-reference artifact hash')
    selected = [('frames', None, 'frames')]
    selected += [('gate_events', g, g + '_events') for g in GATES]
    selected += [('gate_points', g, g + '_points') for g in GATES]
    outputs, metadata = [], None
    for role, gate, oldkey in selected:
        binding = _listed_binding(ctx, old['files'][oldkey])
        raw = _read(ctx, binding, 'Copy already-completed reference bytes without modifications')
        if role == 'gate_events':
            doc = _loads(gzip.decompress(raw) if binding['path'].endswith('.gz') else raw)
            _require(doc.get('sequence') == seq and doc.get('gate_id') == gate, 'Reference event scope differs')
            m = _metadata(doc)
            if metadata is None:
                metadata = m
            _require(m == metadata, 'Reference gate metadata differs')
        suffix = '.jsonl.gz' if role in ('frames', 'gate_points') else ('.json.gz' if binding['path'].endswith('.gz') else '.json')
        name = (role + ('_' + gate if gate else '') + suffix)
        destination = ctx.out / name
        with destination.open('xb') as sink:
            sink.write(raw)
        outputs.append(_output(ctx, destination, role, seq, system, gate))
    return dict(schema='r15_confirmation85_import_complete_v1', status='COMPLETE',
                sequence=seq, system=system, metadata=metadata, frame_format='idxfix_reference',
                source_complete=cp, source_contract=contract_ref, source_lineage=lineage,
                files=outputs, old_identity_not_used=True, no_reference_rebuild=True)


def _admit(ctx, binding, parent_sha, purpose):
    binding = _binding(binding)
    ctx.admit_generated(binding, parent_sha, purpose)
    return binding


def _verify_unit(ctx, cp, parent_sha, seq, system):
    _admit(ctx, cp, parent_sha, 'Explicit unit completion from verified runtime index/seal')
    complete = _json(ctx, cp, 'Verify unit completion')
    _header(ctx, complete, sequence=seq, system=system, stages={'consume', 'import_reference'})
    doc = complete.get('result')
    _require(isinstance(doc, dict), 'Unit completion lacks worker result')
    _require(doc.get('status') == 'COMPLETE', 'Unit is not technically complete')
    _require(doc.get('sequence') == seq and doc.get('system') == system, 'Worker result namespace differs')
    files = _files(doc)
    _file(files, 'frames')
    for g in GATES:
        _file(files, 'gate_events', g)
        _file(files, 'gate_points', g)
    for item in files:
        _require(item.get('sequence') == seq and item.get('system') == system, 'Unit artifact namespace differs')
        ref = _admit(ctx, item['binding'], cp['sha256'], 'Explicit completed unit artifact')
        _read(ctx, ref, 'Verify completed artifact bytes/hash before sealing/scoring')
    # The enclosing runner may also register claims, journals and lineage files.
    # They are sealed too, rather than checking only the scientific subset.
    _require(isinstance(complete.get('files'), list), 'Complete artifact inventory missing')
    for item in complete['files']:
        ref = _admit(ctx, item['binding'], cp['sha256'], 'Enclosing completion artifact')
        _read(ctx, ref, 'Verify every completion output')
    _metadata(doc)
    format_expected = 'panel_outputs' if system in PANELS else ('idxfix_reference' if system in ('p2', 'o1') else 'idxfix_post_m4')
    _require(doc.get('frame_format') == format_expected, 'Actual-output identity pool format differs')
    if system in ('p2', 'o1'):
        _require(complete['stage'] == 'import_reference' and ctx.manifest.get('reference_modes', {}).get(system) == 'import_existing',
                 'Reference mode differs from explicit approved import')
    else:
        _require(complete['stage'] == 'consume', 'Expected frozen downstream consumption')
    return doc


def seal(ctx, request):
    """Validate exactly seven-by-two completed units, then emit a single seal."""
    _require(request.handoff and request.handoff_sha256, 'Explicit fourteen-unit index binding required')
    index = ctx.json(request.handoff, expected_sha=request.handoff_sha256, purpose='Explicit unit index')
    _header(ctx, index, stages={'collect_receipts'})
    _require(index.get('schema') == 'r15_confirmation85_runtime_handoff_v1', 'Unexpected unit-index schema')
    entries = index.get('units')
    _require(isinstance(entries, list), 'Index lacks explicit units')
    expected = {(s, m) for s in _sequences(ctx) for m in SYSTEMS}
    keys = [(r.get('sequence'), r.get('system')) for r in entries]
    _require(len(keys) == 14 and len(set(keys)) == 14 and set(keys) == expected, 'All fourteen units must be present exactly once')
    units = []
    seq_meta = {}
    for entry in sorted(entries, key=lambda x: (x['sequence'], SYSTEMS.index(x['system']))):
        seq, system, cp = entry['sequence'], entry['system'], _binding(entry['binding'])
        doc = _verify_unit(ctx, cp, request.handoff_sha256, seq, system)
        metadata = _metadata(doc)
        if seq in seq_meta:
            _require(metadata == seq_meta[seq], 'System dimensions/frame count differ within sequence')
        seq_meta[seq] = metadata
        units.append(dict(sequence=seq, system=system, binding=cp, metadata=metadata,
                          frame_format=doc['frame_format'], files=doc['files']))
    payload = dict(schema='r15_confirmation85_seal_v1', complete=True, stage='seal',
                   manifest_sha256=ctx.manifest_sha256, freeze_sha256=ctx.freeze_sha256,
                   approval_sha256=ctx.approval_sha256,
                   units=units, index=dict(path=request.handoff, sha256=request.handoff_sha256),
                   all_14_units_verified=True, no_scoring=True)
    artifact = _save(ctx, 'seal.json', payload, 'panel_seal')
    return dict(schema='r15_confirmation85_seal_complete_v1', status='COMPLETE',
                units=units, all_14_units_verified=True, files=[artifact], no_scoring=True)


def decide_confirmation(per_sequence):
    """Pure #85 decisions. No pooled rescue, rounded thresholds or G2 selection.

    Input: two sequence keys, each mapping all seven systems to
    {'bins': {'low': {'correct': int,'gt': int}, 'high': {...}}}.
    """
    errors = []
    if not isinstance(per_sequence, dict) or len(per_sequence) != 2:
        return dict(status='INDETERMINATE', reasons=['Exactly two sequences required'], H_A=None, H_B=None)
    for seq, systems in per_sequence.items():
        if not isinstance(systems, dict) or set(systems) != set(SYSTEMS):
            errors.append(str(seq) + ': missing/extra system')
            continue
        for b in ('low', 'high'):
            den = set()
            for system in SYSTEMS:
                try:
                    row = systems[system]['bins'][b]
                    n, d = row['correct'], row['gt']
                except (KeyError, TypeError):
                    errors.append(f'{seq}/{system}/{b}: missing count')
                    continue
                if type(n) is not int or type(d) is not int or d <= 0 or not 0 <= n <= d:
                    errors.append(f'{seq}/{system}/{b}: invalid/zero population')
                else:
                    den.add(d)
            if len(den) != 1:
                errors.append(f'{seq}/{b}: populations disagree')
    if errors:
        return dict(status='INDETERMINATE', reasons=errors, H_A=None, H_B=None)
    ha, hb = {}, {}
    for seq, systems in per_sequence.items():
        checks = {}
        for system in PANELS:
            low, high = systems[system]['bins']['low'], systems[system]['bins']['high']
            checks[system] = dict(low=dict(low, passed=10 * low['correct'] <= 7 * low['gt']),
                                  high=dict(high, passed=10 * high['correct'] >= 9 * high['gt']))
            checks[system]['passed'] = checks[system]['low']['passed'] and checks[system]['high']['passed']
        ha[seq] = dict(passed=all(c['passed'] for c in checks.values()), systems=checks)
        n = systems['yolox_v11']['bins']['low']['correct']
        best = max(systems[m]['bins']['low']['correct'] for m in PANELS)
        hb[seq] = dict(passed=n > best, yolox_v11_correct=n, best_panel_correct=best,
                      common_gt=systems['yolox_v11']['bins']['low']['gt'], required='strictly_greater')
    pooled = {m: {b: dict(correct=sum(x[m]['bins'][b]['correct'] for x in per_sequence.values()),
                          gt=sum(x[m]['bins'][b]['gt'] for x in per_sequence.values()))
                   for b in ('low', 'high')} for m in SYSTEMS}
    return dict(status='COMPLETE', H_A=dict(overall=all(x['passed'] for x in ha.values()), per_sequence=ha),
                H_B=dict(overall=all(x['passed'] for x in hb.values()), per_sequence=hb),
                pooled_descriptive_only=pooled, pooled_does_not_determine_H_A_or_H_B=True,
                independent_recompute_status='PENDING_CLAUDE_RECOMPUTE')


def _science(ctx, sequences):
    namespaces, ledger = {}, []
    base = dict(Fraction=Fraction, math=math, re=re, collections=collections,
                defaultdict=collections.defaultdict, Counter=collections.Counter,
                Mapping=Mapping, heappop=heappop, heappush=heappush, lcm=math.lcm,
                SEQS=tuple(sequences), GATES=GATES, BINS=BINS, UNKNOWN=UNKNOWN)
    for role, (pin, names) in SCIENCE.items():
        binding = _asset(ctx, role)
        _require(binding['sha256'] == pin, 'Scientific source hash differs: ' + role)
        text = _read(ctx, binding, 'Verify frozen scientific source before exact AST extraction').decode('utf-8-sig')
        nodes = [n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name in names]
        _require(len(nodes) == len(names) and {n.name for n in nodes} == set(names), 'Scientific function inventory differs')
        ns = dict(base)
        exec(compile(ast.Module(body=nodes, type_ignores=[]), '<verified-frozen:' + role + '>', 'exec'), ns)
        namespaces[role] = SimpleNamespace(**{name: ns[name] for name in names})
        ledger.append(dict(role=role, binding=binding, functions=list(names),
                           ast_sha256=hashlib.sha256(ast.dump(ast.Module(body=nodes, type_ignores=[]), include_attributes=False).encode()).hexdigest()))
    return namespaces, ledger


def _jsonl(raw, compressed):
    if compressed:
        raw = gzip.decompress(raw)
    for line in raw.decode('utf-8-sig').splitlines():
        _require(bool(line.strip()), 'Blank JSONL record')
        yield _loads(line)


def _line(sink, value):
    sink.write(json.dumps(_serial(value), ensure_ascii=False, allow_nan=False, separators=(',', ':')) + '\n')


def score(ctx, request):
    """Recompute all seven systems' identities from actual output boxes only."""
    _require(request.seal and request.seal_sha256, 'A complete-panel seal binding is required')
    sealed_complete = ctx.json(request.seal, expected_sha=request.seal_sha256, purpose='Explicit sealed fourteen-unit result')
    _header(ctx, sealed_complete, stages={'seal'})
    sealed = sealed_complete.get('result', sealed_complete)
    _require(sealed.get('schema') in ('r15_confirmation85_seal_v1', 'r15_confirmation85_seal_complete_v1'), 'Unexpected seal schema')
    _require(sealed.get('all_14_units_verified') is True, 'Panel not completely sealed')
    seqs = _sequences(ctx)
    entries = sealed.get('units', [])
    keys = [(r.get('sequence'), r.get('system')) for r in entries]
    _require(len(keys) == 14 and len(set(keys)) == 14 and set(keys) == {(s, m) for s in seqs for m in SYSTEMS},
             'Scoring requires complete seven-by-two panel')
    # Revalidate every completion and every output before reading GT/scoring.
    units_by_key = {}
    for entry in entries:
        key = entry['sequence'], entry['system']
        units_by_key[key] = _verify_unit(ctx, entry['binding'], request.seal_sha256, *key)
    modules, science_ledger = _science(ctx, seqs)
    e1, identity, matching, view, aggregate, panel = (modules['science_' + x] for x in
        ('core', 'identity', 'matching', 'gt_view', 'aggregate', 'panel_score'))
    import numpy as np
    # The only algorithmic code loaded above is hash-pinned function AST. No old
    # main, import-time annotation reader, G2 decision or saved identity is used.
    transitions_ref = _asset(ctx, 'transitions')
    transitions = list(_jsonl(_read(ctx, transitions_ref, 'Explicit confirmed-event derivation input'),
                              transitions_ref['path'].endswith('.gz')))
    _require(all(r.get('sequence') in seqs for r in transitions), 'Derived events outside explicit scope')
    _require(len({r['event_id'] for r in transitions}) == len(transitions), 'Duplicate derived-event IDs')
    views = [view.gt_row(r, transitions_ref['path'], i) for i, r in enumerate(transitions, 1)]
    main_units, evidence_files = [], []
    for seq in seqs:
        metas = [_metadata(units_by_key[(seq, s)]) for s in SYSTEMS]
        _require(all(m == metas[0] for m in metas), 'Scoring unit metadata disagree')
        length = metas[0]['nb_frames']
        _require(all(1 <= r['gt_frame_1based'] <= length for r in transitions if r['sequence'] == seq),
                 'Derived transition outside declared sequence length')
        gt_ref = _asset(ctx, 'gt', seq)
        gt, classes = identity.parse_gt(_read(ctx, gt_ref, 'Explicit sequence GT; all E1-v2 competing identities').decode('utf-8-sig'), length)
        for system in SYSTEMS:
            ctx.budget.check('Score ' + seq + '/' + system)
            doc = units_by_key[(seq, system)]
            files = _files(doc)
            frames_ref = _file(files, 'frames')
            outputobs = collections.defaultdict(list)
            nframes = 0
            identity_path = ctx.out / (system + '_' + seq + '_frame_identity.jsonl.gz')
            raw = _read(ctx, frames_ref, 'Actual emitted output-box pool; no raw-box substitution')
            with gzip.open(identity_path, 'xt', encoding='utf-8', compresslevel=6) as sink:
                for fr in _jsonl(raw, frames_ref['path'].endswith('.gz')):
                    ctx.budget.check('Frame identity assignment')
                    sf = nframes + 1
                    if system in PANELS:
                        pool = panel.output_pool(fr, sf, e1)
                    else:
                        _require(type(fr.get('source_frame')) is int and fr['source_frame'] == sf
                                 and fr.get('frame') == sf - 1 and abs(fr['time_s'] - (sf - 1) / 25) <= 1e-9,
                                 'Native output frame/time mismatch')
                        _, pool, _, _ = e1.pools(fr, 'v11' if system in ('v11', 'yolox_v11') else system.upper())
                    records, _, audit = e1.assign(pool, gt.get(sf, []), matching.solve, np)
                    observations = [dict(source_frame=sf, track_id=r['tid'], output_key=r['index'],
                        gt_id=r['gt_id'], gt_class=r['gt_class'], gt_line=r['gt_line'], status=r['status'],
                        box=r['box'], assigned_iou=r['assigned_iou'], margin=r['margin']) for r in records]
                    for o in observations:
                        outputobs[o['track_id']].append(o)
                    _line(sink, dict(source_frame=sf, observations=observations, output_assignment=audit))
                    nframes += 1
            del raw
            _require(nframes == length, 'Incomplete native frame cache')
            evidence_files.append(_output(ctx, identity_path, 'frame_identity', seq, system))
            event_audits = []
            for gate in GATES:
                ctx.budget.check('Gate event matching')
                event_doc = _json(ctx, _file(files, 'gate_events', gate), 'Frozen final events; replace historical identity verdict')
                panel.validate_events(event_doc, seq, gate, length)
                preds = event_doc['final_events']
                for p in preds:
                    _require(p['track_id'] in outputobs, 'Final event has no emitted track')
                    _require(abs(p['time_s'] - (p['source_frame'] - 1) / 25) <= 1e-9, 'Final event time mismatch')
                    # Explicitly discard old verdicts. They are never accepted as inputs.
                    p.pop('identity_association', None)
                    p.pop('_identity', None)
                    p['_identity'] = identity.event_identity(outputobs[p['track_id']], p['source_frame'], classes)
                selected = [(r, g) for r, g in zip(transitions, views)
                            if r['sequence'] == seq and r['line_id'] == gate and r['confirmed']]
                selected.sort(key=lambda z: (z[0]['gt_frame_1based'], z[0]['track_id'], z[0]['event_id']))
                truths = [dict(id=r['event_id'], frame=int(r['gt_frame_1based']), gid=int(r['track_id']),
                               direction=r['direction'], position=r['position_native_px'], h=g['h'], bin=g['bin']) for r, g in selected]
                matched, _, _, audit = e1.event_matching(preds, truths, matching.solve, matching.can_match_right_optimally)
                main_units.append(dict(system=system, sequence=seq, gate=gate, N_GT=len(truths), N_final=len(preds),
                    correct=len(matched), identity_statuses=dict(collections.Counter(p['_identity']['status'] for p in preds)),
                    bins={b: dict(correct=sum(j in matched for j, g in enumerate(truths) if g['bin'] == b),
                                  GT=sum(g['bin'] == b for g in truths)) for b in BINS}))
                event_audits.append(dict(gate=gate, recomputed_event_identities=[dict(prediction_id=p['prediction_id'],
                    source_frame=p['source_frame'], track_id=p['track_id'], identity=p['_identity']) for p in preds], **audit))
            evidence_files.append(_save(ctx, system + '_' + seq + '_event_matching.json', event_audits,
                                        'event_matching', seq, system))
    summaries = {s: dict(by_sequence={seq: aggregate.aggregate([u for u in main_units if u['system'] == s and u['sequence'] == seq]) for seq in seqs},
                         pooled_descriptive_only=aggregate.aggregate([u for u in main_units if u['system'] == s])) for s in SYSTEMS}
    decision_input = {seq: {s: dict(bins={b: dict(correct=summaries[s]['by_sequence'][seq]['bins'][b]['numerator'],
        gt=summaries[s]['by_sequence'][seq]['bins'][b]['denominator']) for b in ('low', 'high')}) for s in SYSTEMS} for seq in seqs}
    decisions = decide_confirmation(decision_input)
    report = dict(schema='r15_confirmation85_scores_v1', status='PENDING_CLAUDE_RECOMPUTE',
                  population='all_confirmed_whole_sequence_not_core_windows', systems=summaries,
                  confirmed_population={seq: sum(bool(r['confirmed']) for r in transitions if r['sequence'] == seq) for seq in seqs},
                  hypotheses=decisions, scientific_sources=science_ledger, numpy=np.__version__,
                  identity_pool='actual emitted tracker boxes; v11 post-M4 tracker_rows; panel author outputs',
                  precision_policy='All final events remain in denominator, including unknown, ambiguous, mixed and ignore',
                  old_identity_not_used=True, no_G2_selection=True, no_inference=True, no_tracking=True,
                  scope=list(seqs), independent_recompute_required=True)
    evidence_files += [_save(ctx, 'units.json', dict(main=main_units), 'score_units'),
                       _save(ctx, 'scores.json', report, 'scores')]
    return dict(schema='r15_confirmation85_score_complete_v1', status='PENDING_CLAUDE_RECOMPUTE',
                files=evidence_files, hypotheses=decisions, scientific_sources=science_ledger,
                no_inference=True, no_tracking=True, old_identity_not_used=True)


def synthetic_checks(science_source_bytes):
    """Code-only in-memory checks; caller supplies frozen source text, no data IO.

    Does not exercise real sequence readers or certify production readiness.
    The enclosing integration suite tests manifest/seal denial boundaries.
    """
    _require(set(science_source_bytes) == set(SCIENCE), 'Synthetic source inventory differs')
    class FakeContext:
        manifest = dict(assets=[dict(id=k, role=k, sequence=None, system=None,
                        binding=dict(path=k, bytes=len(science_source_bytes[k]), sha256=SCIENCE[k][0])) for k in SCIENCE])
        budget = SimpleNamespace(check=lambda label: None)
        def read_bytes(self, path, expected_sha=None, purpose=''):
            return science_source_bytes[path]
    modules, ledger = _science(FakeContext(), ('MOT20-01', 'MOT20-02'))
    e1, identity, matching, panel = (modules['science_' + x] for x in ('core', 'identity', 'matching', 'panel_score'))
    import numpy as np
    fr = dict(frame=0, source_frame=1, time_s=0,
        detections=[dict(raw_detection_index=0, box=[100., 100., 110., 120.], confidence=.2,
                        track_id=4, original_track_id=2, tracking_eligible=True)],
        tracker_rows=[[0., 0., 10., 20., 4, .2, 0, 0]],
        tracker_frame_metadata=dict(tracker_input_raw_indices=[0]))
    rawpool, tracked, _, _ = e1.pools(fr, 'v11')
    gt = [dict(gid=7, cls=1, box=(0., 0., 10., 20.), gt_line=1)]
    rec, _, _ = e1.assign(tracked, gt, matching.solve, np)
    rawrec, _, _ = e1.assign(rawpool, gt, matching.solve, np)
    assert rec[0]['gt_id'] == 7 and rawrec[0]['gt_id'] is None
    panel_frame = dict(frame=0, source_frame=1, outputs=[dict(emitted_output_index=0,
                       track_id=4, box=[0., 0., 10., 20.], score=.8, raw_detection_index=None)])
    assert panel.output_pool(panel_frame, 1, e1)[0]['tid'] == 4
    observations = [dict(source_frame=f, status='valid', gt_id=7) for f in (1, 2, 3)]
    ident = identity.event_identity(observations, 2, {7: 1})
    assert ident['status'] == 'known'
    p = dict(prediction_id='r000001', source_frame=2, track_id=4, fragment_index=0,
             direction='IN', crossing_position_native_px=[0., 0.], _identity=ident)
    truth = [dict(id='synthetic_g', frame=2, gid=7, direction='IN', position=[0., 0.], h=10., bin='low')]
    matched, _, _, _ = e1.event_matching([p], truth, matching.solve, matching.can_match_right_optimally)
    assert matched == {0: 0}
    row = dict(correct=1, N_GT=1, N_final=3, identity_statuses={'known': 1, 'unidentified': 1, 'ignore': 1},
               bins={b: dict(correct=int(b == 'low'), GT=int(b == 'low')) for b in BINS})
    agg = modules['science_aggregate'].aggregate([row])
    assert agg['identity_precision']['exact'] == Fraction(1, 3)
    denied = False
    try:
        import_reference(SimpleNamespace(manifest=dict(sequences=['MOT20-01', 'MOT20-02'], reference_modes={})),
                         SimpleNamespace(sequence='MOT20-01', system='p2'))
    except ValueError:
        denied = True
    assert denied
    return dict(status='PASS', real_data_read=False, no_inference=True, no_tracking=True,
                cases=['frozen_AST_pin_verification', 'actual_box_not_raw_box', 'panel_null_raw_index_allowed',
                       'conservative_event_identity', 'frozen_exact_matching', 'all_final_denominator',
                       'unresolved_reference_mode_denied'], scientific_sources=ledger)
