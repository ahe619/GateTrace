"""Only new synthetic fixtures; no assumptions about the author's checkout."""
import os
from pathlib import Path


def scratch_parent():
    package = Path(__file__).resolve().parents[1]
    configured = os.environ.get('INSPECTOR_TEST_SCRATCH')
    root = (Path(configured) if configured else Path.cwd()/'.inspector_synthetic_scratch').resolve()
    if root.is_relative_to(package):
        if configured:
            raise ValueError('Synthetic scratch must be outside the source package')
        root = package.parent/'.inspector_synthetic_scratch'
    root.mkdir(parents=True, exist_ok=True)
    return root
