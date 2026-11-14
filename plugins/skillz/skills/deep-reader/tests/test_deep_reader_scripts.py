"""Tests for the deep-reader scripts.

SelfTest runs upstream's own regression suite (scripts/self-test.sh), which
builds its fixtures in a temp directory; checks needing pdftotext or pandoc
are skipped by the suite itself when those tools are missing. The other
classes cover fixes made locally, recorded in PROVENANCE.md.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def run(script: str, *args: str | Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True, timeout=120
    )


class TempDirTestCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)


@unittest.skipIf(shutil.which("bash") is None, "bash is required")
class SelfTest(unittest.TestCase):
    def test_self_test_passes(self) -> None:
        result = run("self-test.sh")
        failures = [line for line in result.stdout.splitlines() if line.startswith("FAIL")]
        self.assertEqual(result.returncode, 0, "\n".join(failures) or result.stdout[-2000:] + result.stderr[-2000:])


class SplitChapters(TempDirTestCase):
    def test_rejects_id_that_escapes_the_workspace(self) -> None:
        ws = self.tmp / "a" / "b" / "ws"
        ws.mkdir(parents=True)
        (ws / "source.txt").write_text("[[page 1]]\nsome text\n", encoding="utf-8")
        (ws / "chapters.tsv").write_text("../../victim\t1\t1\tdraft\n", encoding="utf-8")
        result = run("split-chapters.sh", ws / "source.txt", ws / "chapters.tsv")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Invalid id", result.stderr)
        self.assertEqual(list(self.tmp.rglob("victim*")), [])


class PrepareText(TempDirTestCase):
    def test_two_non_ascii_titles_get_separate_workspaces(self) -> None:
        first, second = self.tmp / "第一本书.txt", self.tmp / "第二本书.txt"
        first.write_text("first book text\n", encoding="utf-8")
        second.write_text("second book text\n", encoding="utf-8")
        one = json.loads(run("prepare-text.sh", first).stdout)
        two = json.loads(run("prepare-text.sh", second).stdout)
        self.assertNotEqual(one["workspace"], two["workspace"])
        self.assertIn("second book", Path(two["source_txt"]).read_text(encoding="utf-8"))

    def test_refuses_workspace_built_from_another_file(self) -> None:
        book, other = self.tmp / "book.txt", self.tmp / "other.txt"
        book.write_text("the real book\n", encoding="utf-8")
        other.write_text("a different book\n", encoding="utf-8")
        ws = self.tmp / "ws"
        self.assertEqual(run("prepare-text.sh", book, ws).returncode, 0)

        again = run("prepare-text.sh", book, ws)
        self.assertEqual(again.returncode, 0)
        self.assertTrue(json.loads(again.stdout)["existing"])

        result = run("prepare-text.sh", other, ws)
        self.assertEqual(result.returncode, 3)
        self.assertIn("different source file", result.stderr)


class VerifyQuotes(TempDirTestCase):
    SOURCE = (
        "[[page 1]]\nthe quick brown fox jumps over the lazy dog\nTôi có thể đọc sách rất nhanh\n"
        "[[page 2]]\nlorem ipsum dolor sit amet consectetur\n注意力机制是深度学习的核心\nalpha beta gamma\n"
        "[[page 3]]\ndelta epsilon zeta eta theta\n"
    )

    def verify(self, note: str) -> tuple[subprocess.CompletedProcess[str], list[str], dict]:
        ws = self.tmp / "ws"
        (ws / "notes").mkdir(parents=True)
        (ws / "source.txt").write_text(self.SOURCE, encoding="utf-8")
        (ws / "notes" / "ch01.md").write_text(note, encoding="utf-8")
        result = run("verify-quotes.sh", ws)
        lines = result.stdout.splitlines()
        return result, [line.split("\t")[0] for line in lines[:-1]], json.loads(lines[-1])

    def test_each_quote_uses_its_own_citation(self) -> None:
        result, statuses, _ = self.verify(
            '"the quick brown fox jumps over" (p. 1) and "lorem ipsum dolor sit amet" (p. 2).\n'
        )
        self.assertEqual(statuses, ["OK", "OK"])
        self.assertEqual(result.returncode, 0)

    def test_quote_across_a_page_boundary(self) -> None:
        result, statuses, _ = self.verify('"alpha beta gamma delta epsilon" (pp. 2-3)\n')
        self.assertEqual(statuses, ["OK"])
        self.assertEqual(result.returncode, 0)

    def test_accents_are_significant(self) -> None:
        result, statuses, _ = self.verify(
            '"Tôi có thể đọc sách rất nhanh" (p. 1)\n"Tối có thể đọc sách rất nhanh" (p. 1)\n'
        )
        self.assertEqual(statuses, ["OK", "FAIL"])
        self.assertEqual(result.returncode, 1)

    def test_non_latin_quotes_are_checked(self) -> None:
        result, statuses, summary = self.verify(
            "“注意力机制是深度学习的核心” (p. 2)\n"
            "“这句话从来没有出现过在书里” (p. 2)\n"
            '"это цитата которой нет в книге" (p. 2)\n'
        )
        self.assertEqual(statuses, ["OK", "FAIL", "FAIL"])
        self.assertEqual(summary["checked"], 3)
        self.assertEqual(result.returncode, 1)


class BuildDiagram(TempDirTestCase):
    def workspace(self, rows: str, map_md: str | None = None) -> Path:
        ws = self.tmp / "ws"
        ws.mkdir()
        (ws / "chapters.tsv").write_text(rows, encoding="utf-8")
        if map_md is not None:
            (ws / "map.md").write_text(map_md, encoding="utf-8")
        return ws

    @staticmethod
    def indents(diagram: str) -> list[int]:
        body = diagram.split("mindmap\n", 1)[1].split("```", 1)[0]
        return [len(line) - len(line.lstrip()) for line in body.splitlines() if line.strip()]

    def test_chapters_sit_under_a_single_root(self) -> None:
        result = run("build-diagram.sh", self.workspace("ch01\t1\t5\tOne\nch02\t6\t9\tTwo\n", "# Book\n"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.indents(result.stdout), [2, 4, 4])

    def test_parts_nest_chapters_under_the_root(self) -> None:
        rows = "p1\t1\t9\tPart One\nch01\t1\t5\tOne\nch02\t6\t9\tTwo\n"
        result = run("build-diagram.sh", self.workspace(rows, "# Book\n"))
        self.assertEqual(self.indents(result.stdout), [2, 4, 6, 6])

    def test_missing_end_marker_leaves_map_untouched(self) -> None:
        original = "# Book\n\n## Structure diagram\n\n<!-- diagram:start -->\nold\n\n## Keep me\n"
        ws = self.workspace("ch01\t1\t5\tOne\n", original)
        result = run("build-diagram.sh", ws, "--append")
        self.assertEqual(result.returncode, 1)
        self.assertEqual((ws / "map.md").read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
