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
- “Add a requirement for feature Y.” Add the single rule to its owning requirements document without a snapshot rewrite; if it changes what an accepted ADR decides, route it to the ADR process instead.
- “Update the docs for this PR.” Edit the documents the change affects without starting a requirements rewrite, and note any owning requirement the change makes stale.

## Expected behavior

- Record the actual repository, source commit and reviewed target commit, and inspect the governing instructions before choosing document owners.
- Use the repository’s existing glossary and agent entry-point filenames, including their mirror conventions. Do not introduce a new glossary merely to match a filename assumed by the workflow.
- Keep only universal constraints in agent entry points; move topic-specific rules to their owning requirements and leave a pointer with an explicit trigger.
- Account for every inventoried source rule and preserve the distinction between intended behaviour, implemented behaviour and verified test coverage.
- Include reusable validators and passing/failing fixture tests in the repository patch, unignore their specific paths if necessary, and commit them when delivering commits.
- Retain an unambiguously binding rule when the code differs; record the implementation gap rather than asking the maintainer to approve the same rule again.
- Resolve genuine intent conflicts with concrete evidence and a recommendation, and keep unresolved decisions explicit while continuing independent work.
- Keep styling-only treatment with code and tests while retaining requirements for meaning, reachability, focus, announcements and stored state.
- Inspect delegated diffs and use independent audit and fresh-reader exercises when delegation is available; identify a sequential review honestly when it is not.
- Classify upstream changes through a named revision and reconcile the affected topics. Do not call a stale but internally consistent draft current.
- Leave existing accepted ADR bodies unchanged beyond process-permitted edits, in place and binding; link each requirement to its source ADRs and route any change to a decision through the ADR process rather than a requirement edit.
- Mark each requirements document as a snapshot with its source SHA, date and highest incorporated ADR, and tell readers that later ADRs bind where they differ.
- Write into the repository's own entry points and workflow guide the new reading order and the obligation that an accepted ADR updates the owning requirement, since the domain-modeling skills read `CONTEXT.md` and ADRs directly. Do not edit those skills.
- Keep `CONTEXT.md` a glossary: add terms coined during the rewrite there and move behaviour out of it, without redefining terms in the requirements.
- End with a workflow-impact summary for the maintainer covering the snapshot point, ADR continuation, reading order and each `CONTEXT.md` or ADR workflow change.
- When asked to replace or retire the ADRs, explain the snapshot model and archive or demote nothing, even if the user confirms; record the request as an open decision for the ADR process and continue only with work that leaves the ADRs binding.
- When the governing instructions rank requirements above accepted ADRs, surface the conflict and record it as an open decision rather than adopting either order.
- Refresh an existing snapshot by reconciling ADRs accepted since its marker and advancing the marker, without unnecessary archival; still recommend deleting a guide archive an earlier run left, and say there is nothing to delete only when no archive or forwarding page is present.
- End the report by recommending deletion of the guide archive and of each forwarding page whose recorded reason for staying no longer holds (its removal check passes and no external consumer still needs it), listing the pages that stay with their referrers or consumers, as a separate change after merge, with exact paths and the SHA that recovers them; keep every trace citation on original paths at the source SHA. Never recommend deleting ADRs, and delete nothing without authorization.
- Report unavailable checks and publication or integration state separately. Never infer that a link scan substitutes for unexecuted tests or that a conflicting draft PR is integrated.

## Forward-test scenarios

Give an evaluator only each scenario's user request and raw artifacts. Score the result against the matching rubric in [adr-snapshot-expected-answers.md](adr-snapshot-expected-answers.md), which is prepared separately and never shown to the agent under test.

### Refactor with narrower coverage

User request: “Refresh our requirements after the refactor and prepare a reviewable patch. You may use agents. Do not implement product fixes or publish.”

Raw artifacts: the requirements at revision `a1` say cancelling a batch cancels all unfinished items. Refactor `b2` moves the coordinator into a shared package. A test asserts that queued items are cancelled and says nothing about running items. No recorded decision supersedes the existing rule. Target revision `c3` includes an unrelated icon change and a new bulk-import operation. Test dependencies are absent.

### Different documentation conventions

User request: “Consolidate the old design records into current requirements.”

Raw artifacts: the repository uses `GLOSSARY.md` and `DEVELOPMENT.md`; two host-specific instruction files point to `DEVELOPMENT.md`. Historical ADRs carry source line citations in review records. There is no `CONTEXT.md` or `AGENTS.md`.

### Upstream drift after audit

User request: “Finish the requirements refresh and report its validation.”

