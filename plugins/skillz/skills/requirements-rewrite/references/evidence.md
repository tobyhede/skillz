# Evidence and run records

Use this reference when starting or resuming a run, recording source dispositions, or preparing a decision. Adapt these fields to the repository's existing format rather than creating parallel records.

## Run record

Keep the record in a durable location agreed by the task or established repository conventions. It should contain:

- Repository identity, worktree, branch and source SHA.
- Target branch and last checked target SHA; affected topics since the prior checkpoint.
- Scope, exclusions, authorization already given and any remaining explicit gates.
- Topic owners, source inventory and locations of drafts, traces and decisions.
- Exact validation commands, tool/dependency prerequisites, observed results and unavailable checks.
- Open questions, unresolved findings and the next concrete action.

Record SHAs rather than relying on branch names or “latest”. Update this record at checkpoints and handoffs. Keep private evidence outside a publication path when the task requires it.

## Source disposition

| Source at revision | Claim | Disposition | Owner / reason |
| --- | --- | --- | --- |
| Path, heading or lines; source SHA | One independently decidable obligation | Retained, superseded, redirected, historical, presentation-only, open | Requirement or ruling; explanation for omission |

Split a source paragraph when its obligations have different owners or outcomes. Preserve useful reasons and rejected alternatives that constrain today's design; put their historical narrative in the trace. A source that merely describes a visual duration need not become a behavioural requirement.

## Requirement evidence

Record intended behaviour, reason and evidence together. Record status beside them only where the repository keeps build status in requirements; otherwise list unbuilt behaviour apart from the rules and link each gap to where status is tracked, such as a delivery issue. Use the repository's status vocabulary consistently. Useful distinctions are built with verified coverage, built with no verified test, not built, and code differs from the decided behaviour.

Cite code by path and symbol and tests by path and case name at the reviewed revision. Identify whether a test was inspected or executed. A test name alone is not proof: inspect its setup and assertions. Record assumptions and uncovered cases explicitly.

## Decision request

Lead with the action and outcome: “When a batch operation is cancelled, should it cancel every item in the batch or only items that have not started?”

Then provide:

1. The competing claims, with short source excerpts and locations.
2. What the code does, and precisely what relevant tests assert.
3. A recommendation, the author-visible consequence and any implementation gap it creates.
4. The affected owners and rule IDs as supporting references.

Record the maintainer's actual answer separately from the recommendation. Apply the ruling to all affected owners, statuses, traces and glossary entries; do not leave the rejected recommendation looking like the current decision.
