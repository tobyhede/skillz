# Behavior cases

## Should activate

- “Consolidate our ADRs and overlapping product guides into requirements that state the current design.”
- “We've written another dozen ADRs since the requirements were last updated. Bring them up to date.”
- “Our specs are out of date with the ADRs.”
- “The architecture changed substantially. Reconcile the requirements with the new ownership boundaries and keep the implementation gaps visible.”
- “Make these conflicting design documents consistent.” If the repository or the conflicting sources are not available, ask for them before asserting a resolution.

## Should not activate

- “Fix the typo in the storage requirements heading.” Correct the wording without a refresh.
- “Implement retry support for this operation.”
- “Summarize this ADR.”
- “Record an ADR for this decision.” Writing an ADR needs no requirements edit; the check reports it as pending.
- “Add a requirement for feature Y.” Add the single rule to its owning document, linking its source ADR, and run `stamp` if the repository has a lock.

## Expected behavior

- Copies `scripts/adr_snapshot.py` into the target repository, runs `init` only when no lock exists, and uses `check`'s pending list as the refresh work list.
- Never hand-writes revisions, dates, freshness markers or ADR coverage lists; the lock file is written only by `stamp`.
- Writes rules in the format from `references/format.md`, each linking the ADRs it restates, with the contract line linking the lock at the top of every requirements document.
- Leaves accepted ADRs in place and unedited, except deleting an ADR that a later ADR fully replaces, recorded with `stamp --supersede` during a refresh, or with `supersede OLD NEW` alone in a pull request between refreshes, which leaves pending ADRs pending. A partly superseded ADR stays.
- Records unresolved conflicts as open questions with a recommendation, never by editing a requirement against an accepted ADR.
- Marks ADRs that no requirement needs with `stamp --na` and a specific reason instead of citing them artificially.
- Adds the CI step and the agent entry-point line once, without editing other workflow guides or the domain-modeling skills.
- Does not require or add a requirements update to an ADR-only change.
- On a refresh, changes only the rules affected by pending ADRs.
- Reports each check with its observed result, and reports a check that could not run as not run.
- Does not implement recorded gaps, publish or merge unless the task authorizes it.
