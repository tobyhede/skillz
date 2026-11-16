# Snapshot model and workflow impact

Read this in Baseline, before drafting the snapshot marker, and before the final report. It defines how the requirements relate to ADRs and `CONTEXT.md`, and what the rewrite changes for the repository's ongoing ADR workflow.

## Contents

- Authority
- Snapshot marker
- After the snapshot
- Strict maintenance checks
- CONTEXT.md
- Domain-modeling workflow impact
- Communicating the impact

## Authority

ADRs are the historical authority. Accepted ADRs stay binding, append-only and in place; the repository keeps writing new ones after the rewrite. The requirements are a snapshot: a restatement, in current words, of what the accepted ADRs and other sources decide as of one recorded revision. They decide nothing themselves.

- Preserve existing accepted ADRs: do not archive, merge, rewrite, renumber or mark them non-binding. Only make edits their ADR process permits, such as a status line.
- ADRs created in the rewrite PR can be corrected in place during review rather than stacking corrective ADRs. Use the repository’s own proposed status if it has one. If it has none, keep its normal ADR format (even an “accepted” label) and state that the PR’s review is the acceptance process; the ADR and its requirement changes are proposed until merge. This exception does not permit rewriting existing accepted ADRs.
- A requirement cannot override an accepted ADR. When the rewrite finds a disagreement it cannot settle from the sources, surface it; a resolution that changes what an ADR decides is a new ADR written through the repository's process, not a requirement edit.
- When the user asks to "replace" or "retire" the ADRs, explain this model. If they still want ADR authority retired, do not archive or demote any ADR: record the request as an open decision for the repository's ADR process, and continue only with work that leaves the ADRs binding.
- A maintainer ruling that settles which accepted source holds, or records detail no ADR states, without changing what any ADR decides, goes into the owning requirement with its date and into the topic's source inventory. A ruling that changes what an ADR decides, or one the ADR process requires recording, is a new ADR. Apply it to the requirements in the same change as that ADR, and mark both proposed until merge using the repository’s status convention or the PR review record. The existing decision remains binding outside that proposal until it is accepted.

## Snapshot marker

Each requirements document states, near its top, the point it was taken at:

- The checked revision and date, separately from the ADRs incorporated. A commit cannot name itself: record the base SHA and explicitly list ADRs added or changed in the same proposed change, linked by ID and path, with their proposal status. Review the actual diff as well as that base revision.
- A link to the reviewed ADR inventory and per-topic dispositions at that revision: incorporated, checked—not applicable (with reason), or unresolved. Record IDs, paths and acceptance state using the repository’s conventions. A highest incorporated ADR number may remain a navigation aid; it is never a freshness boundary or a claim that every lower number was reviewed.
- A snapshot contract: accepted ADRs remain binding, including visual detail omitted from the requirements. Accepted decisions not yet reconciled into the snapshot bind where they differ, regardless of their numbers.

For example:

> Snapshot: checked against `abc1234` (2026-11-01); reviewed ADR inventory and topic dispositions: [repository trace path]. Same-change proposals: ADR 0120 [path]. Accepted ADRs remain binding, including visual detail omitted here and decisions not yet reconciled into this snapshot, regardless of number.

A rule entry under that marker then reads, for example:

> **Cancelling a batch cancels every unfinished item.** Reason: a partly cancelled batch leaves authors unsure which items will still run. Sources: ADR 0042, ADR 0114. Evidence: `BatchCoordinator.cancel`; test `cancels queued items` covers queued items only. Gap: running items are not cancelled (linked delivery issue).

Follow the repository’s existing format for this metadata if it has one. Update the checked revision only after reviewing all changes since that topic’s previous checked revision for relevance, including cross-topic effects, and reconciling any that apply. Record one of these outcomes per topic:

- **Changed and reconciled:** update its rules, incorporated ADRs, dispositions and checked revision.
- **Checked, no change needed:** record the reviewed delta and why it does not affect the topic; advance its checked revision while leaving its rules and incorporated ADRs unchanged.
- **Not checked or unresolved:** retain its previous checked revision and record the outstanding scope or conflict. Under strict maintenance, this is an intermediate work state that blocks merge, not a standing exception.

Thus advance every topic actually reconciled, including a verified no-change result, rather than automatically advancing all topics or only owners whose prose changed. An older checked revision alone does not prove a rule is wrong; it identifies review still needed. A link fix or wording change alone does not advance the checked revision.

## After the snapshot

New decisions keep arriving as ADRs. Agree with the user, and write into the repository's workflow guide, how the snapshot keeps up:

- The default is same-change maintenance: accepting or amending an ADR updates the owning requirement in the same change. Record whether the repository requires all topics to stay current or checks a defined set of affected topics. Under the all-topics policy, every accepted ADR change requires every topic’s review and marker update, including topics with no rule changes; record the actual review before moving markers.
- Under strict maintenance, every required topic must be reconciled before merge. Remove standing “behind” exemptions from the workflow; an unresolved decision or incomplete check blocks merge. If the repository explicitly chooses a deferred snapshot policy instead, document that different contract and direct readers to accepted ADR changes absent from its reviewed inventory. Do not silently use that fallback in a strict repository.

Record the repository’s threshold for future ADRs in the workflow guide. For repositories following the domain-modeling workflow, offer an ADR for a new decision only when all three hold: changing it later has meaningful cost, a future reader would find it surprising without context, and it resolves a genuine trade-off. Keep terminology changes in the glossary and ordinary reversible choices with their existing requirements or code owner. Respect a different established repository threshold and surface conflicts rather than replacing it silently. This filter applies to new decisions: it neither retires existing accepted obligations nor exempts changes to them from the ADR process above.

