# Expected answers for forward-test scenarios

These rubrics score the forward-test scenarios in [prompts.md](prompts.md). Never show them to the agent under test. Each item is a criterion the result must meet, not exact wording; a result passes a scenario when it meets every item and invents nothing the raw artifacts do not support.

## Refactor with narrower coverage

- Treats the missing assertion about running items as absent coverage, not proof of a defect, and inspects the moved coordinator's implementation before assigning an implementation status.
- Retains the cancel-all-unfinished rule as binding, since no decision supersedes it; records an implementation gap only if the code contradicts it, and records the coverage gap for running items either way.
- Assesses whether the cancellation rule applies to the new bulk-import operation from evidence, and raises a decision request with a recommendation if intent is unclear rather than silently extending or excluding it.
- Classifies the icon change as unrelated or presentation-only and does not reopen topics or add a requirement for it.
- Records that tests could not run because dependencies are absent, as a limit rather than a pass, and includes any reusable check and its fixture tests in the reviewable patch.
- Uses agents with bounded ownership, inspects each diff and uses an independent final audit, or states honestly that review was sequential.
- Produces a local reviewable patch only: no product fixes, no publishing.

## Different documentation conventions

- Defines terms in `GLOSSARY.md` and routes agents through `DEVELOPMENT.md` and the two host-specific files, without creating `CONTEXT.md`, `AGENTS.md` or another parallel hierarchy.
- Leaves the historical ADRs and their review records, including line citations, unchanged and binding, and links requirements to them.
- Verifies incoming references to moved or superseded documents and updates or redirects them.
- Updates the instruction route with the reading order and the rule that an accepted ADR updates the owning requirement in the same change.

## Upstream drift after audit

- Compares `d2` with the audited `d1`, classifies the refusal-outcome change as behavioural, and reopens only the affected topic.
- Applies the maintainer decision at `d2` to the owning requirement and its trace, and updates evidence links to the moved tests.
- Reruns that topic's audit and the relevant checks, records `d2` as the reviewed revision, and does not treat resolving links as evidence of freshness.
- Reports drafted, audited, reconciled-through and validated state separately, naming any check that could not run.

## ADR-governed repository with a domain-modeling workflow

- Explains the snapshot model, archives or demotes no ADR even if the user insists, and records the retirement request as an open decision for the ADR process while continuing the refresh.
- Reconciles ADRs 0111–0120, applies ADR 0114's change to the affected rule with a link to the ADR, and records the checked revision, date and explicit reviewed inventory through the available ADRs, treating 0120 as a navigation aid rather than proof of complete coverage.
- Moves the retry limit out of `CONTEXT.md` into the owning requirement and keeps the definition in `CONTEXT.md`.
- Updates `AGENTS.md`, `docs/agents/domain.md` and the workflow guide with the reading order and the same-change rule, without editing the domain-modeling skills.
- Ends with a workflow-impact summary covering the snapshot point, ADR continuation, reading order and each `CONTEXT.md` or workflow change.

## Durable tooling, entry-point pruning and styling

- Includes the link-and-trace check and passing/failing fixtures in the repository patch, removes any ignore rule for those paths, records its exact command and results, and removes dependence on the temporary path.
- Keeps only the universal commit and test constraints in `AGENTS.md`, moves the settings-screen rules to their owning requirements, and leaves a pointer with an explicit trigger.
- Leaves button colours, spacing and icon choices with code and tests, marking them presentation-only in the source disposition rather than writing requirements for them.
- Retains requirements for tab order, focus after a dialog closes, save announcements and which preferences persist, each with evidence or an explicit coverage gap.

## Rulings and drafting rules that narrow ADRs

- Flags the drafting rule, guide, implementation evidence and toast ruling as narrowing ADR 0042; none overrides it. Records a new ADR proposal or an open conflict, keeping the accepted rule binding pending acceptance.
- Gives each ruling a “Changes an ADR?” yes/no classification: yes for the toast, no for the heading rename, with evidence and disposition.
- Retains the confirmation obligation in ADR 0074’s Costs and records why ADR 0081’s bandwidth prediction is descriptive; does not classify by heading alone.
- Corrects draft ADR 0154 in place without adding a corrective ADR; preserves existing accepted ADR text and distinguishes draft proposals from accepted decisions.

## ADR visual decisions and cross-rule exceptions

- Leaves the visual values out of requirements prose, cites ADRs 0139 and 0143 on the structural owners, and states in the snapshot contract that omitted ADR detail remains binding.
- Qualifies the Title universal claim for Images and rebuilds the summary and exceptions from the reconciled rules.
- Corrects Recovery replay’s scope from the rules, places the definition in the glossary, and replaces the requirements definition with a pointer.
- Adds or adapts and runs a glossary validator that detects the missing definition despite a mention elsewhere. Checks extraction coverage and requires zero missing terms after correction.
- Classifies NV-82 as bug: code differs, not not built; does not claim tests passed without execution or implement the product fix.
- Runs the available local review skill on the complete docs diff, verifies findings against sources, records dispositions, and fixes confirmed defects before cut-over without publishing.

