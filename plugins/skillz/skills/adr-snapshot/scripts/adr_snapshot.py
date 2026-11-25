#!/usr/bin/env python3
"""Lock a requirements snapshot to the ADRs it restates, and check it mechanically.

The lock file records every ADR the requirements were reconciled against, by
content hash. It replaces hand-maintained markers, checked revisions and
freshness policies: the script computes what is stale, and CI enforces that the
lock is consistent.

Commands (run from anywhere inside the repository, or pass --root):

  init     Create the lock file with the ADR and requirements globs.
  stamp    Re-hash every ADR and rewrite the lock. Run after reconciling.
             --na PATH REASON       record an ADR that no requirement needs to cite
             --supersede OLD NEW    record a deleted ADR fully replaced by NEW
  check    Verify the lock against the tree. Report ADRs added or changed since
           the last stamp ("pending"); these bind where they differ from the
           requirements.
             --fail-stale           exit 2 when anything is pending
             --github               also print GitHub Actions annotations

Lock format (JSON, version 1):

  {
    "version": 1,
    "script_version": "0.5.0",
    "adr_glob": "docs/adr/[0-9]*.md",
    "requirements_glob": "docs/requirements/*.md",
    "adrs": {"docs/adr/0042-x.md": {"sha256": "...", "na": "optional reason"}},
    "superseded": {"docs/adr/0007-y.md": {"by": "docs/adr/0042-x.md", "commit": "<sha>"}}
  }

Rules check enforces (exit 1 on any):

  - the lock exists, parses, and has a known version and both globs;
  - the lock was not written by a newer copy of this script (stamp
    refuses too); a lock with no script_version is accepted;
  - every locked ADR still exists, unless it is recorded as superseded;
  - every ADR in the tree that is in the lock is cited by a requirements
    document or has an "na" reason;
  - a superseded ADR is absent from the tree, is cited by no requirements
    document, and names a replacement that is locked and not itself superseded;
  - every link from a requirements document into the ADR directory resolves;
  - every requirements document that cites an ADR links to the lock file.

Hashes ignore line-ending differences. Requires Python 3.9+ and, for
--supersede, git. No third-party packages.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

LOCK_VERSION = 1
SCRIPT_VERSION = "0.5.0"
DEFAULT_LOCK = "docs/requirements/snapshot.lock.json"
DEFAULT_ADR_GLOB = "docs/adr/[0-9]*.md"
DEFAULT_REQUIREMENTS_GLOB = "docs/requirements/*.md"
LINK_RE = re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")


class LockError(Exception):
    pass


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    changed: dict[str, list[str]] = field(default_factory=dict)

    @property
    def pending(self) -> bool:
        return bool(self.added or self.changed)


def repo_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        return Path(out)
    except (OSError, subprocess.CalledProcessError):
        return Path.cwd()


def digest(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def parse_version(value: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in value.split("."))
    except (AttributeError, ValueError) as exc:
        raise LockError(f"unrecognised script_version {value!r}") from exc


def load_lock(path: Path) -> dict:
    if not path.is_file():
        raise LockError(f"{path.name}: lock file not found; run `init` first")
    try:
        lock = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LockError(f"{path.name}: invalid JSON: {exc}") from exc
    if not isinstance(lock, dict) or lock.get("version") != LOCK_VERSION:
        raise LockError(f"{path.name}: expected \"version\": {LOCK_VERSION}")
    written_by = lock.get("script_version")
    if written_by is not None and parse_version(written_by) > parse_version(SCRIPT_VERSION):
        raise LockError(
            f"{path.name}: written by adr_snapshot.py {written_by}; "
            f"update this copy (it is {SCRIPT_VERSION}) from the adr-snapshot skill"
        )
    for key in ("adr_glob", "requirements_glob"):
        if not isinstance(lock.get(key), str) or not lock[key]:
            raise LockError(f"{path.name}: missing \"{key}\"")
    for key in ("adrs", "superseded"):
        lock.setdefault(key, {})
        if not isinstance(lock[key], dict):
            raise LockError(f"{path.name}: \"{key}\" must be an object")
    for name, entry in lock["adrs"].items():
        if not isinstance(entry, dict) or not isinstance(entry.get("sha256"), str):
            raise LockError(f"{path.name}: adrs[{name}] needs a sha256")
    for name, entry in lock["superseded"].items():
        if not isinstance(entry, dict) or not entry.get("by") or not entry.get("commit"):
            raise LockError(f"{path.name}: superseded[{name}] needs \"by\" and \"commit\"")
    return lock


def write_lock(path: Path, lock: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = {
        "version": LOCK_VERSION,
        "script_version": SCRIPT_VERSION,
        "adr_glob": lock["adr_glob"],
        "requirements_glob": lock["requirements_glob"],
        "adrs": dict(sorted(lock["adrs"].items())),
        "superseded": dict(sorted(lock["superseded"].items())),
    }
    path.write_text(json.dumps(ordered, indent=2) + "\n", encoding="utf-8")


def tree_adrs(root: Path, lock: dict) -> dict[str, str]:
    return {rel(root, p): digest(p) for p in sorted(root.glob(lock["adr_glob"])) if p.is_file()}


def adr_dir(lock: dict) -> PurePosixPath:
    parts = PurePosixPath(lock["adr_glob"]).parts
    fixed = [p for p in parts[:-1] if not any(c in p for c in "*?[")]
    return PurePosixPath(*fixed) if fixed else PurePosixPath(".")


def resolve_link(root: Path, doc: Path, target: str) -> str | None:
    if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
        return None
    target = target.split("#", 1)[0]
    if not target:
        return None
    base = root if target.startswith("/") else doc.parent
    resolved = Path(os.path.normpath(base / target.lstrip("/")))
    try:
        return rel(root, resolved)
    except ValueError:
        return None


def scan_requirements(root: Path, lock: dict, lock_path: Path) -> tuple[dict[str, list[str]], list[str]]:
    """Return {adr path: [citing docs]} and structural errors in the requirements."""
    adr_base = adr_dir(lock).as_posix()
    lock_rel = rel(root, lock_path)
    citations: dict[str, list[str]] = {}
    errors: list[str] = []
    for doc in sorted(root.glob(lock["requirements_glob"])):
        if not doc.is_file():
            continue
        doc_rel = rel(root, doc)
        cites_adr = links_lock = False
        for target in LINK_RE.findall(doc.read_text(encoding="utf-8")):
            path = resolve_link(root, doc, target)
            if path is None:
                continue
            if path == lock_rel:
                links_lock = True
            elif adr_base == "." or path.startswith(adr_base + "/"):
                if not path.endswith(".md"):
                    continue
                if not (root / path).is_file():
                    errors.append(f"{doc_rel}: links to missing ADR {path}")
                    continue
                cites_adr = True
                citations.setdefault(path, [])
                if doc_rel not in citations[path]:
                    citations[path].append(doc_rel)
        if cites_adr and not links_lock:
            errors.append(f"{doc_rel}: cites ADRs but does not link the lock file {lock_rel}")
    return citations, errors


def check(root: Path, lock_path: Path) -> Report:
    report = Report()
    try:
        lock = load_lock(lock_path)
    except LockError as exc:
        report.errors.append(str(exc))
        return report
    tree = tree_adrs(root, lock)
    citations, doc_errors = scan_requirements(root, lock, lock_path)
    report.errors.extend(doc_errors)
    locked, superseded = lock["adrs"], lock["superseded"]

    for path, entry in locked.items():
        if path in superseded:
            report.errors.append(f"{path}: listed as both locked and superseded")
        elif path not in tree:
            report.errors.append(f"{path}: locked ADR is missing; only superseded ADRs may be deleted (stamp --supersede)")
        elif not citations.get(path) and not entry.get("na"):
            report.errors.append(f"{path}: cited by no requirements document and has no \"na\" reason")

    for path, entry in superseded.items():
        if path in tree:
            report.errors.append(f"{path}: recorded as superseded but still present; delete it")
        for doc in citations.get(path, []):
            report.errors.append(f"{doc}: cites superseded ADR {path}; cite {entry['by']} instead")
        by = entry["by"]
        if by in superseded or by not in locked:
            report.errors.append(f"{path}: superseded by {by}, which is not a live locked ADR")

    for path, sha in tree.items():
        if path in superseded:
            continue
        if path not in locked:
            report.added.append(path)
        elif locked[path]["sha256"] != sha:
            report.changed[path] = citations.get(path, [])
    return report


def git_commit_with(root: Path, path: str) -> str:
    try:
        sha = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        subprocess.run(
            ["git", "-C", str(root), "cat-file", "-e", f"{sha}:{path}"],
            check=True, capture_output=True,
        )
        return sha
    except (OSError, subprocess.CalledProcessError) as exc:
        raise LockError(f"{path}: not found at HEAD; commit it before deleting so history keeps it") from exc


def stamp(root: Path, lock_path: Path, na: list[list[str]], supersede: list[list[str]]) -> Report:
    lock = load_lock(lock_path)
    tree = tree_adrs(root, lock)
    old = lock["adrs"]
    for old_path, by in supersede:
        if old_path in tree:
            raise LockError(f"{old_path}: delete the file before recording it as superseded")
        lock["superseded"][old_path] = {"by": by, "commit": git_commit_with(root, old_path)}
    reasons = {path: entry["na"] for path, entry in old.items() if entry.get("na")}
    for path, reason in na:
        if path not in tree:
            raise LockError(f"{path}: --na names an ADR that is not in the tree")
        reasons[path] = reason.strip()
    missing = [p for p in old if p not in tree and p not in lock["superseded"]]
    if missing:
        raise LockError("ADRs deleted without --supersede: " + ", ".join(missing))
    new = {}
    for path, sha in tree.items():
        if path in lock["superseded"]:
            continue
        new[path] = {"sha256": sha}
        if reasons.get(path):
            new[path]["na"] = reasons[path]
    lock["adrs"] = new
    previous = lock_path.read_text(encoding="utf-8")
    write_lock(lock_path, lock)
    report = check(root, lock_path)
    if report.errors:
        lock_path.write_text(previous, encoding="utf-8")
    return report


def init(root: Path, lock_path: Path, adr_glob: str, requirements_glob: str) -> None:
    if lock_path.exists():
        raise LockError(f"{rel(root, lock_path)} already exists")
    write_lock(lock_path, {
        "adr_glob": adr_glob, "requirements_glob": requirements_glob,
        "adrs": {}, "superseded": {},
    })


def print_report(report: Report, github: bool) -> None:
    for error in report.errors:
        print(f"error: {error}")
        if github:
            print(f"::error::{error}")
    for path in report.added:
        line = f"pending: {path} is new since the last stamp; it binds where it differs from the requirements"
        print(line)
        if github:
            print(f"::warning file={path}::{line}")
    for path, docs in report.changed.items():
        cited = ", ".join(docs) if docs else "no requirements document"
        line = f"pending: {path} changed since the last stamp (cited by {cited})"
        print(line)
        if github:
            print(f"::warning file={path}::{line}")
    if not report.errors and not report.pending:
        print("ok: requirements snapshot covers every ADR")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", help="repository root (default: git top level)")
    parser.add_argument("--lock", default=DEFAULT_LOCK, help=f"lock path from the root (default: {DEFAULT_LOCK})")
    sub = parser.add_subparsers(dest="command", required=True)
    p_init = sub.add_parser("init")
    p_init.add_argument("--adrs", default=DEFAULT_ADR_GLOB)
    p_init.add_argument("--requirements", default=DEFAULT_REQUIREMENTS_GLOB)
    p_stamp = sub.add_parser("stamp")
    p_stamp.add_argument("--na", nargs=2, action="append", default=[], metavar=("PATH", "REASON"))
    p_stamp.add_argument("--supersede", nargs=2, action="append", default=[], metavar=("OLD", "NEW"))
    p_check = sub.add_parser("check")
    p_check.add_argument("--fail-stale", action="store_true")
    p_check.add_argument("--github", action="store_true")
    args = parser.parse_args(argv)

    root = repo_root(args.root)
    lock_path = root / args.lock
    try:
        if args.command == "init":
            init(root, lock_path, args.adrs, args.requirements)
            print(f"created {args.lock}")
            return 0
        if args.command == "stamp":
            report = stamp(root, lock_path, args.na, args.supersede)
            print_report(report, False)
            if report.errors:
                print("lock not written; fix the errors above and stamp again")
                return 1
            return 0
        report = check(root, lock_path)
    except LockError as exc:
        print(f"error: {exc}")
        return 1
    print_report(report, args.github)
    if report.errors:
        return 1
    return 2 if args.fail_stale and report.pending else 0


if __name__ == "__main__":
    sys.exit(main())
