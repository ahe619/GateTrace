"""CPU-only CLI adapters around the byte-frozen resource in core/.

Each invocation uses a fresh Python process so the frozen package's historical
top-level src imports cannot collide with the repository's category packages.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

REPOSITORY = Path(__file__).resolve().parents[1]
ENTRIES = frozenset(("reproduce.py", "score_tracker.py", "inspect_event.py"))
PATH_OPTIONS = frozenset(("--gt-root", "--seqinfo-root", "--tracks",
                          "--out", "--images", "--render-out"))
OUTPUT_OPTIONS = frozenset(("--out", "--render-out"))


def external_output(value, repository=REPOSITORY):
    """Require a new runtime destination outside the whole repository."""
    target = Path(value).resolve()
    repository = Path(repository).resolve()
    if target.exists() or target.is_relative_to(repository) or repository.is_relative_to(target):
        raise ValueError("Use a new runtime output directory outside the repository")
    return target


def normalize_arguments(argv, repository=REPOSITORY):
    """Keep scientific flags unchanged; resolve user paths before changing cwd."""
    result = []
    index = 0
    while index < len(argv):
        token = argv[index]
        option, separator, attached = token.partition("=")
        if option not in PATH_OPTIONS:
            if option.startswith("--") and any(name.startswith(option) for name in PATH_OPTIONS):
                raise ValueError("Use the complete path option name: " + option)
            result.append(token)
            index += 1
            continue
        if separator:
            value = attached
        else:
            index += 1
            if index >= len(argv) or argv[index].startswith("--"):
                raise ValueError("Missing path for " + option)
            value = argv[index]
        if not value:
            raise ValueError("Empty path for " + option)
        path = (external_output(value, repository) if option in OUTPUT_OPTIONS
                else Path(value).resolve())
        result.extend((option, str(path)))
        index += 1
    return result


def cpu_environment():
    env = dict(os.environ)
    for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONOPTIMIZE"):
        env.pop(key, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["CUDA_VISIBLE_DEVICES"] = ""
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS"):
        env[key] = "1"
    return env


def build_command(entry, argv, repository=REPOSITORY, executable=None):
    if entry not in ENTRIES:
        raise ValueError("Unknown resource entry")
    return [executable or sys.executable, "-B",
            str(Path(repository).resolve() / "core" / entry)] + normalize_arguments(argv, repository)


def run(entry, argv=None):
    if sys.flags.optimize:
        raise SystemExit("Run without -O: frozen scientific assertions must remain enabled")
    command = build_command(entry, list(sys.argv[1:] if argv is None else argv))
    return subprocess.run(command, cwd=REPOSITORY / "core", env=cpu_environment(),
                          check=False).returncode

