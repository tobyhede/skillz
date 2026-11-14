# Audit

Use this after drafting and again for topics affected by upstream changes; the fresh-reader questions and expected answers are fixed earlier, during Inventory. Mechanical checks and semantic review answer different questions.

## Coverage and consistency

For each source disposition, check that the destination preserves its intended obligation or that the omission has a defensible reason. Review exceptions and cross-topic operations as well as the ordinary path.

Check especially:

- Code differs from a ruling but the requirement was quietly rewritten to match code.
- A not-built requirement disappeared because the implementation lacks it.
- A newer name was substituted without checking whether the concept changed.
- “Presentation-only” removed reachability, focus, meaning or stored behaviour.
- Two docs own the same rule or assign different outcomes to the same action.
- Old guidance still appears binding through an agent entry point, a skill or a diagnostic.
- Glossary entries carry an operational policy that can drift from its owner.
- A rationale asserts an unverified mechanism, such as how an exception affects the UI.

Verify code and assertions directly; an author's or subagent's summary is not evidence by itself. Return findings with the scenario, affected rule, source evidence and consequence.

## Fresh-reader exercises

Give an independent reader the entry-point instructions and a realistic task. Allow navigation through their pointers, without supplying the desired document or answer. Ask the reader to identify the owning rule, intended outcome and known implementation gap, with citations.

Choose scenarios that cross ownership boundaries: recovery invalidating pending work, deletion affecting references, a URL changing selection, or a child operation inheriting its caller’s policy. Include an ordinary task to check that the reading path is not optimized only for edge cases.

Write the scenarios and their evidence-backed expected answers from the sources during Inventory, before drafting, so the draft cannot shape them; record them in the run record. Compare the reader's answer with that fixed expected answer. Distinguish failure to find a rule from ambiguity in the rule and from a wrong rule. Fix the pointer before inlining a whole document when discovery is the failure. Rerun affected exercises after correction.

## Freshness

Compare the recorded source and target revisions. Classify relevant changes by affected topics, not just file overlap: a refactor can move the evidence or change ownership without touching documentation.

Record which old rulings still apply, which have been explicitly superseded and which need a new decision. Do not treat an old ruling as universal across changed product concepts. Close the audit against a named target SHA. If upstream cannot be checked, qualify freshness rather than claiming the docs describe current main.

## Mechanical evidence

Use existing validators where available. Check rule definitions and references, duplicate identifiers, removed-rule references, links and anchors, archive integrity, agent-file mirrors or symlinks, and the complete proposed diff's whitespace.

Read validators before relying on them. Repeated IDs in a Bugs section may be references rather than definitions; historical references may need explicit exemptions. Keep exemptions narrow and visible. These checks establish structural consistency, not semantic completeness.
