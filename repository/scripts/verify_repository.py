"""Read-only local release audit; no model imports, data download, or subprocesses."""
import argparse
import ast
import gzip
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROHIBITED_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".mp4", ".avi", ".mov",
                       ".pt", ".pth", ".onnx", ".engine", ".whl", ".zip", ".tar"}
WINDOWS_ABSOLUTE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]")
HOME_ABSOLUTE = re.compile(r"/(?:Users|home)/[^/\s\"']+/")
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def child_path(value):
    p = ROOT / value
    if p.is_symlink() or not p.resolve().is_relative_to(ROOT):
        raise ValueError("Manifest path escapes the repository")
    return p

def audit(forbid_tokens=()):
    findings, emails, hashes = [], [], []
    reviewed_findings = []
    py_count = gzip_count = 0
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT).as_posix()
        if path.is_symlink():
            findings.append({"path": rel, "kind": "symlink"})
            continue
        if not path.is_file():
            continue
        if ".git" in path.parts or "__pycache__" in path.parts:
            findings.append({"path": rel, "kind": "generated_or_git_metadata"})
        raw = path.read_bytes()
        hashes.append({"path": rel, "bytes": len(raw), "sha256": digest(raw)})
        if path.suffix.lower() in PROHIBITED_SUFFIXES or path.name == "gt.txt":
            findings.append({"path": rel, "kind": "excluded_data_or_weight_file"})
        try:
            content = gzip.decompress(raw) if path.suffix == ".gz" else raw
            gzip_count += int(path.suffix == ".gz")
            text = content.decode("utf-8-sig")
        except (UnicodeError, OSError, EOFError):
            findings.append({"path": rel, "kind": "uninspected_non_text"})
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if WINDOWS_ABSOLUTE.search(line) or HOME_ABSOLUTE.search(line):
                findings.append({"path": rel, "line": number, "kind": "absolute_machine_path"})
            # Match a whole identity token, not a digit substring in a coordinate/hash.
            if any(t and re.search(r"(?<![A-Za-z0-9_.])" + re.escape(t) +
                                   r"(?![A-Za-z0-9_.])", line, re.IGNORECASE)
                   for t in forbid_tokens):
                findings.append({"path": rel, "line": number, "kind": "local_identity_token"})
            if EMAIL.search(line):
                emails.append({"path": rel, "line": number, "kind": "email_requires_attribution_review"})
        if path.suffix == ".py":
            py_count += 1
            try:
                ast.parse(text, filename=rel)
            except SyntaxError as error:
                findings.append({"path": rel, "line": error.lineno, "kind": "python_syntax"})
    exceptions_path = ROOT / "metadata/privacy_reviewed_exceptions.json"
    if exceptions_path.exists():
        review = json.loads(exceptions_path.read_text(encoding="utf-8"))
        for exc in review["reviewed"]:
            path = child_path(exc["path"])
            raw = path.read_bytes()
            if digest(raw) != exc["sha256"]:
                findings.append({"path": exc["path"], "kind": "reviewed_exception_hash_changed"})
                continue
            content = gzip.decompress(raw) if path.suffix == ".gz" else raw
            row = json.loads(content.decode("utf-8").splitlines()[exc["line"] - 1])
            for part in exc["json_field_path"]:
                row = row[part]
            if exc["required_type"] != "int" or type(row) is not int:
                raise ValueError("Reviewed numeric-line exception no longer has the verified type")
            match = {"path": exc["path"], "line": exc["line"], "kind": exc["kind"]}
            if match in findings:
                findings.remove(match)
                reviewed_findings.append({**match, "reason": exc["reason"]})
    # Precisely reviewed non-identity synthetic absolute-path test.
    # Preserve existing numeric GT-line exceptions and every hash check.
    synthetic_match = {"path": 'core/tests/test_evidence_seal_round2.py', "line": 102, "kind": "absolute_machine_path"}
    if synthetic_match in findings:
        synthetic_raw = child_path(synthetic_match["path"]).read_bytes()
        if digest(synthetic_raw) == '0e704fffc6e06c12c3592d8c4a9fa70defd1be7d624fe9d15f4e86cc1d4498bd':
            findings.remove(synthetic_match)
            reviewed_findings.append({**synthetic_match, "reason": "Hash-bound intentionally invalid synthetic path; no local identity"})
        else:
            findings.append({"path": synthetic_match["path"], "kind": "reviewed_exception_hash_changed"})
    frozen = ROOT / "FROZEN_CODE_MAP.json"
    frozen_count = 0
    if frozen.exists():
        value = json.loads(frozen.read_text(encoding="utf-8"))
        for item in value["files"]:
            path = child_path(item["repo_path"])
            if not path.is_file():
                findings.append({"path": item["repo_path"], "kind": "missing_frozen_file"})
                continue
            raw = path.read_bytes()
            frozen_count += 1
            if digest(raw) != item["sha256"] or len(raw) != item["bytes"]:
                findings.append({"path": item["repo_path"], "kind": "frozen_hash_mismatch"})
    manifest = ROOT / "MANIFEST.json"
    if manifest.exists():
        declared = json.loads(manifest.read_text(encoding="utf-8"))["files"]
        actual = {x["path"]: x for x in hashes if x["path"] != "MANIFEST.json"}
        for item in declared:
            current = actual.pop(item["path"], None)
            if current != item:
                findings.append({"path": item["path"], "kind": "manifest_mismatch"})
        findings.extend({"path": x, "kind": "not_in_manifest"} for x in actual)
    return {"schema": "github_repo101_readonly_audit_v1",
            "status": "PASS" if not findings else "FAIL",
            "file_count": len(hashes), "total_bytes": sum(x["bytes"] for x in hashes),
            "python_parsed": py_count, "gzip_inspected": gzip_count,
            "frozen_files_verified": frozen_count,
            "manifest_verified": manifest.exists(), "findings": findings,
            "reviewed_non_identity_findings": reviewed_findings,
            "email_manual_review": emails,
            "limits": "Pattern-based scan; third-party attribution must be retained. Not a guarantee of absence of all private information.",
            "files": hashes}

def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--forbid-token", action="append", default=[])
    args = parser.parse_args()
    out = args.report.resolve()
    if out.is_relative_to(ROOT):
        parser.error("Audit output must be outside the repository")
    if out.exists():
        parser.error("Refusing to overwrite an audit report")
    result = audit(args.forbid_token)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8", newline="\n") as file:
        json.dump(result, file, indent=2, ensure_ascii=False)
        file.write("\n")
    summary = {k: v for k, v in result.items()
               if k not in {"files", "findings", "email_manual_review"}}
    summary["finding_count"] = len(result["findings"])
    summary["findings_first_ten"] = result["findings"][:10]
    summary["email_review_count"] = len(result["email_manual_review"])
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())