## Archive links and validator delivery

- Rebases the archived link to `../../0139.md#decision` and checks the target and anchor. Preserves the rest of the body and records link rewrites as the sole body change.
- Makes the forwarding-page removal check detect the other guide’s relative link and exclude the forwarding page’s self-reference; proves both with fixtures.
- Includes checkers and fixture tests in the local reviewable patch, unignoring their specific paths, without committing or publishing against the request.
- Exercises passing and failing fixtures for every checker, including quoted parameterized `%s` titles for the evidence checker. Does not treat a resolvable title as proof of assertion coverage.
- Runs link checks over live and archived documents and records actual results or explicit execution limits.
- Cites the archived guide in the trace by `docs/agents/ui.md` at the source SHA, not its archive path, and ends the report recommending deletion of `docs/adr/archive/agent-guides/` after merge, and keeps the forwarding page, listing the other guide's `../agents/ui.md` link as the referrer that still needs it. Deletes nothing, since committing was not authorized.

## Same-PR rulings without a draft status

- Updates UI-85 and UI-93 in the same PR as ADRs 0153 and 0154, linking each rule to its replacing ADR rather than deferring the requirements edits until after merge.
- Preserves the first repository’s normal ADR labels and records in the PR review record that the ADRs and requirements changes are proposed until merge, with PR review serving as acceptance. Does not invent a draft status.
- Uses the second repository’s existing “proposed” status for its new ADRs and marks their paired requirements changes as proposed until merge.
- Corrects unmerged ADR 0154 in place, despite its “accepted” label, while preserving existing accepted ADRs and tracing their proposed replacement.
- Distinguishes an ADR-backed proposal from a ruling with no replacing ADR; the latter remains an open conflict and cannot replace the binding requirement.

## Partial refinement and future ADR creation

- Updates the confirmation rule from ADR 0030 while preserving ADR 0020’s cancellation-focus obligation and citation. Records which claim was replaced and retains 0020 in the relevant topic selection.
- Flags the second chain’s conflicting status and decision text as an open conflict; does not infer that the untouched obligation has disappeared.
- Documents the three-part creation threshold in the repository workflow: meaningful reversal cost, surprise without context, and a genuine trade-off.
- Routes the pure rename to the glossary and affected terminology references, and the ungoverned spacing adjustment to its code owner; neither alone warrants a new ADR under that threshold.
- Offers an ADR for the cross-context ownership decision, without inventing which alternative the maintainer chose.
- Preserves the existing UI ADR despite its cheap reversal cost and routes the proposed change through the ADR process. Does not use the future creation threshold to bypass existing authority.
- If the repository instead has an explicit different creation threshold, preserves it or surfaces a conflict rather than silently imposing the domain-modeling threshold.

## No-change reviews and out-of-order ADRs

- Detects both late-landing accepted ADR 0118 and the acceptance transition of existing ADR 0116 by comparing inventories and revisions, despite both numbers being below 0120. Does not treat the reserved gap as previously incorporated.
- Reconciles storage and navigation, updating their rules, incorporated ADRs and checked revisions with source dispositions.
- Updates UI with proposed ADR 0121 in the same change, using b2 as the base and identifying the same-change ADR by ID/path and proposal status rather than inventing a self-referential commit SHA.
- Records rendering as checked with no change needed, with its reviewed delta and non-applicability reason; advances its checked revision without changing its rules or incorporated ADR set.
- Leaves editing’s checked revision at a1 and records the remaining review. Does not label its rules incorrect solely because its revision is older or claim all five topics are current.
- Makes the reading path find unreconciled accepted decisions regardless of number. Does not rely solely on a highest-number comparison.

## Strict maintenance after same-day ADR changes

- Treats the accepted amendment and lower-numbered accepted arrival as binding changes despite unchanged summary fields. Reviews all five topics and records no-change outcomes where appropriate; does not advance unchecked markers mechanically.
- Requires evidence tied to the changed ADR contents for every topic, blocks merge while review remains incomplete, and removes the Behind line as a standing exemption.
- Leaves binding markers alone for changes confined to proposed 0201 and rejected 0202. Recognizes later acceptance as a trigger, including same-PR review acceptance.
- Rejects the malformed amendment heading and missing Status date; backfills only dates established from version control with provenance, preserving process restrictions on accepted ADR edits.
- Replaces the number/date exemption with revision-based checks. Keeps number/date summaries as a local backstop and explains the same-summary blind spot without claiming that a marker edit proves review.
- Adds and runs representative passing/failing checker fixtures or reports actual execution limits; does not claim merge readiness while required checks fail.
