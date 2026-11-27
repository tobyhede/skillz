# Provenance

This skill is third-party work, copied into skillz with its upstream license and extended here.

- Upstream: <https://github.com/cipherstash/skills/tree/f2eb8f45a33310713ea8d02ab4ad56e973dd48f3/plugins/company-skills/skills/implement-tickets>, the head of open pull request [cipherstash/skills#140](https://github.com/cipherstash/skills/pull/140)
- Commit: `f2eb8f45a33310713ea8d02ab4ad56e973dd48f3`
- Author: Company Skills contributors (CipherStash)
- License: MIT, see [LICENSE](LICENSE) (copied from the upstream repository root)
- Imported: 2026-11-27

## Local changes

`agents/openai.yaml` is byte-identical to the upstream commit. Everything else differs:

- `LICENSE`: copied from the upstream repository root, since upstream keeps no licence inside the skill directory.
- `workflows/implement-tickets.js`: reads tickets from GitHub issues, as upstream does, or from `.scratch/<feature>/issues/<NN>-<slug>.md` files (the mattpocock-skills local tracker). `args.feature` or `args.tracker: "files"` picks files. With files:
  - The Plan agent reads `spec.md` and the ticket files, their `Status:` and `Blocked by:` lines, and returns each file's text. A ticket is ready when its status is `ready-for-agent`, and closed when it is `done`, `resolved`, `closed` or `wontfix`, whatever the plan says.
  - Ticket ids are the files' `NN` prefixes; `3`, `"3"` and `"03"` name one ticket.
  - Every build, PR, review, fix and audit agent gets the ticket's text, and build and review get the spec's, because a fresh worktree may not have an untracked or ignored `.scratch/` directory.
  - Every agent's rules forbid writing, staging or committing anything under the feature directory.
  - The PR body has a `Ticket: <path>` line instead of `Closes #<n>`, and the Plan agent finds an existing PR by that line.
  
  In both modes, a blocker that is a ticket the run skips takes its state from the plan's ticket list when the plan leaves it out of `blockerStates`, so its dependents still build on a closed blocker. The result also says which tracker was used. GitHub-mode prompts are otherwise unchanged from upstream.
- `SKILL.md`: takes a spec issue number or a `.scratch` feature, and works out the tracker when given neither.
- `tests/prompts.md`: the command is `/skillz:implement-tickets`, and it adds cases for ticket files.
- `tests/test_implement_tickets_workflow.py`: moved from upstream's `scripts/tests/` into the skill, so the skillz CI runs it. It finds the skill and repository root from its own location, its README check ends at the ticket-files paragraph, and it checks that a spec number picks the GitHub tracker.
- `tests/test_implement_tickets_files.py`: added. The upstream tests rerun with ticket files, plus tests for the file tracker.
- `PROVENANCE.md`: this file.

The workflow still names `company-skills` skills (`authoring-pull-requests`, `review-audit`, `review-fix`, `run-report`, and the language skills) for its agents to call. They ship in the upstream `company-skills` plugin, not in skillz.

To update, diff `plugins/company-skills/skills/implement-tickets/` and `scripts/tests/test_implement_tickets_workflow.py` at a newer upstream commit against the upstream commit above, apply that diff here, and bump the commit.
