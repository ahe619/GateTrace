def _register_packages(reader, names):
    import importlib.util
    from pathlib import Path
    refs = {}
    for name in names:
        spec = importlib.util.find_spec(name)
        _require(spec is not None and spec.origin is not None,
                 'Required installed package missing; installation forbidden: ' + name)
        package = Path(spec.origin).resolve().parent
        reader.register_runtime_tree(package, purpose='Existing read-only package for MOT20 worker: ' + name)
        refs[name] = str(package)
    return refs
