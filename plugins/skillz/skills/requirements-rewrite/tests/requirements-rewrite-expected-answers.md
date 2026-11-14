# Expected answers for forward-test scenarios

These rubrics score the forward-test scenarios in [prompts.md](prompts.md). Never show them to the agent under test. Each item is a criterion the result must meet, not exact wording; a result passes a scenario when it meets every item and invents nothing the raw artifacts do not support.

## Refactor with narrower coverage

- Treats the missing assertion about running items as absent coverage, not proof of a defect, and inspects the moved coordinator's implementation before assigning an implementation status.
- Retains the cancel-all-unfinished rule as binding, since no decision supersedes it; records an implementation gap only if the code contradicts it, and records the coverage gap for running items either way.
- Assesses whether the cancellation rule applies to the new bulk-import operation from evidence, and raises a decision request with a recommendation if intent is unclear rather than silently extending or excluding it.
- Classifies the icon change as unrelated or presentation-only and does not reopen topics or add a requirement for it.
- Records that tests could not run because dependencies are absent, as a limit rather than a pass, and keeps any reusable check it writes somewhere durable.
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
- Reconciles ADRs 0111–0120, applies ADR 0114's change to the affected rule with a link to the ADR, and advances the snapshot marker to ADR 0120 with source SHA and date.
- Moves the retry limit out of `CONTEXT.md` into the owning requirement and keeps the definition in `CONTEXT.md`.
- Updates `AGENTS.md`, `docs/agents/domain.md` and the workflow guide with the reading order and the same-change rule, without editing the domain-modeling skills.
- Ends with a workflow-impact summary covering the snapshot point, ADR continuation, reading order and each `CONTEXT.md` or workflow change.

## Durable tooling, entry-point pruning and styling

- Moves the link-and-trace check into a durable location within scope, such as the repository or the run record, records its exact command, and removes the run record's dependence on the temporary path.
- Keeps only the universal commit and test constraints in `AGENTS.md`, moves the settings-screen rules to their owning requirements, and leaves a pointer with an explicit trigger.
- Leaves button colours, spacing and icon choices with code and tests, marking them presentation-only in the source disposition rather than writing requirements for them.
- Retains requirements for tab order, focus after a dialog closes, save announcements and which preferences persist, each with evidence or an explicit coverage gap.
