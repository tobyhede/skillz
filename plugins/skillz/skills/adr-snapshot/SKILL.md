---
name: adr-snapshot
description: Writes or refreshes requirements documents that restate a repository's accepted ADRs in current words, locked to the exact ADR versions they cover by a script-maintained lock file that CI checks. New ADRs need no other document edits; the check reports them as pending until the next refresh. Deletes only ADRs fully superseded by a later one, since git keeps them. Use when asked to consolidate ADRs and overlapping guides into current requirements, bring requirements up to date with ADRs written since, reconcile requirements with a refactored codebase, or make conflicting design documents consistent. Not for a routine wording fix, adding one requirement, summarizing one ADR, or implementation work.
---

# ADR snapshot

Requirements restate the accepted ADRs; they decide nothing. ADRs stay binding. `scripts/adr_snapshot.py` records which ADR versions the requirements cover and checks that record. Never hand-write revisions, dates, freshness markers or coverage lists: the script owns them.

A documentation rewrite does not authorize implementing defects, changing product decisions, publishing or merging. Ask only for decisions or actions outside the task's scope, and keep working on everything else while they are pending.

## Steps

1. **Set up the check.** Copy `scripts/adr_snapshot.py` from this skill to `scripts/adr_snapshot.py` in the target repository. If a copy exists with a lower `SCRIPT_VERSION` than this skill's, replace it; never replace a newer one. If there is no lock yet, run `python3 scripts/adr_snapshot.py init`, passing `--adrs` and `--requirements` globs when the repository does not use `docs/adr/[0-9]*.md` and `docs/requirements/*.md`. Run `check` and keep its output: on a refresh, its `pending` lines are the work list.

2. **Read the sources.** Read the pending ADRs (every ADR, on a first run), the requirements they affect, overlapping guides and `CONTEXT.md`. Treat code and tests as evidence of what is built, not of what is intended.

3. **Write the rules.** Use the rule format and document layout in [Format](references/format.md). Split topics by which part of the product owns the behaviour. Each rule links the ADRs it restates; the script counts those links as coverage. Terms go in `CONTEXT.md`, not in requirements. On a refresh, change only the rules the pending ADRs affect.

4. **Handle conflicts.** When sources disagree and the ADRs do not settle it, add the conflict to the document's open questions with a recommendation, or draft a new ADR when the user has decided. Never resolve a conflict by editing a requirement against an accepted ADR, and never edit an accepted ADR's decision.

5. **Delete superseded ADRs.** Delete an ADR only when a later ADR replaces every decision in it. Partly superseded ADRs stay. Cite the replacement in the rules, delete the file, and record it with `stamp --supersede OLD NEW`. Delete superseded guides outright; git keeps them.

6. **Stamp.** Run `python3 scripts/adr_snapshot.py stamp`, adding `--na PATH REASON` for each ADR no requirement needs to cite. It refuses to write the lock until every ADR is cited or has a reason, every requirements document that cites an ADR links the lock, and every ADR link resolves. Fix what it reports and rerun.

7. **Wire it in, once.** Add the check to CI and the reading-order line to the agent entry point, using the snippets in [Format](references/format.md). Skip whichever is already present.

8. **Deliver.** Run `check` and the repository's own documentation checks, and produce the change in the form the task authorizes. Report: topics written or refreshed, ADRs deleted as superseded, open questions, and each check with its observed result. A check that could not run is reported as not run.

**Done when** `check` reports `ok`, or only `pending` for ADRs merged after you stamped, and every open question is listed in its requirements document.
