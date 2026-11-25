"""Tests for scripts/adr_snapshot.py, run against throwaway git repositories."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import adr_snapshot  # noqa: E402

CONTRACT = "> Snapshot of the ADRs in [the lock](snapshot.lock.json). ADRs added or changed since bind where they differ.\n\n"


class Repo:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")

    def git(self, *args: str) -> None:
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def write(self, path: str, text: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def commit(self) -> None:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "change")

    def run(self, *args: str) -> tuple[int, str]:
        out = io.StringIO()
        with redirect_stdout(out):
            code = adr_snapshot.main(["--root", str(self.root), *args])
        return code, out.getvalue()

    def lock(self) -> dict:
        return json.loads((self.root / adr_snapshot.DEFAULT_LOCK).read_text(encoding="utf-8"))


class AdrSnapshotTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Repo(Path(self.tmp.name))
        self.repo.write("docs/adr/README.md", "# Catalogue\n")
        self.repo.write("docs/adr/0001-cancel.md", "# Cancel batches\n")
        self.repo.write("docs/adr/0002-logging.md", "# Logging format\n")
        self.repo.write(
            "docs/requirements/batches.md",
            "# Batches\n\n" + CONTRACT + "**Cancel cancels every unfinished item.** Sources: [ADR 0001](../adr/0001-cancel.md#decision).\n",
        )
        self.assertEqual(self.repo.run("init")[0], 0)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def stamp_clean(self) -> None:
        code, out = self.repo.run("stamp", "--na", "docs/adr/0002-logging.md", "engineering only")
        self.assertEqual(code, 0, out)
        self.repo.commit()

    def test_stamp_then_check_is_clean(self) -> None:
        self.stamp_clean()
        code, out = self.repo.run("check")
        self.assertEqual(code, 0, out)
        self.assertIn("ok:", out)
        lock = self.repo.lock()
        self.assertEqual(sorted(lock["adrs"]), ["docs/adr/0001-cancel.md", "docs/adr/0002-logging.md"])
        self.assertEqual(lock["adrs"]["docs/adr/0002-logging.md"]["na"], "engineering only")

    def test_stamp_refuses_uncited_adr_without_reason(self) -> None:
        code, out = self.repo.run("stamp")
        self.assertEqual(code, 1)
        self.assertIn("0002-logging.md: cited by no requirements document", out)
        self.assertEqual(self.repo.lock()["adrs"], {}, "lock must not be written on error")

    def test_na_reason_survives_restamp(self) -> None:
        self.stamp_clean()
        self.assertEqual(self.repo.run("stamp")[0], 0)
        self.assertEqual(self.repo.lock()["adrs"]["docs/adr/0002-logging.md"]["na"], "engineering only")

    def test_new_adr_is_pending_not_failing(self) -> None:
        self.stamp_clean()
        self.repo.write("docs/adr/0003-retry.md", "# Retry\n")
        code, out = self.repo.run("check")
        self.assertEqual(code, 0, out)
        self.assertIn("pending: docs/adr/0003-retry.md is new", out)
        self.assertEqual(self.repo.run("check", "--fail-stale")[0], 2)

    def test_late_lower_number_is_pending(self) -> None:
        self.stamp_clean()
        self.repo.write("docs/adr/0000-early.md", "# Reserved earlier\n")
        self.assertIn("0000-early.md is new", self.repo.run("check")[1])

    def test_amended_adr_names_citing_docs(self) -> None:
        self.stamp_clean()
        self.repo.write("docs/adr/0001-cancel.md", "# Cancel batches\n\n## Amendment\nRunning items too.\n")
        code, out = self.repo.run("check", "--github")
        self.assertEqual(code, 0)
        self.assertIn("0001-cancel.md changed since the last stamp (cited by docs/requirements/batches.md)", out)
        self.assertIn("::warning file=docs/adr/0001-cancel.md::", out)

    def test_line_endings_do_not_count_as_change(self) -> None:
        self.stamp_clean()
        (self.repo.root / "docs/adr/0001-cancel.md").write_bytes(b"# Cancel batches\r\n")
        self.assertIn("ok:", self.repo.run("check")[1])

    def test_deleting_a_live_adr_fails(self) -> None:
        self.stamp_clean()
        (self.repo.root / "docs/adr/0002-logging.md").unlink()
        code, out = self.repo.run("check")
        self.assertEqual(code, 1)
        self.assertIn("only superseded ADRs may be deleted", out)
        code, out = self.repo.run("stamp")
        self.assertEqual(code, 1)
        self.assertIn("deleted without --supersede", out)

    def test_supersede_records_commit_and_passes(self) -> None:
        self.stamp_clean()
        (self.repo.root / "docs/adr/0002-logging.md").unlink()
        code, out = self.repo.run("stamp", "--supersede", "docs/adr/0002-logging.md", "docs/adr/0001-cancel.md")
        self.assertEqual(code, 0, out)
        entry = self.repo.lock()["superseded"]["docs/adr/0002-logging.md"]
        self.assertEqual(entry["by"], "docs/adr/0001-cancel.md")
        self.assertRegex(entry["commit"], r"^[0-9a-f]{40}$")
        self.assertNotIn("docs/adr/0002-logging.md", self.repo.lock()["adrs"])
        self.assertEqual(self.repo.run("check")[0], 0)

    def test_supersede_requires_deleted_file_and_committed_history(self) -> None:
        self.stamp_clean()
        code, out = self.repo.run("stamp", "--supersede", "docs/adr/0002-logging.md", "docs/adr/0001-cancel.md")
        self.assertEqual(code, 1)
        self.assertIn("delete the file", out)
        self.repo.write("docs/adr/0009-never-committed.md", "# Draft\n")
        (self.repo.root / "docs/adr/0009-never-committed.md").unlink()
        code, out = self.repo.run("stamp", "--supersede", "docs/adr/0009-never-committed.md", "docs/adr/0001-cancel.md")
        self.assertEqual(code, 1)
        self.assertIn("not found at HEAD", out)

    def test_superseded_adr_restored_or_cited_fails(self) -> None:
        self.stamp_clean()
        (self.repo.root / "docs/adr/0002-logging.md").unlink()
        self.assertEqual(self.repo.run("stamp", "--supersede", "docs/adr/0002-logging.md", "docs/adr/0001-cancel.md")[0], 0)
        self.repo.write("docs/adr/0002-logging.md", "# Logging format\n")
        code, out = self.repo.run("check")
        self.assertEqual(code, 1)
        self.assertIn("recorded as superseded but still present", out)
        self.assertNotIn("is new", out)

    def test_supersede_target_must_be_live(self) -> None:
        self.stamp_clean()
        (self.repo.root / "docs/adr/0002-logging.md").unlink()
        code, out = self.repo.run("stamp", "--supersede", "docs/adr/0002-logging.md", "docs/adr/0099-missing.md")
        self.assertEqual(code, 1)
        self.assertIn("not a live locked ADR", out)

    def test_link_to_missing_adr_fails(self) -> None:
        self.stamp_clean()
        self.repo.write(
            "docs/requirements/other.md",
            "# Other\n\n" + CONTRACT + "Rule. Sources: [ADR 0042](../adr/0042-gone.md).\n",
        )
        code, out = self.repo.run("check")
        self.assertEqual(code, 1)
        self.assertIn("other.md: links to missing ADR docs/adr/0042-gone.md", out)

    def test_doc_citing_adrs_must_link_lock(self) -> None:
        self.stamp_clean()
        self.repo.write("docs/requirements/other.md", "# Other\n\nRule. Sources: [ADR 0001](../adr/0001-cancel.md).\n")
        code, out = self.repo.run("check")
        self.assertEqual(code, 1)
        self.assertIn("other.md: cites ADRs but does not link the lock file", out)

    def test_cited_adr_losing_its_citation_fails(self) -> None:
        self.stamp_clean()
        self.repo.write("docs/requirements/batches.md", "# Batches\n\nNo sources now.\n")
        code, out = self.repo.run("check")
        self.assertEqual(code, 1)
        self.assertIn("0001-cancel.md: cited by no requirements document", out)

    def test_external_and_anchor_links_are_ignored(self) -> None:
        self.stamp_clean()
        self.repo.write(
            "docs/requirements/batches.md",
            "# Batches\n\n" + CONTRACT + "[old](https://github.com/o/r/blob/abc/docs/adr/0007-old.md) [top](#batches) "
            "[ADR 0001](../adr/0001-cancel.md)\n",
        )
        self.assertEqual(self.repo.run("check")[0], 0)

    def test_malformed_and_missing_lock_fail(self) -> None:
        lock = self.repo.root / adr_snapshot.DEFAULT_LOCK
        lock.write_text("{not json", encoding="utf-8")
        self.assertIn("invalid JSON", self.repo.run("check")[1])
        lock.write_text(json.dumps({"version": 99}), encoding="utf-8")
        self.assertIn("expected \"version\": 1", self.repo.run("check")[1])
        lock.unlink()
        code, out = self.repo.run("check")
        self.assertEqual(code, 1)
        self.assertIn("run `init` first", out)

    def test_init_refuses_to_overwrite(self) -> None:
        code, out = self.repo.run("init")
        self.assertEqual(code, 1)
        self.assertIn("already exists", out)


if __name__ == "__main__":
    unittest.main()
