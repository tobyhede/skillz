# Provenance

This skill is third-party work, vendored into skillz with its upstream license. Upstream calls the repository "book80"; the skill's own name is `distill-book`, which is why this directory uses that name.

- Upstream: <https://github.com/qianquandong/book80-skill/tree/ba7ae13c745cea899717ca3974524d8a2b84e199>
- Commit: `ba7ae13c745cea899717ca3974524d8a2b84e199`
- Author: Jack Qian
- License: MIT, see [LICENSE](LICENSE)
- Imported: 2026-11-14

## Local changes

Every other file is byte-identical to the upstream commit. The upstream `.gitignore` was not copied.

- `SKILL.md`: a closing sentence in `description` points chapter-by-chapter study with persistent notes to `deep-reader`.
- `tests/prompts.md`: added for the skillz behavior-case contract.
- `tests/test_scripts.py`: added; upstream ships no tests for its two scripts.
- `PROVENANCE.md`: this file.

The upstream `README.md` install line clones the upstream repository; install through the skillz plugin instead.

To update, diff the upstream repository at a newer commit against this directory, reapply the changes above, and bump the commit here.
