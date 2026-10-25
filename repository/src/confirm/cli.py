"""Generate frozen confirmation commands only. This wrapper has no execution action."""
import argparse
import json
from pathlib import Path
import stat
import subprocess
import sys
from src.detect.io import REPO, relative, require, verify_frozen


def deployment_path(workspace, target):
    """Reject redirected deployment components before any code file is written."""
    workspace, target = Path(workspace).resolve(), Path(target)
    require(target.resolve().is_relative_to(workspace) and not target.resolve().is_relative_to(REPO),
            "Confirmation deployment must stay in the external workspace")
    require(target.is_relative_to(workspace), "Deployment path must be below workspace")
    for component in (target, *target.parents):
        if component == workspace:
            break
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode)
                and not (getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)),
                "Confirmation deployment rejects symlink/junction/reparse components")
    return target


def generate_workspace(workspace, manifest, manifest_sha, approval, approval_sha, out):
    """Relocate the original control plane byte-for-byte, preserving its real path guard."""
    workspace = Path(workspace).resolve()
    require(not workspace.is_relative_to(REPO), "Confirmation workspace must be outside the repository")
    manifest, approval, out = [Path(value).as_posix() for value in (manifest, approval, out)]
    for value in (manifest, approval, out):
        relative(value)
    source_rows = verify_frozen("src/confirm/production_v1/")
    destination = deployment_path(workspace, workspace / "scripts/confirmation85/production_v1")
    destination.mkdir(parents=True, exist_ok=True)
    deployment_path(workspace, destination)
    for row in source_rows:
        raw = (REPO / row["repo_path"]).read_bytes()
        target = deployment_path(workspace, destination / Path(row["repo_path"]).name)
        if target.exists():
            require(target.read_bytes() == raw, "Existing workspace control source differs")
        else:
            with target.open("xb") as stream:
                stream.write(raw)
    # This invokes only the original command generator, never run.py or a worker.
    completed = subprocess.run([sys.executable, "-I", "-S", "-B", str(destination / "command.py"), "generate",
        "--manifest", str(manifest), "--manifest-sha256", manifest_sha,
        "--approval", str(approval), "--approval-sha256", approval_sha, "--out", str(out)],
        cwd=workspace, check=True, capture_output=True, text=True)
    return json.loads((workspace / str(out) / "commands.json").read_text(encoding="utf-8")), completed.stdout


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", type=Path, required=True, help="Explicit external workspace; control/output paths are relative to it")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--manifest-sha256", required=True)
    p.add_argument("--approval", type=Path, required=True)
    p.add_argument("--approval-sha256", required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args(argv)
    result, _ = generate_workspace(a.workspace, a.manifest, a.manifest_sha256, a.approval, a.approval_sha256, a.out)
    print(result["status"])
    print("Command generation only; no asset, approval, or scientific stage was executed.")
    return 0
