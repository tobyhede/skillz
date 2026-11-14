# Provenance

This skill is third-party work, vendored into skillz with its upstream license. Upstream calls the repository "book80"; the skill's own name is `distill-book`, which is why this directory uses that name.

- Upstream: <https://github.com/qianquandong/book80-skill/tree/ba7ae13c745cea899717ca3974524d8a2b84e199>
- Commit: `ba7ae13c745cea899717ca3974524d8a2b84e199`
- Author: Jack Qian
- License: MIT, see [LICENSE](LICENSE)
- Imported: 2026-11-14

## Local changes

Every file not listed here is byte-identical to the upstream commit. The upstream `.gitignore` was not copied.

- `SKILL.md`: a closing sentence in `description` points chapter-by-chapter study with persistent notes to `deep-reader`, and step 2 tells the agent to report the manifest's `skipped` entries as extraction gaps.
- `scripts/extract_epub.py`:
  - Normalizes `..` in manifest hrefs before reading the ZIP member.
  - Records every spine entry it could not extract, with a reason, under `skipped` in `manifest.json`, and warns on stderr.
  - No longer unescapes entities twice, so a literal `&lt;br&gt;` in the book stays literal.
- `scripts/build_html_report.py`:
  - Only `http:`, `https:`, `mailto:` and relative links become live; other schemes such as `javascript:` render as plain text.
  - A `#L<n>` fragment becomes a source-line link only on a relative target, so external links keep their destination.
  - In-page search matches the source text, not the line numbers.
- `tests/prompts.md`: added for the skillz behavior-case contract.
- `tests/test_distill_book_scripts.py`: added (upstream ships no tests). It covers both scripts, including the changes above.
- `PROVENANCE.md`: this file.

The upstream `README.md` install line clones the upstream repository; install through the skillz plugin instead.

To update, diff the upstream repository at a newer commit against this directory, reapply the changes above, and bump the commit here.
