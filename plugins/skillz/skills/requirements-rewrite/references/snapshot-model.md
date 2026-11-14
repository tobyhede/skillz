# Snapshot model and workflow impact

Read this in Baseline, before drafting the snapshot marker, and before the final report. It defines how the requirements relate to ADRs and `CONTEXT.md`, and what the rewrite changes for the repository's ongoing ADR workflow.

## Contents

- Authority
- Snapshot marker
- After the snapshot
- CONTEXT.md
- Domain-modeling workflow impact
- Communicating the impact

## Authority

ADRs are the historical authority. Accepted ADRs stay binding, append-only and in place; the repository keeps writing new ones after the rewrite. The requirements are a snapshot: a restatement, in current words, of what the accepted ADRs and other sources decide as of one recorded revision. They decide nothing themselves.

- Never archive, merge, rewrite, renumber or mark ADRs non-binding as part of this workflow. The only ADR edits allowed are those the repository's ADR process already permits, such as a status line.
- A requirement cannot override an accepted ADR. When the rewrite finds a disagreement it cannot settle from the sources, surface it; a resolution that changes what an ADR decides is a new ADR written through the repository's process, not a requirement edit.
- When the user asks to "replace" or "retire" the ADRs, explain this model. If they still want ADR authority retired, do not archive or demote any ADR: record the request as an open decision for the repository's ADR process, and continue only with work that leaves the ADRs binding.
- A maintainer ruling that settles which accepted source holds, or records detail no ADR states, without changing what any ADR decides, goes into the owning requirement with its date and into the topic's source inventory. A ruling that changes what an ADR decides, or one the ADR process requires recording, is a new ADR.

## Snapshot marker

Each requirements document states, near its top, the point it was taken at:

- The source commit SHA and date the restatement was checked against. A commit cannot name itself, so record the base commit the change was made on; when the requirement is updated in the same change as an ADR, the ADR number is the reliable key.
- The highest ADR number incorporated, or the explicit list of source ADRs for the topic, including any that were reviewed and found not to apply.
- A one-line rule for readers: ADRs accepted after this point bind where they differ, until the requirements are updated.

For example:

> Snapshot: checked against `abc1234` (2026-11-01); incorporates ADRs through 0120. ADRs accepted after 0120 bind where they differ, until this document is updated.

A rule entry under that marker then reads, for example:

> **Cancelling a batch cancels every unfinished item.** Reason: a partly cancelled batch leaves authors unsure which items will still run. Sources: ADR 0042, ADR 0114. Evidence: `BatchCoordinator.cancel`; test `cancels queued items` covers queued items only. Gap: running items are not cancelled (linked delivery issue).

Follow the repository's existing format for this metadata if it has one. Update the marker only when the topic is actually reconciled against a newer revision; a link fix or wording change does not advance it.

## After the snapshot

New decisions keep arriving as ADRs. Agree with the user, and write into the repository's workflow guide, how the snapshot keeps up:

- The default is same-change maintenance: accepting an ADR updates the owning requirement and its snapshot marker in the same change.
- If the repository will not maintain requirements that way, the snapshot goes stale by design. Say so in each marker, and have the reading path send readers to ADRs newer than the marker.

Either way, the reader's rule is the same: read the requirement, then check the ADR catalogue for anything accepted after its marker.

When the rewrite covers only some topics, the workflow guide keeps one list of the topics that have requirements, with each topic's marker, so a partial rewrite cannot appear to cover the whole repository. A topic not on the list is still read through its ADRs and existing guides.

## CONTEXT.md

`CONTEXT.md` (or `CONTEXT-MAP.md` and its per-context files) stays the glossary: definitions, distinctions and `_Avoid_` entries, with no behaviour, formats or build status.

- Requirements use `CONTEXT.md` terms and do not redefine them. A term coined or sharpened during the rewrite goes into `CONTEXT.md` in the same change.
- Behaviour found in a glossary entry moves to its owning requirement, leaving the definition behind.
- ADRs keep the vocabulary they were written in. Where current terms differ, give readers a mapping from old words to current ones, in the ADR catalogue or the repository's existing equivalent, rather than editing ADR bodies.
- In a multi-context repository, give each context its own requirements beside its `CONTEXT.md` and ADR directory, and keep system-wide requirements beside the system-wide ADRs.

## Domain-modeling workflow impact

Repositories that use the mattpocock skills have agents that read `CONTEXT.md` and `docs/adr/` directly: for example `diagnosing-bugs`, `tdd`, `triage`, `improve-codebase-architecture`, `to-spec` and `to-tickets` read ADRs in the area, and `domain-modeling` (also reached through `triage` and `grill-with-docs`) writes new terms and ADRs. Those skills do not know the requirements exist, and their files are not edited by this rewrite.

Those skills take repository-specific reading rules from `docs/agents/domain.md`, which `setup-matt-pocock-skills` generates, and from the agent entry point that links it. Carry these changes there and in the repository's workflow guide, or in their existing equivalents:

- **Reading order.** Agent entry point, then `CONTEXT.md` for terms, then the owning requirement, then ADRs for the full argument, rejected alternatives, history and anything newer than the snapshot marker. In `docs/agents/domain.md`'s "before exploring" list, put the owning requirement before `docs/adr/`, so the skills' "read the ADRs in the area" step reaches it first.
- **Recording a decision.** `domain-modeling` still decides when an ADR is warranted and its format. Add the repository's obligation that an accepted ADR also updates the owning requirement and marker in the same change, or records that the topic's snapshot is now behind.
- **Recording a term.** Unchanged: terms still go into `CONTEXT.md` the moment they settle. Add that a renamed term is also applied to the requirements that use it.
- **ADR conflicts.** Skills that respect ADRs keep doing so. Extend `docs/agents/domain.md`'s conflict rule to requirements: output that contradicts an ADR or a requirement is surfaced, and a requirement that disagrees with an accepted ADR is a defect, never a reason to ignore the ADR.
- **Build status.** Requirements may list accepted-but-unbuilt behaviour; code does not retire an accepted rule.

Check each of these against what the repository's entry points and workflow guide already say. Change only what differs, using the repository's filenames and mirror conventions.

## Communicating the impact

The final report includes a short section, written for the maintainer, that states:

1. What the requirements are: a snapshot as of the recorded SHA and ADR number, not a new authority.
2. That ADRs stay binding and keep being written, and how the snapshot is kept current after this change.
3. The new reading order, and where it is written down.
4. Each change to the `CONTEXT.md` and ADR workflow, naming the file that now carries it, and any workflow step that still needs the maintainer's agreement.
