# Provenance

This skill is third-party work, copied into skillz with its upstream license.

- Upstream: <https://github.com/cipherstash/skills/tree/f2eb8f45a33310713ea8d02ab4ad56e973dd48f3/plugins/company-skills/skills/implement-tickets>, the head of open pull request [cipherstash/skills#140](https://github.com/cipherstash/skills/pull/140)
- Commit: `f2eb8f45a33310713ea8d02ab4ad56e973dd48f3`
- Author: Company Skills contributors (CipherStash)
- License: MIT, see [LICENSE](LICENSE) (copied from the upstream repository root)
- Imported: 2026-11-27

## Local changes

Every file not listed here is byte-identical to the upstream commit.

- `LICENSE`: copied from the upstream repository root, since upstream keeps no licence inside the skill directory.
- `tests/prompts.md`: the command is `/skillz:implement-tickets`, not `/company-skills:implement-tickets`.
- `tests/test_implement_tickets_workflow.py`: moved from upstream's `scripts/tests/` into the skill, so the skillz CI runs it. It finds the skill and repository root from its own location, and its README check ends at the `implement-scratch-tickets` paragraph instead of upstream's `run-report` one.
- `PROVENANCE.md`: this file.

The workflow still names `company-skills` skills (`authoring-pull-requests`, `review-audit`, `review-fix`, `run-report`, and the language skills) for its agents to call. They ship in the upstream `company-skills` plugin, not in skillz.

To update, diff `plugins/company-skills/skills/implement-tickets/` and `scripts/tests/test_implement_tickets_workflow.py` at a newer upstream commit against this directory, reapply the changes above, bump the commit here, and carry the same change into `implement-scratch-tickets`.
