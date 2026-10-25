def _bound_bytes(reader, path, sha, purpose):
    import hashlib
    from pathlib import Path
    p = Path(path).resolve()
    data = reader.read(p, expected_sha=sha, purpose=purpose)
    _require(isinstance(data, bytes), 'reader.read must return bytes')
    actual = hashlib.sha256(data).hexdigest()
    _require(sha is None or actual == sha, 'Input SHA mismatch: ' + str(p))
    return data, dict(path=str(p), bytes=len(data), sha256=actual)