Either way, read the requirement, then compare the current ADR inventory and acceptance state with its reviewed inventory and revision, including same-change proposals. Check added or changed ADRs, newly accepted existing ADRs, renames and removals; a reserved number that lands below the highest incorporated number must still be reviewed. Record reserved or missing IDs as absent, never implicitly incorporated. If the old inventory or revision is unavailable, rebuild coverage from the current catalogue and report the historical comparison limit rather than declaring freshness from numbering.

When the rewrite covers only some topics, the workflow guide keeps one list of the topics that have requirements, with each topic's marker, so a partial rewrite cannot appear to cover the whole repository. A topic not on the list is still read through its ADRs and existing guides.

## Strict maintenance checks

Specify deterministic checks in the workflow guide when strict maintenance is chosen:

- **Binding changes.** Compare both sides of the revision diff and repository acceptance conventions. New accepted ADRs, amendments to accepted ADRs and status changes affecting accepted decisions trigger reconciliation. Edits confined to proposed or rejected decisions do not require marker movement. Accepting a proposal does; a same-PR acceptance through review must include the paired requirements and required topic checks before merge, even if its ADR label already says “accepted”. Keep proposed requirement edits distinguishable from binding coverage.
- **Parseable dates.** Where amendment or Status dates are used, choose one repository-compatible form (for example `## Amendment, YYYY-MM-DD`) and a dated Status form. Reject missing, invalid or unrecognized forms rather than treating them as unchanged. Backfill historical dates from version control with provenance, using metadata edits permitted by the ADR process; if the event cannot be established, report the gap and block the date check rather than inventing a date.
- **Revision check.** Where CI can inspect the diff, require each binding ADR change to have a disposition and review evidence for every required topic. Bind evidence to the reviewed ADR version (for example its Git blob ID or content digest) so a second change on the same day invalidates earlier evidence. A marker edit alone is insufficient. Do not exempt an unchanged topic merely because its highest number and date already match. If CI cannot run this check, record the limitation and require the equivalent review before claiming strict freshness.
- **Local number/date backstop.** If the repository displays these summary fields, use the highest accepted ADR number and latest binding ADR change date together. An amendment or status change may advance only the date; a late lower-numbered ADR must not lower the number. These summaries supplement the checked revision and inventory, never replace them. An exemption for a marker already naming the newest number and date misses another accepted change with the same summary, such as a same-day amendment or lower-numbered arrival; document that blind spot in any existing checker until the revision check replaces the exemption.

Exercise fixtures for proposal-only and rejected-only edits, acceptance, amendments to older ADRs, a same-day second change, a late lower number, an untouched topic with recorded review, an unchecked topic, and malformed or missing dates. A “behind” line must not turn a failing strict check green.

## CONTEXT.md

`CONTEXT.md` (or `CONTEXT-MAP.md` and its per-context files) stays the glossary: definitions, distinctions and `_Avoid_` entries, with no behaviour, formats or build status.

- Requirements use `CONTEXT.md` terms and do not redefine them. A term coined or sharpened during the rewrite goes into `CONTEXT.md` in the same change.
- Behaviour found in a glossary entry moves to its owning requirement, leaving the definition behind.
- ADRs keep the vocabulary they were written in. Where current terms differ, give readers a mapping from old words to current ones, in the ADR catalogue or the repository's existing equivalent, rather than editing ADR bodies.
- In a multi-context repository, give each context its own requirements beside its `CONTEXT.md` and ADR directory, and keep system-wide requirements beside the system-wide ADRs.

## Domain-modeling workflow impact

Repositories that use the mattpocock skills have agents that read `CONTEXT.md` and `docs/adr/` directly: for example `diagnosing-bugs`, `tdd`, `triage`, `improve-codebase-architecture`, `to-spec` and `to-tickets` read ADRs in the area, and `domain-modeling` (also reached through `triage` and `grill-with-docs`) writes new terms and ADRs. Those skills do not know the requirements exist, and their files are not edited by this rewrite.

Those skills take repository-specific reading rules from `docs/agents/domain.md`, which `setup-matt-pocock-skills` generates, and from the agent entry point that links it. Carry these changes there and in the repository's workflow guide, or in their existing equivalents:

- **Reading order.** Agent entry point, then `CONTEXT.md` for terms, then the owning requirement, then ADRs for the full argument, rejected alternatives, history and any accepted decision not yet reconciled into the snapshot. In `docs/agents/domain.md`'s "before exploring" list, put the owning requirement before `docs/adr/`, so the skills' "read the ADRs in the area" step reaches it first.
- **Recording a decision.** `domain-modeling` still decides when an ADR is warranted and its format. Add the repository’s obligation that an accepted ADR also updates the owning requirement in the same change; use the per-topic outcomes above to update checked revisions or record remaining review.
- **Recording a term.** Unchanged: terms still go into `CONTEXT.md` the moment they settle. Add that a renamed term is also applied to the requirements that use it.
- **ADR conflicts.** Skills that respect ADRs keep doing so. Extend `docs/agents/domain.md`'s conflict rule to requirements: output that contradicts an ADR or a requirement is surfaced, and a requirement that disagrees with an accepted ADR is a defect, never a reason to ignore the ADR.
- **Build status.** Requirements may list accepted-but-unbuilt behaviour; code does not retire an accepted rule.

Check each of these against what the repository's entry points and workflow guide already say. Change only what differs, using the repository's filenames and mirror conventions.

## Communicating the impact

The final report includes a short section, written for the maintainer, that states:

1. What the requirements are: a snapshot at the checked revision with an explicit reviewed ADR inventory, not a new authority.
2. That ADRs stay binding and keep being written, and how the snapshot is kept current after this change.
3. The new reading order, and where it is written down.
4. Each change to the `CONTEXT.md` and ADR workflow, naming the file that now carries it, and any workflow step that still needs the maintainer's agreement.
