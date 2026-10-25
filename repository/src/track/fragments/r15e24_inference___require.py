def _require(value, message):
    if not value:
        raise RuntimeError(message)
