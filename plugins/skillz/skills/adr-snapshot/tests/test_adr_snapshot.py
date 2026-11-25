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

PLUGIN_VERSION = json.loads(
    (Path(__file__).resolve().parents[3] / "plugin.json").read_text(encoding="utf-8")
)["version"]

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
        self.assertIn("deleted without being recorded as superseded", out)

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
        self.assertIn("not found in git history", out)

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
        self.assertIn("not a live ADR", out)

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

    def test_stamp_records_the_released_script_version(self) -> None:
        self.stamp_clean()
        self.assertEqual(self.repo.lock()["script_version"], PLUGIN_VERSION)

    def set_lock_field(self, key: str, value: object) -> None:
        lock = self.repo.lock()
        if value is None:
            lock.pop(key, None)
        else:
            lock[key] = value
        (self.repo.root / adr_snapshot.DEFAULT_LOCK).write_text(json.dumps(lock), encoding="utf-8")

    def test_check_fails_on_lock_from_newer_script(self) -> None:
        self.stamp_clean()
        self.set_lock_field("script_version", "99.0.0")
        code, out = self.repo.run("check")
        self.assertEqual(code, 1)
        self.assertIn("written by adr_snapshot.py 99.0.0", out)
        self.assertIn(f"update this copy (it is {PLUGIN_VERSION})", out)

    def test_stamp_refuses_lock_from_newer_script(self) -> None:
        self.stamp_clean()
        self.set_lock_field("script_version", "99.0.0")
        before = (self.repo.root / adr_snapshot.DEFAULT_LOCK).read_text(encoding="utf-8")
        code, out = self.repo.run("stamp")
        self.assertEqual(code, 1)
        self.assertIn("written by adr_snapshot.py 99.0.0", out)
        self.assertEqual((self.repo.root / adr_snapshot.DEFAULT_LOCK).read_text(encoding="utf-8"), before)

    def test_unversioned_lock_is_accepted_and_upgraded_by_stamp(self) -> None:
        self.stamp_clean()
        self.set_lock_field("script_version", None)
        code, out = self.repo.run("check")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.repo.run("stamp")[0], 0)
        self.assertEqual(self.repo.lock()["script_version"], PLUGIN_VERSION)

    def test_malformed_script_version_fails(self) -> None:
        self.stamp_clean()
        self.set_lock_field("script_version", "latest")
        code, out = self.repo.run("check")
        self.assertEqual(code, 1)
        self.assertIn("unrecognised script_version 'latest'", out)

    def test_superseding_a_replacement_repoints_the_chain(self) -> None:
        self.stamp_clean()
        (self.repo.root / "docs/adr/0002-logging.md").unlink()
        self.assertEqual(self.repo.run("stamp", "--supersede", "docs/adr/0002-logging.md", "docs/adr/0001-cancel.md")[0], 0)
        self.repo.commit()
        first_commit = self.repo.lock()["superseded"]["docs/adr/0002-logging.md"]["commit"]
        self.repo.write("docs/adr/0003-cancel-v2.md", "# Cancel v2\n")
        self.repo.write(
            "docs/requirements/batches.md",
            "# Batches\n\n" + CONTRACT + "Rule. Sources: [ADR 0003](../adr/0003-cancel-v2.md).\n",
        )
        self.repo.commit()
        (self.repo.root / "docs/adr/0001-cancel.md").unlink()
        code, out = self.repo.run("stamp", "--supersede", "docs/adr/0001-cancel.md", "docs/adr/0003-cancel-v2.md")
        self.assertEqual(code, 0, out)
        superseded = self.repo.lock()["superseded"]
        self.assertEqual(superseded["docs/adr/0002-logging.md"]["by"], "docs/adr/0003-cancel-v2.md")
        self.assertEqual(superseded["docs/adr/0002-logging.md"]["commit"], first_commit)
        self.assertEqual(superseded["docs/adr/0001-cancel.md"]["by"], "docs/adr/0003-cancel-v2.md")

    def test_link_to_superseded_adr_is_pending_and_blocks_stamp(self) -> None:
        self.stamp_clean()
        (self.repo.root / "docs/adr/0002-logging.md").unlink()
        self.assertEqual(self.repo.run("stamp", "--supersede", "docs/adr/0002-logging.md", "docs/adr/0001-cancel.md")[0], 0)
        self.repo.write(
            "docs/requirements/other.md",
            "# Other\n\n" + CONTRACT + "Rule. Sources: [ADR 0002](../adr/0002-logging.md).\n",
        )
        message = "other.md: cites superseded ADR docs/adr/0002-logging.md; cite docs/adr/0001-cancel.md instead"
        code, out = self.repo.run("check")
        self.assertEqual(code, 0, out)
        self.assertIn(f"pending: docs/requirements/{message}", out)
        self.assertNotIn("links to missing ADR", out)
        self.assertEqual(self.repo.run("check", "--fail-stale")[0], 2)
        code, out = self.repo.run("stamp")
        self.assertEqual(code, 1)
        self.assertIn(f"error: docs/requirements/{message}", out)

    def supersede_cited_adr(self) -> None:
        """Lock 0001 (cited) and 0002, add a pending 0003, then move 0001 out of the glob."""
        self.stamp_clean()
        self.repo.write("docs/adr/0003-cancel-v2.md", "# Cancel v2\n")
        self.repo.write("docs/adr/0002-logging.md", "# Logging format, amended\n")
        self.repo.commit()
        self.repo.git("mv", "docs/adr/0001-cancel.md", "docs/adr/superseded-0001-cancel.md")

    def test_supersede_records_only_the_supersession(self) -> None:
        self.supersede_cited_adr()
        before = self.repo.lock()
        code, out = self.repo.run("supersede", "docs/adr/0001-cancel.md", "docs/adr/0003-cancel-v2.md")
        self.assertEqual(code, 0, out)
        lock = self.repo.lock()
        self.assertEqual(lock["superseded"]["docs/adr/0001-cancel.md"]["by"], "docs/adr/0003-cancel-v2.md")
        self.assertRegex(lock["superseded"]["docs/adr/0001-cancel.md"]["commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(lock["adrs"], {k: v for k, v in before["adrs"].items() if k != "docs/adr/0001-cancel.md"})
        code, out = self.repo.run("check")
        self.assertEqual(code, 0, out)
        self.assertIn("pending: docs/adr/0003-cancel-v2.md is new", out)
        self.assertIn("pending: docs/adr/0002-logging.md changed", out)
        self.assertIn("pending: docs/requirements/batches.md: cites superseded ADR docs/adr/0001-cancel.md", out)

    def test_supersede_finds_the_commit_before_a_committed_move(self) -> None:
        self.supersede_cited_adr()
        self.repo.commit()
        code, out = self.repo.run("supersede", "docs/adr/0001-cancel.md", "docs/adr/0003-cancel-v2.md")
        self.assertEqual(code, 0, out)
        sha = self.repo.lock()["superseded"]["docs/adr/0001-cancel.md"]["commit"]
        subprocess.run(["git", "-C", str(self.repo.root), "cat-file", "-e", f"{sha}:docs/adr/0001-cancel.md"], check=True)

    def test_supersede_refuses_what_it_cannot_record(self) -> None:
        self.supersede_cited_adr()
        cases = [
            (("docs/adr/0002-logging.md", "docs/adr/0003-cancel-v2.md"), "delete the file"),
            (("docs/adr/0001-cancel.md", "docs/adr/0099-missing.md"), "not a live ADR"),
            (("docs/adr/0042-never-locked.md", "docs/adr/0003-cancel-v2.md"), "not in the lock"),
        ]
        before = self.repo.lock()
        for args, message in cases:
            code, out = self.repo.run("supersede", *args)
            self.assertEqual(code, 1, args)
            self.assertIn(message, out)
            self.assertEqual(self.repo.lock(), before)

    def test_stamp_prints_what_it_records(self) -> None:
        self.stamp_clean()
        self.repo.write("docs/adr/0003-cancel-v2.md", "# Cancel v2\n")
        code, out = self.repo.run("stamp", "--na", "docs/adr/0003-cancel-v2.md", "process")
        self.assertEqual(code, 0, out)
        self.assertIn("recorded: docs/adr/0003-cancel-v2.md", out)
        self.assertNotIn("recorded: docs/adr/0001-cancel.md", out)

    def test_leave_pending_keeps_an_adr_pending_through_a_stamp(self) -> None:
        self.stamp_clean()
        before = self.repo.lock()["adrs"]["docs/adr/0001-cancel.md"]
        self.repo.write("docs/adr/0001-cancel.md", "# Cancel batches, amended\n")
        self.repo.write("docs/adr/0003-cancel-v2.md", "# Cancel v2\n")
        code, out = self.repo.run(
            "stamp", "--leave-pending", "docs/adr/0001-cancel.md", "--leave-pending", "docs/adr/0003-cancel-v2.md",
        )
        self.assertEqual(code, 0, out)
        self.assertNotIn("recorded:", out)
        lock = self.repo.lock()["adrs"]
        self.assertEqual(lock["docs/adr/0001-cancel.md"], before)
        self.assertNotIn("docs/adr/0003-cancel-v2.md", lock)
        code, out = self.repo.run("check")
        self.assertIn("pending: docs/adr/0001-cancel.md changed", out)
        self.assertIn("pending: docs/adr/0003-cancel-v2.md is new", out)
        code, out = self.repo.run("stamp", "--leave-pending", "docs/adr/0099-missing.md")
        self.assertEqual(code, 1)
        self.assertIn("--leave-pending names an ADR that is not in the tree", out)

    def test_link_into_superseded_directory_is_pending_and_blocks_stamp(self) -> None:
        (self.repo.root / adr_snapshot.DEFAULT_LOCK).unlink()
        self.assertEqual(self.repo.run("init", "--superseded", "docs/adr/superseded/[0-9]*.md")[0], 0)
        self.assertEqual(self.repo.lock()["superseded_glob"], "docs/adr/superseded/[0-9]*.md")
        self.stamp_clean()
        self.assertEqual(self.repo.lock()["superseded_glob"], "docs/adr/superseded/[0-9]*.md")
        self.repo.write("docs/adr/superseded/0000-old.md", "# Old\n")
        self.repo.write(
            "docs/requirements/other.md",
            "# Other\n\n" + CONTRACT + "Rule. Sources: [ADR 0000](../adr/superseded/0000-old.md), "
            "[ADR 0004](../adr/superseded/0004-gone.md).\n",
        )
        code, out = self.repo.run("check")
        self.assertEqual(code, 1)
        self.assertIn("other.md: links to missing ADR docs/adr/superseded/0004-gone.md", out)
        self.assertIn("pending: docs/requirements/other.md: cites superseded ADR docs/adr/superseded/0000-old.md", out)
        self.repo.write(
            "docs/requirements/other.md",
            "# Other\n\nRule. Sources: [ADR 0000](../adr/superseded/0000-old.md).\n",
        )
        code, out = self.repo.run("check")
        self.assertEqual(code, 1)
        self.assertIn("other.md: cites ADRs but does not link the lock file", out)
        self.repo.write(
            "docs/requirements/other.md",
            "# Other\n\n" + CONTRACT + "Rule. Sources: [ADR 0000](../adr/superseded/0000-old.md).\n",
        )
        self.assertEqual(self.repo.run("check")[0], 0)
        code, out = self.repo.run("stamp", "--na", "docs/adr/0002-logging.md", "engineering only")
        self.assertEqual(code, 1)
        self.assertIn("error: docs/requirements/other.md: cites superseded ADR", out)

    def test_supersede_records_several_pairs_at_once(self) -> None:
        self.supersede_cited_adr()
        self.repo.write("docs/adr/0004-logging-v2.md", "# Logging v2\n")
        self.repo.commit()
        (self.repo.root / "docs/adr/0002-logging.md").unlink()
        code, out = self.repo.run(
            "supersede", "docs/adr/0001-cancel.md", "docs/adr/0003-cancel-v2.md",
            "docs/adr/0002-logging.md", "docs/adr/0004-logging-v2.md",
        )
        self.assertEqual(code, 0, out)
        self.assertEqual(sorted(self.repo.lock()["superseded"]), ["docs/adr/0001-cancel.md", "docs/adr/0002-logging.md"])
        code, out = self.repo.run("supersede", "docs/adr/0001-cancel.md")
        self.assertEqual(code, 1)
        self.assertIn("OLD NEW pairs", out)

    def test_stamp_records_a_chain_in_one_run(self) -> None:
        self.stamp_clean()
        self.repo.write("docs/adr/0003-cancel-v2.md", "# Cancel v2\n")
        self.repo.write(
            "docs/requirements/batches.md",
            "# Batches\n\n" + CONTRACT + "Rule. Sources: [ADR 0003](../adr/0003-cancel-v2.md).\n",
        )
        (self.repo.root / "docs/adr/0001-cancel.md").unlink()
        (self.repo.root / "docs/adr/0002-logging.md").unlink()
        code, out = self.repo.run(
            "stamp", "--supersede", "docs/adr/0002-logging.md", "docs/adr/0001-cancel.md",
            "--supersede", "docs/adr/0001-cancel.md", "docs/adr/0003-cancel-v2.md",
            "--na", "docs/adr/0003-cancel-v2.md", "unused",
        )
        self.assertEqual(code, 0, out)
        superseded = self.repo.lock()["superseded"]
        self.assertEqual(superseded["docs/adr/0002-logging.md"]["by"], "docs/adr/0003-cancel-v2.md")
        self.assertEqual(superseded["docs/adr/0001-cancel.md"]["by"], "docs/adr/0003-cancel-v2.md")

    def test_pending_proposed_adr_binds_nothing(self) -> None:
        self.stamp_clean()
        self.repo.write("docs/adr/0003-draft.md", "# Draft\n\nStatus: proposed\n")
        self.repo.write("docs/adr/0004-taken.md", "# Taken\n\nStatus: accepted\n")
        code, out = self.repo.run("check")
        self.assertIn("pending: docs/adr/0003-draft.md is new since the last stamp; its Status is not accepted, so it binds nothing", out)
        self.assertIn("pending: docs/adr/0004-taken.md is new since the last stamp; it binds where it differs", out)

    def test_reference_links_count_and_code_does_not(self) -> None:
        self.stamp_clean()
        self.repo.write(
            "docs/requirements/batches.md",
            "# Batches\n\n" + CONTRACT + "Rule. Sources: [ADR 0001][a].\n\n[a]: ../adr/0001-cancel.md\n",
        )
        self.assertEqual(self.repo.run("check")[0], 0)
        self.repo.write(
            "docs/requirements/batches.md",
            "# Batches\n\n" + CONTRACT + "Example: `[ADR 0001](../adr/0001-cancel.md)`\n\n"
            "```md\n[ADR 0001](../adr/0001-cancel.md)\n```\n",
        )
        code, out = self.repo.run("check")
        self.assertEqual(code, 1)
        self.assertIn("0001-cancel.md: cited by no requirements document", out)

    def test_non_string_script_version_is_an_error_not_a_traceback(self) -> None:
        self.stamp_clean()
        self.set_lock_field("script_version", 0.5)
        code, out = self.repo.run("check")
        self.assertEqual(code, 1)
        self.assertIn("unrecognised script_version", out)

    def test_stamp_restores_the_lock_when_check_raises(self) -> None:
        self.stamp_clean()
        before = (self.repo.root / adr_snapshot.DEFAULT_LOCK).read_text(encoding="utf-8")
        self.repo.write("docs/adr/0003-new.md", "# New\n")
        (self.repo.root / "docs/requirements/broken.md").write_bytes(b"\xff\xfe not utf-8")
        with self.assertRaises(UnicodeDecodeError):
            self.repo.run("stamp", "--na", "docs/adr/0003-new.md", "x")
        self.assertEqual((self.repo.root / adr_snapshot.DEFAULT_LOCK).read_text(encoding="utf-8"), before)

    def test_link_to_non_adr_file_in_adr_directory_is_not_a_citation(self) -> None:
        self.stamp_clean()
        self.repo.write("docs/requirements/glossary.md", "# Glossary\n\nSee the [ADR index](../adr/README.md).\n")
        code, out = self.repo.run("check")
        self.assertEqual(code, 0, out)

    def test_pre_release_versions_compare_by_release_number(self) -> None:
        self.stamp_clean()
        self.set_lock_field("script_version", f"{PLUGIN_VERSION}-rc.1")
        self.assertEqual(self.repo.run("check")[0], 0)
        self.set_lock_field("script_version", "99.0.0-rc.1")
        self.assertIn("written by adr_snapshot.py 99.0.0-rc.1", self.repo.run("check")[1])

    def test_init_refuses_to_overwrite(self) -> None:
        code, out = self.repo.run("init")
        self.assertEqual(code, 1)
        self.assertIn("already exists", out)


if __name__ == "__main__":
    unittest.main()
