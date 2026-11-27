# Provenance

This skill is a variant of the `implement-tickets` skill in this plugin, which is copied from [cipherstash/skills](https://github.com/cipherstash/skills) at commit `f2eb8f45a33310713ea8d02ab4ad56e973dd48f3` under the MIT licence. See [LICENSE](LICENSE) and `../implement-tickets/PROVENANCE.md`.

## What differs from implement-tickets

The workflow, its models, its review and fix rounds, its chain of pull requests and its run report are the same. What changes is where the tickets come from:

- `workflows/implement-scratch-tickets.js`:
  - Takes `feature` (a slug under `.scratch/`, or a directory path) instead of `spec`, and ticket ids such as `"03"` instead of issue numbers. `3`, `"3"` and `"03"` name the same ticket.
  - The Plan agent reads `spec.md` and the `issues/<NN>-<slug>.md` files, their `Status:` and `Blocked by:` lines, and returns each file's text. A ticket is ready when its status is `ready-for-agent`, and closed when its status is `done`, `resolved`, `closed` or `wontfix`.
  - Every build, PR, review, fix and audit agent gets the ticket's text, and build and review get the spec's, because a fresh worktree may not have an untracked or ignored `.scratch/` directory.
  - Every agent's rules forbid writing, staging or committing anything under the feature directory.
  - The PR body has a `Ticket: <path>` line instead of `Closes #<n>`, and the Plan agent finds an existing PR by that line.
  - Branches are named after the ticket file, for example `feat/03-add-filters`.
- `SKILL.md`, `tests/prompts.md`: written for this variant.
- `tests/test_implement_scratch_tickets_workflow.py`: implement-tickets' tests with ticket ids for issue numbers, plus tests for the differences above.

Carry any fix to `implement-tickets`' workflow into this one.
