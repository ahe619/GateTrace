def _load_adapter(reader, filename, sha):
    import types
    path = _root() / 'scripts' / filename
    data, ref = _bound_bytes(reader, path, sha, 'Read pinned reusable detector/tracker adapter')
    module = types.ModuleType('_r15e24_pinned_' + path.stem)
    module.__file__ = str(path)
    # Pinned wrappers have no top-level model, data, or configuration reads.
    exec(compile(data, str(path), 'exec'), module.__dict__)
    return module, ref
