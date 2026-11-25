# Format

Read this when writing requirements (step 3) and when wiring the check in (step 7). Follow the repository's own filenames and conventions where they already exist.

## Requirements document

Start each document with the contract line. It must link the lock file, or `check` fails:

```markdown
# Batch operations

> Restates the ADRs recorded in [snapshot.lock.json](snapshot.lock.json). ADRs added or changed since then bind where they differ; `python3 scripts/adr_snapshot.py check` lists them.
```

Then the rules, an optional **Not built** list, and an **Open questions** list.

## Rule

One rule per entry, present tense, current names:

```markdown
**Cancelling a batch cancels every unfinished item.** Reason: a partly cancelled batch leaves authors unsure which items will still run. Sources: [ADR 0042](../adr/0042-cancel.md), [ADR 0114](../adr/0114-bulk.md). Evidence: `BatchCoordinator.cancel`; test `cancels queued items` covers queued items only. Gap: running items are not cancelled.
```

- **Sources** are relative links to ADR files. They are what the lock counts as coverage, so link every ADR the rule restates.
- **Evidence** names code by path or symbol and tests by name. Missing test coverage is a gap, not proof the behaviour is absent.
- **Gap** appears only when code differs from the rule. Keep a rule whose behaviour is not built: an accepted ADR is not retired by missing code.
- Each rule has one owning document. Link to it from elsewhere instead of restating it.

## What goes where

| Content | Belongs in |
| --- | --- |
| Task pointers and universal constraints | Agent entry point (`AGENTS.md`, `CLAUDE.md`) |
| Term definitions | `CONTEXT.md` or the repository's glossary |
| Current obligations | Requirements |
| Reasoning, rejected alternatives, history | ADRs |
| Commands, versions, configuration values | Their manifest, config file or command help |
| Styling detail an ADR decides | The ADR; cite it on the rule for the visible structure |

## Open question

```markdown
- **When a batch is cancelled, should running items stop too?** ADR 0042 says every unfinished item; ADR 0114 says queued items only. Code stops queued items only. Recommendation: stop running items, matching ADR 0042, because ADR 0114 does not say it replaces it. Resolve by a new ADR.
```

## Agent entry point

Add one line where the entry point routes documentation tasks:

```markdown
Before changing behaviour, read the owning requirement in `docs/requirements/`, then any ADR that `python3 scripts/adr_snapshot.py check` lists as pending; a pending ADR overrides the requirement where they differ. Writing an ADR needs no requirements edit.
```

## CI

Add a step to an existing workflow that runs on pull requests, or create one:

```yaml
- name: Check requirements snapshot
  run: python3 scripts/adr_snapshot.py check --github
```

Pending ADRs appear as warnings and do not fail the build. Add `--fail-stale` only if the repository wants every ADR folded into the requirements before merge.
