# Provenance

This skill is third-party work, vendored into skillz with its upstream license.

- Upstream: <https://github.com/tronghieu/agent-skills/tree/831d1ae5c686a81b10f9c5b9cca04a7b8b97303d/skills/deep-reader>
- Commit: `831d1ae5c686a81b10f9c5b9cca04a7b8b97303d`
- Author: Hieu T. Luu
- License: MIT, see [LICENSE](LICENSE) (copied from the upstream repository root)
- Imported: 2026-11-14

## Local changes

Every file not listed here is byte-identical to the upstream commit.

- `LICENSE`: copied from the upstream repository root, since upstream keeps no licence inside the skill directory.
- `SKILL.md`:
  - The folded (`>-`) `description` is joined onto one line so `scripts/validate.py` can check it, and a closing sentence points fast whole-book briefings to `distill-book`.
  - Documents `prepare-text.sh` exit code 3, the `source.id` workspace file, and `verify-quotes.sh` `SKIP` lines.
- `scripts/split-chapters.sh`: rejects a chapter id that is not a single safe path component, so `../../x` cannot write outside the workspace.
- `scripts/prepare-text.sh`:
  - A file name with no ASCII letters or digits slugs to `doc-<hash>` instead of `doc`.
  - The workspace records the input's SHA-256 in `source.id` and exits 3 instead of reusing a workspace built from a different file.
- `scripts/verify-quotes.sh`:
  - Keeps non-ASCII letters when normalizing, so accents matter and Cyrillic or CJK quotes are checked rather than skipped.
  - Selects unspaced (CJK) quotes.
  - Pairs each quote with its own citation when a line has several.
  - Joins page blobs with single spaces so cross-page quotes match.
  - Runs awk in the C locale.
  - Reports quotes it cannot check as `SKIP`, counts them in a new `skipped` field, and exits 1 when there are any.
- `scripts/build-diagram.sh`:
  - Indents every row under the title, so the mindmap has a single root.
  - Refuses to rewrite `map.md` when only one diagram marker is present.
- `tests/prompts.md`: added for the skillz behavior-case contract.
- `tests/test_deep_reader_scripts.py`: added. It runs upstream's `scripts/self-test.sh` and adds regression tests for the script changes above.
- `PROVENANCE.md`: this file.

To update, diff `skills/deep-reader/` at a newer upstream commit against this directory, reapply the changes above, and bump the commit here.
