# Behavior cases

## Should activate

- “Replace our ADR history and overlapping product guides with requirements that state the current design.”
- “The architecture changed substantially. Reconcile the requirements with the new ownership boundaries and keep the implementation gaps visible.”
- “Make these conflicting design documents consistent.” If the repository or governing authority is not available, inspect the available context and ask for the missing source or decision before asserting a resolution.

## Should not activate

- “Fix the typo in the storage requirements heading.” Correct the wording and any affected anchor references without starting a rewrite.
- “Implement retry support for this operation.” Implementation alone is not a documentation authority migration.
- “Summarize this ADR.” A summary does not require consolidating the repository’s design authority.

## Expected behavior

- Record the actual repository, source commit and reviewed target commit, and inspect the governing instructions before choosing document owners.
- Use the repository’s existing glossary and agent entry-point filenames, including their mirror conventions. Do not introduce a new glossary merely to match a filename assumed by the workflow.
- Account for every inventoried source rule and preserve the distinction between intended behaviour, implemented behaviour and verified test coverage.
- Retain an unambiguously binding rule when the code differs; record the implementation gap rather than asking the maintainer to approve the same rule again.
- Resolve genuine intent conflicts with concrete evidence and a recommendation, and keep unresolved decisions explicit while continuing independent work.
- Keep styling-only treatment with code and tests while retaining requirements for meaning, reachability, focus, announcements and stored state.
- Inspect delegated diffs and use independent audit and fresh-reader exercises when delegation is available; identify a sequential review honestly when it is not.
- Classify upstream changes through a named revision and reconcile the affected topics. Do not call a stale but internally consistent draft current.
- Refresh existing requirements without unnecessary archival when authority and document locations have not changed.
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
