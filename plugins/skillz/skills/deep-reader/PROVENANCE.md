# Provenance

This skill is third-party work, vendored into skillz with its upstream license.

- Upstream: <https://github.com/tronghieu/agent-skills/tree/831d1ae5c686a81b10f9c5b9cca04a7b8b97303d/skills/deep-reader>
- Commit: `831d1ae5c686a81b10f9c5b9cca04a7b8b97303d`
- Author: Hieu T. Luu
- License: MIT, see [LICENSE](LICENSE) (copied from the upstream repository root)
- Imported: 2026-11-14

## Local changes

Every other file is byte-identical to the upstream commit.

- `SKILL.md`: the folded (`>-`) `description` is joined onto one line so `scripts/validate.py` can check it, and a closing sentence points fast whole-book briefings to `distill-book`.
- `tests/prompts.md`: added for the skillz behavior-case contract.
- `tests/test_scripts.py`: added; it runs upstream's own `scripts/self-test.sh` in CI.
- `PROVENANCE.md`: this file.

To update, diff `skills/deep-reader/` at a newer upstream commit against this directory, reapply the changes above, and bump the commit here.
