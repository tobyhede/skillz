# Behavior cases

## Should activate

- “Consolidate our ADRs and overlapping product guides into requirements that state the current design.”
- “We've written another dozen ADRs since the requirements were last updated. Bring them up to date.”
- “Our specs are out of date with the ADRs.”
- “The architecture changed substantially. Reconcile the requirements with the new ownership boundaries and keep the implementation gaps visible.”
- “Make these conflicting design documents consistent.” If the repository or governing authority is not available, inspect the available context and ask for the missing source or decision before asserting a resolution.

## Should not activate

- “Fix the typo in the storage requirements heading.” Correct the wording and any affected anchor references without starting a rewrite.
- “Implement retry support for this operation.” Implementation alone does not call for a requirements snapshot.
- “Summarize this ADR.” A summary does not require a requirements snapshot.
- “Record an ADR for this decision.” Writing one ADR belongs to the repository's ADR workflow, though the agent should note that the owning requirement needs updating in the same change.

## Expected behavior

- Record the actual repository, source commit and reviewed target commit, and inspect the governing instructions before choosing document owners.
- Use the repository’s existing glossary and agent entry-point filenames, including their mirror conventions. Do not introduce a new glossary merely to match a filename assumed by the workflow.
- Account for every inventoried source rule and preserve the distinction between intended behaviour, implemented behaviour and verified test coverage.
- Retain an unambiguously binding rule when the code differs; record the implementation gap rather than asking the maintainer to approve the same rule again.
- Resolve genuine intent conflicts with concrete evidence and a recommendation, and keep unresolved decisions explicit while continuing independent work.
- Keep styling-only treatment with code and tests while retaining requirements for meaning, reachability, focus, announcements and stored state.
- Inspect delegated diffs and use independent audit and fresh-reader exercises when delegation is available; identify a sequential review honestly when it is not.
- Classify upstream changes through a named revision and reconcile the affected topics. Do not call a stale but internally consistent draft current.
- Leave every ADR body unchanged, in place and binding; link each requirement to its source ADRs and route any change to a decision through the ADR process rather than a requirement edit.
- Mark each requirements document as a snapshot with its source SHA, date and highest incorporated ADR, and tell readers that later ADRs bind where they differ.
- Write into the repository's own entry points and workflow guide the new reading order and the obligation that an accepted ADR updates the owning requirement, since the domain-modeling skills read `CONTEXT.md` and ADRs directly. Do not edit those skills.
- Keep `CONTEXT.md` a glossary: add terms coined during the rewrite there and move behaviour out of it, without redefining terms in the requirements.
- End with a workflow-impact summary for the maintainer covering the snapshot point, ADR continuation, reading order and each `CONTEXT.md` or ADR workflow change.
- When asked to replace or retire the ADRs, explain the snapshot model and archive or demote nothing, even if the user confirms; record the request as an open decision for the ADR process and continue only with work that leaves the ADRs binding.
- When the governing instructions rank requirements above accepted ADRs, surface the conflict and record it as an open decision rather than adopting either order.
- Refresh an existing snapshot by reconciling ADRs accepted since its marker and advancing the marker, without unnecessary archival.
- Report unavailable checks and publication or integration state separately. Never infer that a link scan substitutes for unexecuted tests or that a conflicting draft PR is integrated.

## Forward-test scenarios

### Refactor with narrower coverage

User request: “Refresh our requirements after the refactor and prepare a reviewable patch. You may use agents. Do not implement product fixes or publish.”

Raw artifacts: the requirements at revision `a1` say cancelling a batch cancels all unfinished items. Refactor `b2` moves the coordinator into a shared package. A test asserts that queued items are cancelled and says nothing about running items. No recorded decision supersedes the existing rule. Target revision `c3` includes an unrelated icon change and a new bulk-import operation. Test dependencies are absent.

Observe whether the agent distinguishes absent coverage from proof of a defect, inspects implementation before assigning a status, assesses whether the old rule applies to the new operation, records unavailable checks and respects the local-patch boundary. Do not provide those observations as the expected answer to an independent evaluator.

### Different documentation conventions

User request: “Consolidate the old design records into current requirements.”

Raw artifacts: the repository uses `GLOSSARY.md` and `DEVELOPMENT.md`; two host-specific instruction files point to `DEVELOPMENT.md`. Historical ADRs carry source line citations in review records. There is no `CONTEXT.md` or `AGENTS.md`.

Observe whether the agent uses the existing glossary and instruction route, preserves historical evidence and verifies incoming references instead of introducing a parallel documentation hierarchy.

### Upstream drift after audit

User request: “Finish the requirements refresh and report its validation.”

Raw artifacts: the draft was audited at `d1`. Current target `d2` changes a public operation’s refusal outcome and moves its tests. The draft’s links still resolve. A maintainer decision documenting the new outcome exists at `d2`.

Observe whether the agent reopens the affected topic, updates evidence and the reviewed revision, and reruns relevant checks before claiming freshness.

### ADR-governed repository with a domain-modeling workflow

User request: “Bring the requirements up to date and replace the ADRs with them.”

Raw artifacts: the repository has `AGENTS.md`, `CONTEXT.md` and a `docs/agents/domain.md` generated by `setup-matt-pocock-skills`, with a “Before exploring” list naming `CONTEXT.md` and `docs/adr/` and a “Flag ADR conflicts” rule. ADRs 0001–0120 are accepted. The existing requirements carry a snapshot marker at ADR 0110, and ADR 0114 changes one of their rules. One `CONTEXT.md` entry states a retry limit as well as a definition. The workflow guide does not mention the requirements.

Observe whether the agent leaves every ADR binding and records the retirement request as an open decision for the ADR process; reconciles ADRs 0111–0120 and advances the marker; moves the retry limit out of `CONTEXT.md` while keeping the definition; updates `docs/agents/domain.md` and the workflow guide with the reading order and the same-change rule without editing the domain-modeling skills; and ends with the workflow-impact summary.
