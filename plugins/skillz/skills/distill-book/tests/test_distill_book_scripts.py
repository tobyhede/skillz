"""Tests for the distill-book scripts: extract_epub.py and build_html_report.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"

CONTAINER = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"""

OPF = """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <manifest>
    <item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>
    <item id="c1" href="text/chapter%201.xhtml" media-type="application/xhtml+xml"/>
    <item id="c2" href="text/ch2.xhtml" media-type="application/xhtml+xml"/>
    <item id="gone" href="text/missing.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="cover" linear="no"/>
    <itemref idref="c1"/>
    <itemref idref="gone"/>
    <itemref idref="c2"/>
  </spine>
</package>"""

CH1 = """<html><head><title>Feedback Loops</title><style>p{color:red}</style></head>
<body><h1>Feedback Loops</h1><p>Systems&nbsp;learn &amp; adapt.</p><script>alert(1)</script><p>Second   paragraph.</p></body></html>"""

CH2 = "<html><body><p>No title here.</p></body></html>"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-I", *args], capture_output=True, text=True, timeout=60)


class TempDirTestCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)


class ExtractEpub(TempDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.out = self.tmp / "out"

    def extract(self, epub: Path) -> subprocess.CompletedProcess[str]:
        return run(str(SCRIPTS / "extract_epub.py"), str(epub), "--output-dir", str(self.out))

    def manifest(self) -> dict:
        return json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))

    def make_epub(self, files: dict[str, str]) -> Path:
        path = self.tmp / "book.epub"
        with zipfile.ZipFile(path, "w") as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        return path

    def test_extracts_linear_spine_in_order_with_locators(self) -> None:
        epub = self.make_epub({
            "META-INF/container.xml": CONTAINER,
            "OEBPS/content.opf": OPF,
            "OEBPS/cover.xhtml": "<html><body><p>Cover</p></body></html>",
            "OEBPS/text/chapter 1.xhtml": CH1,
            "OEBPS/text/ch2.xhtml": CH2,
        })
        result = self.extract(epub)
        self.assertEqual(result.returncode, 0, result.stderr)

        manifest = self.manifest()
        self.assertEqual(manifest["sections_extracted"], 2)
        self.assertEqual(
            [(gap["spine_index"], gap["reason"]) for gap in manifest["skipped"]], [(2, "missing from archive")]
        )
        sections = manifest["sections"]
        # Non-linear cover is skipped; missing spine item is skipped; indices keep spine order.
        self.assertEqual([s["spine_index"] for s in sections], [1, 3])
        self.assertEqual(sections[0]["title"], "Feedback Loops")
        self.assertEqual(sections[0]["source_path"], "OEBPS/text/chapter 1.xhtml")
        self.assertEqual(sections[1]["title"], "ch2")

        text = (self.out / sections[0]["output_file"]).read_text(encoding="utf-8")
        self.assertTrue(text.startswith("SOURCE: EPUB spine 1, OEBPS/text/chapter 1.xhtml\nTITLE: Feedback Loops\n"))
        self.assertIn("Systems learn & adapt.", text)
        self.assertIn("Second paragraph.", text)
        self.assertNotIn("alert", text)
        self.assertNotIn("color:red", text)

    def test_resolves_parent_relative_hrefs(self) -> None:
        opf = OPF.replace('href="text/chapter%201.xhtml"', 'href="../Text/one.xhtml"')
        epub = self.make_epub({
            "META-INF/container.xml": CONTAINER.replace("OEBPS/content.opf", "OEBPS/pkg/content.opf"),
            "OEBPS/pkg/content.opf": opf,
            "OEBPS/Text/one.xhtml": CH1,
        })
        result = self.extract(epub)
        self.assertEqual(result.returncode, 0, result.stderr)
        sections = self.manifest()["sections"]
        self.assertEqual([s["source_path"] for s in sections], ["OEBPS/Text/one.xhtml"])

    def test_keeps_escaped_markup_literal(self) -> None:
        epub = self.make_epub({
            "META-INF/container.xml": CONTAINER,
            "OEBPS/content.opf": OPF,
            "OEBPS/text/chapter 1.xhtml": "<html><body><p>use &amp;lt;br&amp;gt; tag</p></body></html>",
        })
        self.assertEqual(self.extract(epub).returncode, 0)
        text = (self.out / self.manifest()["sections"][0]["output_file"]).read_text(encoding="utf-8")
        self.assertIn("use &lt;br&gt; tag", text)

    def test_missing_file_exits_2(self) -> None:
        result = self.extract(self.tmp / "nope.epub")
        self.assertEqual(result.returncode, 2)
        self.assertIn("file not found", result.stderr)

    def test_not_a_zip_exits_2(self) -> None:
        bad = self.tmp / "bad.epub"
        bad.write_text("not a zip", encoding="utf-8")
        result = self.extract(bad)
        self.assertEqual(result.returncode, 2)
        self.assertIn("not a valid EPUB", result.stderr)

    def test_missing_container_exits_2(self) -> None:
        epub = self.make_epub({"mimetype": "application/epub+zip"})
        result = self.extract(epub)
        self.assertEqual(result.returncode, 2)
        self.assertIn("malformed EPUB", result.stderr)

    def test_no_text_exits_1(self) -> None:
        epub = self.make_epub({
            "META-INF/container.xml": CONTAINER,
            "OEBPS/content.opf": OPF,
            "OEBPS/text/chapter 1.xhtml": "<html><body><script>x</script></body></html>",
        })
        result = self.extract(epub)
        self.assertEqual(result.returncode, 1)
        manifest = self.manifest()
        self.assertEqual(manifest["sections_extracted"], 0)


