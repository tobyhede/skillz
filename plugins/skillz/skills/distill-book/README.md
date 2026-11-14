# book80

**English** | [中文](./README.zh-CN.md)

An agent skill that distills an EPUB or PDF into a 30-second, a 3-minute, and a 10-minute briefing — with every key claim traceable back to where the book actually says it.

The goal is understanding per minute, not coverage per page: the highest-value 80% of a book, fast, without losing the ability to check the original.

## What it does

- Reads EPUB, text or scanned PDF, plain text, Markdown, HTML, and DOCX.
- Extracts the text with **stable locators** (page number, chapter + heading, spine index) so every claim in the briefing can point back to its source. Extraction gaps are reported, never silently summarized over.
- Adapts to a reading goal: rapid understanding, work application, critical reading, content creation, or study.
- Outputs three briefing depths — 30 seconds, 3 minutes, 10 minutes — plus an optional self-contained interactive HTML reader.
- Given only a book title (no file), it will say so and produce a synthesis from public sources, clearly labeled as not source-grounded.

## Install

```bash
git clone https://github.com/qianquandong/book80-skill.git ~/.claude/skills/book80-skill
```

Works in Claude Code and Codex. The EPUB extractor is a plain Python script with no third-party dependencies:

```bash
python3 scripts/extract_epub.py BOOK.epub --output-dir extracted/
```

## Use

Point the skill at a book file:

> Distill ~/Books/thinking-fast-and-slow.epub — I want the 3-minute version for work application.

Or just ask for a book summary; the skill picks rapid understanding by default and asks a question only when the answer would change the result.

## Files

| Path | What it is |
|------|------------|
| `SKILL.md` | The full playbook the agent follows |
| `scripts/extract_epub.py` | EPUB → chapters with a manifest, stdlib only |
| `scripts/build_html_report.py` | Builds the optional interactive HTML reader |
| `references/` | Supporting reference material |

## License

MIT