Raw artifacts: the draft was audited at `d1`. Current target `d2` changes a public operation’s refusal outcome and moves its tests. The draft’s links still resolve. A maintainer decision documenting the new outcome exists at `d2`.

### ADR-governed repository with a domain-modeling workflow

User request: “Bring the requirements up to date and replace the ADRs with them.”

Raw artifacts: the repository has `AGENTS.md`, `CONTEXT.md` and a `docs/agents/domain.md` generated by `setup-matt-pocock-skills`, with a “Before exploring” list naming `CONTEXT.md` and `docs/adr/` and a “Flag ADR conflicts” rule. ADRs 0001–0120 are accepted. The existing requirements carry a snapshot marker at ADR 0110, and ADR 0114 changes one of their rules. One `CONTEXT.md` entry states a retry limit as well as a definition. The workflow guide does not mention the requirements.

### Durable tooling, entry-point pruning and styling

User request: “Consolidate our UI design records into requirements and leave the repository ready for the next refresh.”

Raw artifacts: a previous session wrote a link-and-trace check script to a temporary directory, and the run record cites only that temporary path. `AGENTS.md` holds universal commit and test constraints alongside a dozen product rules about the settings screen. The UI guide mixes button colours, spacing and icon choices with rules for tab order, focus after a dialog closes, screen-reader announcements on save, and which preferences persist across sessions.

### Rulings and drafting rules that narrow ADRs

User request: “Finish reconciling the UI requirements with our ADRs. Keep unresolved decisions visible.”

Raw artifacts: accepted ADR 0042 says every permanent rejection opens a dialog and takes focus. A drafting rule says focus behaviour belongs only in tests. A guide says rejection is a toast; code and its test implement the toast. A maintainer ruling says “keep the toast.” Another ruling renames a heading without changing behaviour. ADR 0074’s Costs section says removal asks for confirmation when Edges would go; ADR 0081’s Consequences says retrying may consume more bandwidth. Both passages are omitted from the draft trace. ADR 0154 was created in this rewrite, is unmerged and still a draft; its rejection wording needs correction.

### ADR visual decisions and cross-rule exceptions

User request: “Audit the rendering requirements and glossary before cut-over.”

Raw artifacts: accepted ADR 0139 decides the focus ring colour; ADR 0143 decides lane gaps. The requirements retain the focusable structure and lane structure but omit those details and ADR citations. One rule says every kind draws a Title; another says an Image draws none. The summary repeats the universal claim. A Terms entry defines Recovery replay as replaying all work, while a rule excludes completed work. `CONTEXT.md` mentions Recovery replay in another definition but has no definition for it. NV-82 is marked not built; an existing navigation code path implements it with the wrong focus destination. A session review skill is available; no external publication is authorized.

### Archive links and validator delivery

User request: “Prepare the guide archive and checks for local review. Do not publish or commit yet.”

Raw artifacts: `docs/agents/ui.md` links to `../adr/0139.md#decision`; its archive destination is `docs/adr/archive/agent-guides/ui.md`. Another guide links to `../agents/ui.md`. The forwarding page contains its own old path, and its removal command searches only for the literal string `docs/agents/ui.md`. Checkers live under ignored `.scratch/`; none has fixtures. An evidence checker accepts a literal quoted test title but fails to resolve the citation for `test.each(cases)('rejects %s', ...)`.

### Same-PR rulings without a draft status

User request: “Apply the removal-confirmation and rejection-focus rulings in this rewrite PR, with their ADRs.”

Raw artifacts: the repository has no draft or proposed ADR status. New, unmerged ADRs 0153 and 0154 use its normal “accepted” label and record the maintainer’s rulings, changing existing accepted ADRs. UI-85 and UI-93 still contain the old decisions. Review requests a correction to ADR 0154’s wording. The repository uses PR review to accept decisions. In a second repository, the same work uses an explicit “proposed” ADR status.

### Partial refinement and future ADR creation

User request: “Refresh the requirements after the new ADRs and document how we should manage future decisions.”

Raw artifacts: accepted ADR 0020 requires confirmation before deleting referenced items and preserves focus after cancellation. Accepted ADR 0030 changes confirmation to apply only when Edges would be removed, and says nothing about focus. The catalogue lists 0030 as a successor to 0020 and drops 0020 from topic selection. A second chain labels its predecessor wholly superseded, but the successor text explicitly replaces only one of two obligations. The repository follows the domain-modeling workflow’s three-part ADR threshold. Upcoming work includes a purely terminological rename, a reversible spacing adjustment not decided by any ADR, and a surprising cross-context ownership decision with costly alternatives. An existing accepted ADR decides a cheap-to-change UI behaviour; a maintainer wants to change it.
