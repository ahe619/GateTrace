"""Content bindings for freshly generated inspector evidence, not scientific QC.

The frozen scorer is unchanged. Its caller writes this seal immediately after
score_tracks returns successfully, then passes the returned digest to Inspector.
An existing unsealed directory is not silently accepted by Inspector. A seal is
an integrity checkpoint, not proof that upstream scoring or labels are correct.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

MANIFEST_NAME = 'inspection_evidence_manifest.json'
SCHEMA = 'inspection_evidence_content_bindings_v1'
FILES = ('complete.json', 'read_ledger.json',
         'MOT20-01_event_matching.json', 'MOT20-01_frame_identity.jsonl.gz',
         'MOT20-02_event_matching.json', 'MOT20-02_frame_identity.jsonl.gz')


def safe_evidence_path(directory, name):
    """Require the named regular file itself, never another resolved member."""
    if name not in FILES + (MANIFEST_NAME,):
        raise ValueError('Unexpected inspector evidence member')
    root = Path(directory).resolve(strict=True)
    requested = root / name
    resolved = requested.resolve(strict=True)
    if resolved != requested or not resolved.is_file():
        raise ValueError('Missing or redirected inspector evidence member: ' + name)
    return resolved


def _digest(value):
    return (isinstance(value, str) and len(value) == 64
            and all(c in '0123456789abcdef' for c in value))


def seal_score_evidence(directory, package_manifest_sha256):
    """Seal a fresh completed score; never overwrite an existing seal.

    Call only in the fresh-scoring producer path. For stored evidence retain the
    original returned digest separately and pass that digest to Inspector. This
    function does not repair, rescore, or authenticate existing scientific data.
    """
    if not _digest(package_manifest_sha256):
        raise ValueError('Fresh evidence must bind the verified package manifest SHA256')
    root = Path(directory).resolve(strict=True)
    target = root / MANIFEST_NAME
    if target.exists() or target.is_symlink():
        raise FileExistsError('Evidence already sealed; refusing to replace seal')
    entries = []
    for name in FILES:
        raw = safe_evidence_path(root, name).read_bytes()
        if name == 'complete.json':
            receipt = json.loads(raw.decode('utf-8'))
            if receipt.get('status') != 'COMPLETE':
                raise ValueError('Cannot seal incomplete scoring evidence')
        entries.append(dict(path=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    payload = dict(schema=SCHEMA, files=entries,
                   package_manifest_sha256=package_manifest_sha256,
                   scientific_qc='not_established_by_integrity_seal',
                   producer_contract='call_immediately_after_frozen_score_tracks_success')
    raw = (json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with target.open('xb') as sink:
        sink.write(raw)
    return dict(path=MANIFEST_NAME, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                files=len(entries))


def load_evidence_bindings(directory, expected_sha256, read, package_manifest_sha256):
    """Read using Inspector's ledger callback, and require an external SHA anchor."""
    if not _digest(expected_sha256):
        raise ValueError('Scoring evidence needs its retained lowercase SHA256 seal anchor')
    raw = read(safe_evidence_path(directory, MANIFEST_NAME), 'score:evidence_seal',
               dict(sha256=expected_sha256))
    manifest = json.loads(raw.decode('utf-8'))
    if manifest.get('schema') != SCHEMA:
        raise ValueError('Unknown inspector evidence seal schema')
    if (not _digest(package_manifest_sha256)
            or manifest.get('package_manifest_sha256') != package_manifest_sha256):
        raise ValueError('Evidence was not sealed for this exact package manifest')
    entries = manifest.get('files')
    if not isinstance(entries, list) or len(entries) != len(FILES):
        raise ValueError('Incomplete inspector evidence seal')
    mapping = {}
    for row in entries:
        if not isinstance(row, dict) or set(row) != {'path', 'bytes', 'sha256'}:
            raise ValueError('Malformed inspector evidence binding')
        name, size, digest = row['path'], row['bytes'], row['sha256']
        if name not in FILES or name in mapping:
            raise ValueError('Duplicate or unexpected inspector evidence binding')
        if (not isinstance(size, int) or isinstance(size, bool) or size < 0
                or not isinstance(digest, str) or len(digest) != 64
                or any(c not in '0123456789abcdef' for c in digest)):
            raise ValueError('Invalid inspector evidence length or digest')
        mapping[name] = row
    if set(mapping) != set(FILES):
        raise ValueError('Missing inspector evidence binding')
    return mapping
