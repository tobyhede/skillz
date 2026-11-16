# Evidence and run records

Use this reference when starting or resuming a run, recording source dispositions, or preparing a decision. Adapt these fields to the repository's existing format rather than creating parallel records.

## Run record

Keep the record in a durable location agreed by the task or established repository conventions. It should contain:

- Repository identity, worktree, branch and source SHA.
- Target branch and last checked target SHA; affected topics since the prior checkpoint.
- Scope, exclusions, authorization already given and any remaining explicit gates.
- Topic owners, source inventory and locations of drafts, traces and decisions.
- Per-topic checked revisions, reviewed ADR inventories and dispositions, including same-change proposals, no-change review outcomes with reasons, and outstanding review.
- Rulings, each with a “Changes an ADR?” yes/no column, affected ADRs, the reason for the classification, and the new ADR or open conflict for each yes. Recheck earlier rulings when later drafting reveals a narrowing.
- Exact validation commands, tool/dependency prerequisites, observed results and unavailable checks.
- Open questions, unresolved findings and the next concrete action.

Record SHAs rather than relying on branch names or “latest”. Update this record at checkpoints and handoffs. Keep private evidence outside a publication path when the task requires it.

## Source disposition

| Source at revision | Claim | Disposition | Owner / reason |
| --- | --- | --- | --- |
| Path and heading or symbol (lines optional); source SHA | One independently decidable obligation | Retained, superseded, redirected, historical, presentation-only, open | Requirement or ruling; explanation for omission |

Split a source paragraph when its obligations have different owners or outcomes. Preserve useful reasons and rejected alternatives that constrain today's design; put their historical narrative in the trace. Treat behaviour stated in an accepted ADR’s Costs or Consequences section as decided, unless the passage merely describes an observation, trade-off or prediction rather than prescribing an outcome. Record a reason for every dropped claim, including those classified as descriptive; the section heading alone cannot justify dropping it. A merely descriptive visual duration need not become a behavioural requirement. Keep ADR-decided visual detail traceable to its structural owner even when omitted from the requirements prose.

Mark each supersession or conflict disposition by basis: source-stated (an accepted ADR or source says so), proposed (an agent's inference) or ruled (a dated maintainer answer); a proposed disposition is not final. On refresh, re-resolve each cited anchor at the new SHA (`git diff <old>..<new> -- <path>`) and reopen claims whose cited text changed.

Distinguish whole-ADR supersession from partial refinement. Record the exact claims and scopes a successor replaces; retain the predecessor’s unaffected obligations and their source citations. A successor link or later ADR number alone does not establish whole-document supersession. If a status label implies full replacement but the decision text changes only part, record the ambiguity as an open conflict rather than silently dropping the rest. When using a catalogue or selecting ADRs for a topic, include predecessors whose obligations still apply.

Triage at document level first: a document with one outcome throughout (superseded in full by a named ADR, out of scope, presentation-only) takes one row. Split into claims only for retained, partly superseded or conflicting material, and batch triage by topic.

## Requirement evidence

Record intended behaviour, reason and evidence together. Record status beside them only where the repository keeps build status in requirements; otherwise list unbuilt behaviour apart from the rules and link each gap to where status is tracked, such as a delivery issue. Use the repository's status vocabulary consistently. Useful distinctions are built with verified coverage, built with no verified test, not built, and bug: code differs from the decided behaviour. Use “not built” only when no code path for the required behaviour exists at all. If a relevant path exists but produces the wrong outcome, classify it as “bug: code differs”, including partial implementations. Missing test coverage alone proves neither absence nor a defect.

Cite code by path and symbol and tests by path and case name at the reviewed revision. Identify whether a test was inspected or executed. A test name alone is not proof: inspect its setup and assertions. Record assumptions and uncovered cases explicitly.

## Decision request

Lead with the action and outcome: “When a batch operation is cancelled, should it cancel every item in the batch or only items that have not started?”

Then provide:

1. The competing claims, with short source excerpts and locations.
2. What the code does, and precisely what relevant tests assert.
3. A recommendation, the author-visible consequence and any implementation gap it creates.
4. The affected owners and rule IDs as supporting references.

Record the maintainer's actual answer separately from the recommendation and classify its ADR impact. Apply a ruling to all affected owners, statuses, traces and glossary entries. When it changes an accepted ADR, apply it in the same change as the draft ADR, and mark both proposed until merge using the acceptance convention in the snapshot-model reference. Record the existing decision and proposed replacement in the trace so their authority is clear. If there is no replacing ADR, retain the still-binding rule and record the ruling as an open conflict. Do not leave a rejected recommendation looking like the current decision.
