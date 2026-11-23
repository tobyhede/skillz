# Audit

Use this after drafting and again for topics affected by upstream changes; the fresh-reader questions and expected answers are fixed earlier, during Inventory. Mechanical checks and semantic review answer different questions.

## Coverage and consistency

For each source disposition, check that the destination preserves its intended obligation or that the omission has a defensible reason. Review exceptions and cross-topic operations as well as the ordinary path.

Check placement against this table, using the repository's own filenames:

| Content | Belongs in |
| --- | --- |
| Task pointers and universal constraints | Agent entry points |
| Term definitions and distinctions | Glossary (usually `CONTEXT.md`) |
| Operational obligations | Requirements |
| Reasoning, rejected alternatives and history | ADRs |
| Commands, packages, scripts and configuration values | Their own manifest, config file or command help |
| Build status and implementation gaps | Where the repository tracks delivery |

Check especially:

- Code differs from a ruling but the requirement was quietly rewritten to match code.
- A not-built requirement disappeared because the implementation lacks it.
- A newer name was substituted without checking whether the concept changed.
- “Presentation-only” removed reachability, focus, meaning or stored behaviour.
- Two docs own the same rule or assign different outcomes to the same action.
- Old guidance still appears binding through an agent entry point, a skill or a diagnostic.
- An agent entry point or guide lists commands, packages, scripts or configuration values that their manifest, config file or command help already owns.
- Glossary entries carry an operational policy that can drift from its owner.
- A rationale asserts an unverified mechanism, such as how an exception affects the UI.

Scan every “every”, “never”, “all” and “only” claim against the other rules and their exceptions, within and across documents. Qualify a universal claim at its owner when an exception applies; for example, “every kind draws a Title” must account for an Image rule that draws none. Rebuild summaries, Exceptions and Terms sections from the reconciled rules, checking their scopes and definitions rather than carrying old prose forward. Terms sections should point to glossary definitions, not introduce parallel definitions.

Verify code and assertions directly; an author's or subagent's summary is not evidence by itself. Return findings with the scenario, affected rule, source evidence and consequence.

## Automated review

Before cut-over, run the repository’s review bot or an available session review skill on the complete documentation diff when either is available. Use a local review skill when invoking a bot would require publication outside the task’s authorization. Verify every finding against the sources and reviewed revision, record its disposition, fix confirmed defects, and rerun affected checks. Record the reviewer, revision, results and any access or execution limit; an unavailable review is not a pass.

## Fresh-reader exercises

Give an independent reader the entry-point instructions and a realistic task. Allow navigation through their pointers, without supplying the desired document or answer. Ask the reader to identify the owning rule, intended outcome and known implementation gap, with citations.

Choose scenarios that cross ownership boundaries: recovery invalidating pending work, deletion affecting references, a URL changing selection, or a child operation inheriting its caller’s policy. Include an ordinary task to check that the reading path is not optimized only for edge cases.

Write the scenarios and their evidence-backed expected answers from the sources during Inventory, before drafting, so the draft cannot shape them; record them in the run record. Before drafting, run each exercise once against the existing reading path and record the result as the baseline; where that reader's cited answer differs from the expected answer, decide whether the old structure fails discovery or the expected answer is wrong before drafting. After drafting, compare the reader's answer with that fixed expected answer. Distinguish failure to find a rule from ambiguity in the rule and from a wrong rule. Fix the pointer before inlining a whole document when discovery is the failure. Rerun affected exercises after correction.

## Freshness

Compare the recorded source and target revisions. Classify relevant changes by affected topics, not just file overlap: a refactor can move the evidence or change ownership without touching documentation. List source documents added or renamed since the baseline, for example `git diff --name-status --diff-filter=AR <baseline>..<target> -- <doc paths>`, and inventory any new guide, glossary file or refactor record before closing the audit.

Compare the ADR inventory and acceptance state at each topic’s checked revision with the target and proposed diff, without filtering by ADR number. Include lower-numbered late arrivals and existing proposals that became accepted. Resolve renamed or removed inventory entries explicitly. Record each topic as changed and reconciled, checked with no change needed, or not checked/unresolved, following the snapshot-model marker rules. Verify that every advanced checked revision has evidence for its outcome; unchanged prose alone proves neither review nor staleness. For strict maintenance, exercise the checks and fixtures in the snapshot-model reference and verify that every required topic is reconciled before merge.

Record which old rulings still apply, which have been explicitly superseded and which need a new decision. Do not treat an old ruling as universal across changed product concepts. Close the audit against a named target SHA. If upstream cannot be checked, qualify freshness rather than claiming the docs describe current main.

## Mechanical evidence

Use existing validators where available. Check rule definitions and references, duplicate identifiers, removed-rule references, links and anchors, archive integrity, agent-file mirrors or symlinks, and the complete proposed diff's whitespace.

Add or adapt a glossary validator to the repository’s actual Markdown conventions. It must enumerate terms defined in requirements (including inline definitions and Terms sections), compare them with definition entries in `CONTEXT.md` or the repository’s glossary, and report missing terms with source locations; a mention alone is not a glossary definition. Inspect extraction coverage so a zero count cannot result from matching no definitions. Move definitions to the glossary and link them from requirements, then require zero missing terms before completion.

Track every validator and its tests in version control, unignoring their specific paths where necessary. Document inputs, outputs, dependencies and failure behaviour, and give each validator a small fixture test with a passing case and a deliberately failing case. Include the actual syntax it checks: glossary inline definitions, moved relative links and, for evidence checkers, `%s` in quoted parameterized test titles. Run the fixtures and validators against the proposed tree, recording both results.

Read validators before relying on them. Repeated IDs in a Bugs section may be references rather than definitions; historical references may need explicit exemptions. Keep exemptions narrow and visible. These checks establish structural consistency, not semantic completeness.
