"""Explicit-input I/O for the portable wrappers; no asset discovery or downloads."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import os
import re
import sys

REPO = Path(__file__).resolve().parents[2]
DEVELOPMENT = ("MOT20-01", "MOT20-02")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key: " + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("Nonfinite JSON: " + value)
    return json.loads(Path(path).read_text(encoding="utf-8-sig"),
                      object_pairs_hook=pairs, parse_constant=invalid)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def binding(value):
    require(isinstance(value, dict) and set(value) == {"path", "bytes", "sha256"},
            "Binding requires exactly path, bytes, sha256")
    relative(value["path"])
    require(type(value["bytes"]) is int and value["bytes"] >= 0, "Invalid byte count")
    require(isinstance(value["sha256"], str) and re.fullmatch("[0-9a-f]{64}", value["sha256"]),
            "A full lowercase SHA256 is required")
    return value


def relative(value):
    require(isinstance(value, str) and value and "\\" not in value, "Use a relative POSIX path")
    path = Path(value)
    require(not path.is_absolute() and not value.startswith("/") and not re.match("^[A-Za-z]:", value)
            and ".." not in path.parts and "\x00" not in value, "Path must stay below its manifest")
    return path


def explicit_asset(base, ref):
    binding(ref)
    base = Path(base).resolve()
    path = base / relative(ref["path"])
    require(path.resolve().is_relative_to(base), "Asset escapes manifest directory")
    for part in (path, *path.parents):
        if part == base:
            break
        require(not part.is_symlink(), "Asset symlinks are not accepted")
    require(path.is_file() and path.stat().st_size == ref["bytes"], "Asset size differs: " + ref["path"])
    require(sha(path) == ref["sha256"], "Asset SHA differs: " + ref["path"])
    return path


def new_output(value):
    path = Path(value).resolve()
    require(not path.is_relative_to(REPO), "Runtime outputs must be outside the repository")
    require(not path.exists(), "Output exists; never overwrite")
    return path


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write("\n")


def development(sequence):
    require(sequence in DEVELOPMENT, "This portable execution wrapper permits development 01/02 only")


def verify_frozen(prefix):
    require(sys.flags.optimize == 0, "Do not use Python -O/-OO; frozen scientific assertions must remain enabled")
    rows = load_json(REPO / "metadata/pipeline_frozen_map.json")["files"]
    selected = [row for row in rows if row["repo_path"].startswith(prefix)]
    require(selected, "No frozen binding for " + prefix)
    for row in selected:
        path = REPO / row["repo_path"]
        require(path.stat().st_size == row["bytes"] and sha(path) == row["sha256"],
                "Frozen source differs: " + row["repo_path"])
    return selected


def fragment_namespace(source_filename, namespace=None):
    """Compile only hash-bound, unchanged physical source slices approved for publication."""
    require(sys.flags.optimize == 0, "Do not use Python -O/-OO")
    rows = load_json(REPO / "metadata/pipeline_frozen_map.json")["fragments"]
    selected = [r for r in rows if r["source_project_path"] == "scripts/" + source_filename]
    require(selected, "No approved node slices for " + source_filename)
    namespace = {} if namespace is None else namespace
    for row in selected:
        raw = (REPO / row["repo_path"]).read_bytes()
        require(len(raw) == row["excerpt_bytes"] and hashlib.sha256(raw).hexdigest() == row["excerpt_sha256"],
                "Approved source node differs: " + row["repo_path"])
        exec(compile(raw, row["repo_path"], "exec"), namespace)
    return namespace


def activate_frozen(prefix):
    verify_frozen(prefix + "/")
    directory = str(REPO / prefix)
    if directory not in sys.path:
        sys.path.insert(0, directory)


def frozen_module(relative_path, name):
    verify_frozen(relative_path)
    path = REPO / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def offline_runtime():
    os.environ["YOLO_AUTOINSTALL"] = "false"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True
    def audit(event, args):
        if event in ("socket.connect", "socket.getaddrinfo", "subprocess.Popen", "os.system"):
            raise PermissionError("Offline wrapper forbids network/install/subprocess: " + event)
    sys.addaudithook(audit)


def runtime_directories(output):
    """Put mutable library caches below the caller's new external output."""
    output = Path(output)
    for key, leaf in {"TEMP": "tmp", "TMP": "tmp", "TMPDIR": "tmp",
                      "YOLO_CONFIG_DIR": "yolo", "TORCH_HOME": "torch",
                      "XDG_CACHE_HOME": "cache", "MPLCONFIGDIR": "mpl",
                      "NUMBA_CACHE_DIR": "numba", "CUDA_CACHE_PATH": "cuda"}.items():
        path = output / "runtime" / leaf
        path.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(path)


def finite_positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0
