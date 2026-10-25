"""Explicit-input control plane. Importing this module performs no file I/O.

An approval hash is an integrity binding, not proof of human consent: an external
execution instruction must authorize its contents. No producer string grants
permission. Scientific data are opened only by the later, bound worker.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import datetime
import hashlib
import json
import math
import os
import re
import shutil
import stat
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
STAGES = ('export_yolox', 'consume', 'import_reference', 'seal', 'score')
SYSTEMS = ('yolox_v11', 'byte', 'oc', 'bot', 'p2', 'v11', 'o1')
SCOPE = {'development': ('MOT20-01', 'MOT20-02'),
         'confirmation': ('MOT20-03', 'MOT20-05')}
SCHEMA = 'r15_confirmation85_production_inputs_v1'
APPROVAL_SCHEMA = 'r15_confirmation85_execution_approval_v1'
FREEZE_SCHEMA = 'r15_confirmation85_production_freeze_v1'
HANDOFF_SCHEMA = 'r15_confirmation85_runtime_handoff_v1'


class ContractError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise ContractError(message)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(',', ':')).encode('utf-8')


def json_bytes(raw):
    def pairs(rows):
        answer = {}
        for key, value in rows:
            require(key not in answer, 'Duplicate JSON key: ' + key)
            answer[key] = value
        return answer
    def invalid(value):
        raise ContractError('Non-finite JSON: ' + value)
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs,
                      parse_constant=invalid)


def valid_sha(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def validate_binding(binding):
    require(isinstance(binding, dict) and set(binding) == {'path', 'bytes', 'sha256'},
            'Binding must contain exactly path/bytes/sha256')
    require(isinstance(binding['path'], str) and binding['path'] and '\x00' not in binding['path'], 'Invalid binding path')
    require(type(binding['bytes']) is int and binding['bytes'] >= 0, 'Invalid binding byte count')
    require(valid_sha(binding['sha256']), 'Invalid binding SHA256')
    return binding


def path_key(path, root=ROOT):
    path = Path(path)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _reparse(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return bool(getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 1024)) or stat.S_ISLNK(info.st_mode)


def guarded_path(path, root=ROOT, *, scope=None, control=False):
    """Reject forbidden lexical paths before filesystem inspection, then aliases.

    Windows junctions/reparse points and symlinks are not accepted for bound
    production assets. No hash verification follows an unapproved redirection.
    """
    candidate = Path(path)
    lexical = Path(os.path.abspath(str(candidate if candidate.is_absolute() else root / candidate)))
    def check_text(p):
        value = str(p).replace('\\', '/').lower()
        deny = ('ht21', 'e18_test_windows', 'sealed_system_v1', 'e25_timeline',
                'review/labels', 'e16_scoring', 'e10_dedup', 'spatial_vlm_pilot')
        require(not any(x in value for x in deny), 'Forbidden path category')
        sequences = set(re.findall(r'mot20[-_/](0[1-5])', value))
        if control:
            require(not sequences, 'A data-sequence path cannot be a control document')
            require(p.suffix.lower() == '.json', 'Controls must be explicit JSON documents')
            require(not any(x in value for x in ('/gt/', '/img1/', 'gt.txt', '/gt_', '.jsonl', 'claude_scores', 'gmc-')),
                    'A data/cache path cannot masquerade as a control document')
            allowed_roots = (root / 'data/r15/confirmation85', root / 'docs', root / 'codex_supervision/claude_checks')
            require(any(p.is_relative_to(q) for q in allowed_roots), 'Control outside approved project control directories')
        elif scope is not None:
            allowed = {s[-2:] for s in SCOPE[scope]}
            require(sequences <= allowed, 'Path sequence conflicts with manifest scope')
    check_text(lexical)
    for part in (lexical, *lexical.parents):
        require(not _reparse(part), 'Symlink/junction/reparse-point paths are forbidden: ' + str(part))
    resolved = lexical.resolve()
    check_text(resolved)
    require(os.path.normcase(str(resolved)) == os.path.normcase(str(lexical)), 'Resolved path differs from bound lexical path')
    return resolved


def binding_for(path):
    path = Path(path).resolve()
    h = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            size += len(chunk)
            h.update(chunk)
    return dict(path=str(path), bytes=size, sha256=h.hexdigest())


def contains_binding(doc, wanted):
    if isinstance(doc, dict):
        if set(doc) == {'path', 'bytes', 'sha256'} and doc == wanted:
            return True
        return any(contains_binding(value, wanted) for value in doc.values())
    return isinstance(doc, list) and any(contains_binding(value, wanted) for value in doc)


def validate_manifest(doc):
    mandatory = {'schema', 'manifest_id', 'producer', 'scope', 'sequences', 'systems',
                 'assets', 'freeze', 'reference_modes', 'run_root', 'resources',
                 'interpreters', 'runtime_roots'}
    require(isinstance(doc, dict) and set(doc) == mandatory, 'Manifest fields differ')
    require(doc['schema'] == SCHEMA, 'Unsupported production manifest')
    require(isinstance(doc['manifest_id'], str) and re.fullmatch('[A-Za-z0-9_.-]{1,96}', doc['manifest_id']), 'Invalid manifest id')
    require(isinstance(doc['producer'], str), 'Producer is descriptive metadata only')
    require(doc['scope'] in SCOPE and doc['sequences'] == list(SCOPE[doc['scope']]), 'Sequence scope/order differs')
    require(doc['systems'] == list(SYSTEMS), 'System scope/order differs')
    validate_binding(doc['freeze'])
    require(doc['reference_modes'] == {'p2': 'import_existing', 'o1': 'import_existing'},
            'P2/O1 must be explicitly approved as import_existing; rebuild is not implemented/authorized')
    require(isinstance(doc['run_root'], str) and bool(doc['run_root']), 'Explicit run_root required')
    require(isinstance(doc['assets'], list), 'Assets must be an explicit list')
    ids, bypath = set(), {}
    for item in doc['assets']:
        require(isinstance(item, dict) and set(item) == {'id', 'role', 'sequence', 'system', 'binding'}, 'Asset fields differ')
        require(isinstance(item['id'], str) and item['id'] and item['id'] not in ids, 'Duplicate/invalid asset id')
        ids.add(item['id'])
        require(isinstance(item['role'], str) and re.fullmatch('[A-Za-z0-9_.-]+', item['role']), 'Invalid role')
        require(item['sequence'] is None or item['sequence'] in doc['sequences'], 'Asset sequence outside scope')
        require(item['system'] is None or item['system'] in SYSTEMS, 'Asset system outside scope')
        ref = validate_binding(item['binding'])
        old = bypath.get(ref['path'])
        require(old is None or old == ref, 'Conflicting path bindings')
        bypath[ref['path']] = ref
    r = doc['resources']
    require(isinstance(r, dict) and set(r) == {'stages', 'max_output_bytes', 'min_free_bytes', 'max_workers', 'cpu_threads'}, 'Resource fields differ')
    require(type(r['max_output_bytes']) is int and r['max_output_bytes'] > 0, 'Output resource limit missing')
    require(type(r['min_free_bytes']) is int and r['min_free_bytes'] >= 0, 'Disk floor missing')
    require(type(r['max_workers']) is int and r['max_workers'] in (1, 2), 'Explicit 1/2-worker limit required')
    require(type(r['cpu_threads']) is int and 1 <= r['cpu_threads'] <= 4, 'Explicit CPU thread count required')
    require(isinstance(r['stages'], dict) and set(r['stages']) == set(STAGES), 'Every stage needs resource limits')
    for limits in r['stages'].values():
        require(set(limits) == {'cpu_seconds', 'wall_seconds'}, 'Stage limit fields differ')
        require(all(type(v) in (int, float) and math.isfinite(v) and v > 0 for v in limits.values()), 'Invalid time limit')
    require(isinstance(doc['interpreters'], dict) and set(doc['interpreters']) == {'detector', 'cpu'}, 'Both interpreter bindings required')
    for ref in doc['interpreters'].values():
        validate_binding(ref)
    require(isinstance(doc['runtime_roots'], list) and all(isinstance(x, str) and x for x in doc['runtime_roots']), 'Explicit runtime roots required')
    return doc


@dataclass(frozen=True)
class Request:
    stage: str
    sequence: str | None = None
    system: str | None = None
    handoff: str | None = None
    handoff_sha256: str | None = None
    seal: str | None = None
    seal_sha256: str | None = None
    run_root: str | None = None


def validate_request(request, manifest):
    require(request.stage in STAGES, 'Unknown stage')
    if request.stage in ('seal', 'score'):
        require(request.sequence is None and request.system is None, 'Whole-run stage cannot select a subset')
    else:
        require(request.sequence in manifest['sequences'], 'Request sequence outside scope')
    if request.stage == 'export_yolox':
        require(request.system is None, 'Export is shared, not system-specific')
    elif request.stage == 'consume':
        require(request.system in ('yolox_v11', 'byte', 'oc', 'bot', 'v11'), 'Unsupported consumer')
    elif request.stage == 'import_reference':
        require(request.system in ('p2', 'o1'), 'Only fixed P2/O1 reference import permitted')
    requires_handoff = request.stage == 'seal' or (request.stage == 'consume' and request.system != 'v11')
    require(bool(request.handoff) == requires_handoff, 'Explicit handoff required only for shared-cache consumers/seal')
    require((request.handoff_sha256 is not None) == requires_handoff, 'Handoff SHA required')
    if requires_handoff:
        require(valid_sha(request.handoff_sha256), 'Invalid handoff SHA')
    require(bool(request.seal) == (request.stage == 'score'), 'Explicit seal required only for score')
    require((request.seal_sha256 is not None) == (request.stage == 'score'), 'Seal SHA required')
    if request.stage == 'score':
        require(valid_sha(request.seal_sha256), 'Invalid seal SHA')
    if request.run_root is not None:
        require(guarded_path(request.run_root, scope=manifest['scope']) == guarded_path(manifest['run_root'], scope=manifest['scope']), 'run_root differs from approval contract')


def stage_output(root, request):
    if request.stage == 'export_yolox':
        return root / 'export_yolox' / request.sequence
    if request.stage in ('consume', 'import_reference'):
        return root / 'systems' / request.system / request.sequence
    return root / request.stage


class Budget:
    def __init__(self, resources, stage, run_root):
        self.resources, self.limits, self.run_root = resources, resources['stages'][stage], run_root
        self.cpu, self.wall = time.process_time(), time.perf_counter()
    def check(self, label=''):
        require(time.process_time() - self.cpu <= self.limits['cpu_seconds'], 'CPU budget exceeded: ' + label)
        require(time.perf_counter() - self.wall <= self.limits['wall_seconds'], 'Wall budget exceeded: ' + label)
        anchor = self.run_root if self.run_root.exists() else self.run_root.parent
        while not anchor.exists():
            anchor = anchor.parent
        require(shutil.disk_usage(anchor).free >= self.resources['min_free_bytes'], 'Disk floor breached: ' + label)
    def output_check(self):
        # Only this new output tree is inspected, never an input/data tree.
        total = 0
        if self.run_root.exists():
            for p in self.run_root.rglob('*'):
                require(not _reparse(p), 'Output symlink/junction not permitted')
                if p.is_file():
                    total += p.stat().st_size
        require(total <= self.resources['max_output_bytes'], 'Whole-run output budget exceeded')
        return total
    def fields(self):
        return dict(cpu_seconds=time.process_time()-self.cpu, wall_seconds=time.perf_counter()-self.wall,
                    limits=self.limits)


class Ctx:
    """Bound I/O and output context; construction opens controls, not data.

    Runtime libraries may be imported from pre-approved environment roots, but
    register_runtime_tree never permits new data reads through this object.
    """
    def __init__(self, *, manifest_path, manifest_sha256, freeze_sha256,
                 approval_path, approval_sha256, request, out, root=ROOT, _synthetic_test=False):
        self.ROOT = self.project_root = Path(root).resolve()
        self.request = request
        self.control_reads = []
        self.documents = {}
        self.allowed, self.outputs = {}, {}
        self._claimed = False
        self._slot = None
        require(all(valid_sha(x) for x in (manifest_sha256, freeze_sha256, approval_sha256)), 'Full control hashes required')
        self.manifest_sha256, self.freeze_sha256, self.approval_sha256 = manifest_sha256, freeze_sha256, approval_sha256
        self.manifest = validate_manifest(self._control(manifest_path, manifest_sha256, 'Execution input manifest'))
        self.manifest_binding = self.control_reads[-1]['binding']
        require(self.manifest['freeze']['sha256'] == freeze_sha256, 'Freeze argument differs from manifest')
        self.freeze = self._control(self.manifest['freeze']['path'], freeze_sha256, 'Final frozen code/scope contract')
        self.freeze_binding = self.control_reads[-1]['binding']
        require(self.freeze_binding == {**self.manifest['freeze'], 'path': str(path_key(self.manifest['freeze']['path'], self.ROOT))}, 'Freeze bytes/path differ')
        require(self.freeze.get('schema') == FREEZE_SCHEMA, 'Unsupported freeze schema')
        for key in ('scope', 'sequences', 'systems', 'reference_modes'):
            require(self.freeze.get(key) == self.manifest[key], 'Freeze scope/mode differs: ' + key)
        require(isinstance(self.freeze.get('code'), list) and self.freeze['code'], 'Freeze must list actual code bindings')
        code_by_path = {}
        for ref in self.freeze['code']:
            validate_binding(ref)
            p = guarded_path(ref['path'], self.ROOT, scope=self.manifest['scope'])
            require(p not in code_by_path, 'Duplicate frozen code path')
            code_by_path[p] = ref
        self.approval = self._control(approval_path, approval_sha256, 'Separately supplied explicit execution approval')
        self.approval_binding = self.control_reads[-1]['binding']
        a = self.approval
        require(not a.get('synthetic_fixture', False) or _synthetic_test is True,
                'Synthetic approval fixtures cannot authorize the production CLI')
        require(a.get('schema') == APPROVAL_SCHEMA and a.get('decision') == 'APPROVE_EXECUTION', 'No explicit production execution approval')
        require(a.get('manifest_sha256') == manifest_sha256 and a.get('freeze_sha256') == freeze_sha256, 'Approval binds different controls')
        require(a.get('allowed_stages') == list(STAGES), 'Approval must explicitly bind stage set')
        for key in ('scope', 'sequences', 'systems', 'reference_modes', 'resources', 'run_root'):
            require(a.get(key) == self.manifest[key], 'Approval differs: ' + key)
        require(isinstance(a.get('authorization_source'), str) and a['authorization_source'].strip(), 'External instruction reference required')
        validate_request(request, self.manifest)
        self.run_root = guarded_path(self.manifest['run_root'], self.ROOT, scope=self.manifest['scope'])
        permitted = self.ROOT / 'data/r15/confirmation85'
        require(self.run_root.is_relative_to(permitted) and self.run_root != permitted, 'Output root must be a new confirmation85 subdirectory')
        self.out = guarded_path(out, self.ROOT, scope=self.manifest['scope'])
        require(self.out == stage_output(self.run_root, request), 'Output differs from fixed stage layout')
        self.budget = Budget(self.manifest['resources'], request.stage, self.run_root)
        for item in self.manifest['assets']:
            ref = item['binding']
            p = guarded_path(ref['path'], self.ROOT, scope=self.manifest['scope'])
            require(not p.is_relative_to(self.run_root), 'Original asset cannot be inside new run output')
            self._allow(ref)
            if item['role'].startswith(('code', 'science_')) or item['role'] == 'python_module':
                require(p in code_by_path and code_by_path[p] == ref, 'Source asset absent from final code freeze')
        for ref in self.freeze['code']:
            self._allow(ref)
        self.runtime_roots = tuple(guarded_path(p, self.ROOT, scope=self.manifest['scope']) for p in self.manifest['runtime_roots'])
        # Verify the I/O/control implementation itself before data or workers.
        for filename in ('manifest.py', 'run.py'):
            p = Path(__file__).with_name(filename).resolve()
            require(p in code_by_path, 'Control implementation missing from freeze: ' + filename)
            self.read_bytes(p, purpose='Verify active production control code')
        self._verify_interpreter()
        require(not self.out.exists(), 'Output already exists; no automatic retry/resume of partial or completed unit')

    def _control(self, path, sha, purpose):
        p = guarded_path(path, self.ROOT, control=True)
        raw = p.read_bytes()
        require(sha_bytes(raw) == sha, 'Control hash mismatch: ' + str(p))
        ref = dict(path=str(p), bytes=len(raw), sha256=sha)
        self.control_reads.append(dict(binding=ref, purpose=purpose, utc=utc()))
        return json_bytes(raw)

    def _allow(self, ref):
        validate_binding(ref)
        p = guarded_path(ref['path'], self.ROOT, scope=self.manifest['scope'])
        normalized = dict(ref, path=str(p))
        old = self.allowed.get(p)
        require(old is None or old == normalized, 'Conflicting canonical-path bindings')
        self.allowed[p] = normalized
        return p

    def _verify_interpreter(self):
        key = 'detector' if self.request.stage == 'export_yolox' else 'cpu'
        ref = self.manifest['interpreters'][key]
        require(guarded_path(ref['path'], self.ROOT, scope=self.manifest['scope']) == Path(sys.executable).resolve(), 'Wrong interpreter for stage')
        self._allow(ref)
        self.read_bytes(ref['path'], purpose='Active interpreter bytes')

    def claim(self):
        require(not self._claimed, 'Context already claimed')
        self.budget.check('claim')
        self.run_root.mkdir(parents=True, exist_ok=True)
        slots = self.run_root / '_control_slots'
        slots.mkdir(exist_ok=True)
        for i in range(self.manifest['resources']['max_workers']):
            slot = slots / ('slot_' + str(i) + '.json')
            try:
                with slot.open('xb') as f:
                    f.write(canonical(dict(out=str(self.out), utc=utc(), request=self.request.__dict__)))
                self._slot = slot
                break
            except FileExistsError:
                continue
        require(self._slot is not None, 'Worker concurrency limit reached; stale locks require explicit review, not automatic deletion')
        try:
            self.out.mkdir(parents=True, exist_ok=False)
        except BaseException:
            self.release_slot()
            raise
        self._claimed = True
        self.ledger_path = self.out / 'read_ledger.jsonl'
        for row in self.control_reads:
            self._log(row)
        self.save_json('RUN_CLAIM.json', self.header(dict(command=sys.orig_argv, python=sys.executable,
            base_executable=getattr(sys, '_base_executable', None), request=self.request.__dict__,
            manifest=self.manifest_binding, freeze=self.freeze_binding, approval=self.approval_binding,
            execution_complete=False)))
        if self.request.handoff:
            self._admit_root(self.request.handoff, self.request.handoff_sha256, 'handoff')
        if self.request.seal:
            self._admit_root(self.request.seal, self.request.seal_sha256, 'seal')

    def release_slot(self):
        if self._slot is not None:
            self._slot.unlink(missing_ok=True)
            self._slot = None

    def header(self, content=None):
        answer = dict(manifest_sha256=self.manifest_sha256, freeze_sha256=self.freeze_sha256,
                      approval_sha256=self.approval_sha256, stage=self.request.stage,
                      sequence=self.request.sequence, system=self.request.system, utc=utc())
        answer.update(content or {})
        return answer

    def _log(self, row):
        if self._claimed:
            with self.ledger_path.open('ab') as f:
                f.write(canonical(row) + b'\n')
        else:
            self.control_reads.append(row)

    def assets(self, role=None, sequence=None, system=None):
        return [x for x in self.manifest['assets'] if (role is None or x['role'] == role)
                and x['sequence'] == sequence and x['system'] == system]

    def asset_item(self, role, sequence=None, system=None):
        items = self.assets(role, sequence, system)
        require(len(items) == 1, f'Expected one explicit asset: {role}/{sequence}/{system}, found {len(items)}')
        return items[0]

    def asset(self, role, sequence=None, system=None):
        return self.asset_item(role, sequence, system)['binding']

    def read_bytes(self, path, expected_sha=None, purpose=''):
        self.budget.check('read: ' + purpose)
        p = guarded_path(path, self.ROOT, scope=self.manifest['scope'])
        require(p in self.allowed, 'Path absent from explicit bindings: ' + str(p))
        ref = self.allowed[p]
        require(expected_sha is None or expected_sha == ref['sha256'], 'Caller SHA differs from binding')
        raw = p.read_bytes()
        require(len(raw) == ref['bytes'] and sha_bytes(raw) == ref['sha256'], 'Asset bytes/hash changed: ' + str(p))
        self._log(dict(binding=ref, purpose=purpose, utc=utc()))
        return raw

    read = read_bytes

    def json(self, path, expected_sha=None, purpose=''):
        raw = self.read_bytes(path, expected_sha, purpose)
        doc = json_bytes(raw)
        self.documents[sha_bytes(raw)] = doc
        return doc

    def verified_stream(self, path, expected_sha=None, purpose=''):
        self.budget.check('stream: ' + purpose)
        p = guarded_path(path, self.ROOT, scope=self.manifest['scope'])
        require(p in self.allowed, 'Stream path absent from bindings: ' + str(p))
        ref = self.allowed[p]
        require(expected_sha is None or ref['sha256'] == expected_sha, 'Stream SHA argument differs')
        require(binding_for(p) == ref, 'Stream bytes/hash changed')
        self._log(dict(binding=ref, purpose=purpose, utc=utc()))
        return p

    def register_runtime_tree(self, path, purpose=''):
        p = guarded_path(path, self.ROOT, scope=self.manifest['scope'])
        require(any(p == root or p.is_relative_to(root) for root in self.runtime_roots), 'Runtime root not approved: ' + str(p))
        self._log(dict(runtime_root=str(p), purpose=purpose, utc=utc(), grants_new_data_reads=False))

    def _admit_root(self, path, expected_sha, kind):
        p = guarded_path(path, self.ROOT, scope=self.manifest['scope'])
        require(p.is_relative_to(self.run_root) and not p.is_relative_to(self.out), 'Runtime root must come from a prior stage in this run')
        ref = binding_for(p)
        require(ref['sha256'] == expected_sha, 'Runtime root hash mismatch')
        self._allow(ref)
        doc = self.json(p, expected_sha, 'Explicit ' + kind + ' root')
        require(doc.get('complete') is True and doc.get('manifest_sha256') == self.manifest_sha256
                and doc.get('freeze_sha256') == self.freeze_sha256
                and doc.get('approval_sha256') == self.approval_sha256,
                'Runtime root is incomplete or from a different run/approval contract')
        if kind == 'handoff' and self.request.stage == 'consume':
            require(doc.get('schema') == HANDOFF_SCHEMA and doc.get('stage') == 'export_yolox'
                    and doc.get('sequence') == self.request.sequence and doc.get('system') is None, 'Shared-cache handoff scope differs')
        elif kind == 'handoff':
            require(doc.get('schema') == HANDOFF_SCHEMA and doc.get('stage') == 'collect_receipts'
                    and doc.get('sequence') is None and doc.get('system') is None, 'Seal requires explicit all-unit receipt index')
        else:
            require(doc.get('stage') == 'seal' and doc.get('sequence') is None and doc.get('system') is None,
                    'Score requires whole-run sealed completion')

    def admit_generated(self, binding, parent_sha, purpose='Generated artifact named by verified parent'):
        validate_binding(binding)
        require(parent_sha in self.documents, 'Parent JSON has not been read and verified')
        require(contains_binding(self.documents[parent_sha], binding), 'Binding is not actually listed in verified parent')
        p = guarded_path(binding['path'], self.ROOT, scope=self.manifest['scope'])
        require(p.is_relative_to(self.run_root), 'Generated input escapes this run root')
        self._allow(binding)
        self._log(dict(admitted=binding, parent_sha256=parent_sha, purpose=purpose, utc=utc()))
        return p

    def record_output(self, path, role='output'):
        p = guarded_path(path, self.ROOT, scope=self.manifest['scope'])
        require(self._claimed and p.is_relative_to(self.out) and p != self.out, 'Output outside this exclusive unit')
        require(p.is_file() and not p.is_symlink(), 'Output must be a regular file')
        ref = binding_for(p)
        self._allow(ref)
        self.outputs[str(p)] = dict(role=role, binding=ref)
        return ref

    def save_json(self, name, obj):
        p = self.out / name
        require(p.resolve().is_relative_to(self.out), 'Output JSON path escape')
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('xb') as f:
            f.write(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False).encode('utf-8') + b'\n')
        return self.record_output(p, str(name))

    def complete(self, result):
        require(isinstance(result, dict), 'Worker must return a result mapping')
        require(not (self.out / 'complete.json').exists(), 'Worker must not write runner-owned complete.json')
        self.budget.check('completion')
        self.record_output(self.ledger_path, 'read_ledger')
        size = self.budget.output_check()
        # Keep worker-produced files explicitly named; also include all registered outputs.
        return self.save_json('complete.json', self.header(dict(
            schema='r15_confirmation85_unit_complete_v1', complete=True,
            result=result, files=list(self.outputs.values()), resource_usage=self.budget.fields(),
            whole_run_output_bytes=size, production_technical_completion_only=True,
            scientific_status='PENDING_CLAUDE_RECOMPUTE')))

    def fail(self, exc):
        if self._claimed and not (self.out / 'FAILED.json').exists():
            self.save_json('FAILED.json', self.header(dict(complete=False, error_type=type(exc).__name__,
                error=str(exc), resource_usage=self.budget.fields(), automatic_retry=False)))