class BuildHtmlReport(TempDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.source = self.tmp / "book.txt"
        self.source.write_text("line one\n<b>line two</b>\nline three\n", encoding="utf-8")

    def build(self, report: str, *extra: str) -> tuple[subprocess.CompletedProcess[str], str]:
        md = self.tmp / "report.md"
        md.write_text(report, encoding="utf-8")
        out = self.tmp / "out" / "brief.html"
        result = run(str(SCRIPTS / "build_html_report.py"), str(md), str(self.source), "--output", str(out), *extra)
        return result, out.read_text(encoding="utf-8") if out.exists() else ""

    def test_embeds_source_and_links_citations(self) -> None:
        result, doc = self.build(
            "# My Book\n\n## Core ideas\n\n- **Claim** [Chapter 2, source line 2](./book-source.html#L2)\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("3 anchored source lines", result.stdout)
        self.assertIn("<title>My Book - Interactive Brief</title>", doc)
        self.assertIn('<html lang="en">', doc)
        self.assertIn('href="#source-L2" data-line="2"', doc)
        self.assertIn('id="source-L3"', doc)
        # Source text is escaped, not injected as markup.
        self.assertIn("&lt;b&gt;line two&lt;/b&gt;", doc)
        self.assertNotIn("<b>line two</b>", doc)
        self.assertIn("<strong>Claim</strong>", doc)

    def test_unsafe_link_schemes_are_not_live(self) -> None:
        result, doc = self.build(
            "# B\n\n[a](javascript:alert%281%29) [b](JavaScript:x) [c](data:text/html,x) [ok](https://example.com)\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('href="javascript', doc.lower())
        self.assertNotIn('href="data:', doc)
        self.assertIn('<a href="https://example.com">ok</a>', doc)

    def test_external_line_fragments_keep_their_destination(self) -> None:
        _, doc = self.build("# B\n\n[gh](https://github.com/a/b/blob/main/f.py#L10)\n")
        self.assertIn('href="https://github.com/a/b/blob/main/f.py#L10"', doc)
        self.assertNotIn('href="#source-L10"', doc)

    def test_search_ignores_line_numbers(self) -> None:
        _, doc = self.build("# B\n")
        self.assertIn("lastElementChild.textContent", doc)
        self.assertNotIn("LS[i].innerText", doc)

    def test_detects_chinese_and_honours_overrides(self) -> None:
        result, doc = self.build("# 思考\n\n正文\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('<html lang="zh">', doc)
        self.assertIn("交互式速读", doc)

        result, doc = self.build("# 思考\n\n正文\n", "--lang", "en", "--title", "Override")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('<html lang="en">', doc)
        self.assertIn("<title>Override - Interactive Brief</title>", doc)


if __name__ == "__main__":
    unittest.main()
