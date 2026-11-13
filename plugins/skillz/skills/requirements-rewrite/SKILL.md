---
name: requirements-rewrite
description: Consolidates ADRs and overlapping guides into current requirements, or reconciles an existing requirements set after substantial refactoring. Use for a documentation authority migration across topics, not a routine wording fix or implementation task.
---

# Requirements rewrite

Produce one current account of intended behaviour, with implementation gaps explicit and historical evidence recoverable. Reuse prior rulings as evidence; reassess their applicability to the current product. Choose document boundaries from current ownership rather than copying the previous run's topic count.

Respect the task's existing scope and authorization. A documentation rewrite does not itself authorize implementing recorded defects, changing product decisions, publishing, or merging. Ask only for missing decisions or actions outside the authorized scope; continue independent work while they are pending.

## 1. Baseline

Identify the actual repository, target branch, source commit, current vocabulary and governing instructions. Read the existing requirements, ADR catalogue and refactor records to establish their authority. Treat the current code as evidence of implementation, not automatic authority over intent.

Choose a durable run-record location following repository conventions. Record source and target SHAs, scope, document owners, decisions, exact validation commands and next actions using [Evidence and run records](references/evidence.md). Establish which checks can run before drafting depends on them. Keep reusable validators in a maintained repository or skill location, not only a temporary directory.

**Done when:** the source revision, authority order, scope, record location and verification capability are explicit. Unavailable upstream access or checks are recorded as limits, not inferred successes.

## 2. Inventory

Account for requirements, ADRs, product guides, glossary obligations and relevant refactor decisions. Inspect incoming references from agent instructions, skills, diagnostics, source comments and documentation tests. Assign each source rule a disposition and each retained rule one authoritative owner. Keep engineering workflow and tooling guidance distinct from product behaviour.

**Done when:** every inventoried source rule is retained, superseded, redirected, historical, presentation-only or an explicit open question, with a reason and destination where applicable. The topic split follows ownership and the tasks that should cause a reader to open each doc.

## 3. Reconcile

For disagreements, put the source claim beside the code and test evidence. Distinguish intended behaviour, observed implementation and verified coverage. Present unresolved choices as concrete author actions and outcomes, with a recommendation and its consequences; keep rule IDs subordinate to the wording.

Obtain a ruling when the evidence and established authority cannot decide a behavioural conflict. An implementation discrepancy against an unambiguously binding rule needs a gap recorded, not renewed approval of that rule. Record a new answer once and apply it to every affected owner and trace. A passing test establishes what it asserts, not that the asserted behaviour is the intended design.

**Done when:** every disagreement has evidence and a disposition. Settled topics may proceed independently; an unresolved decision cannot be presented as binding or the whole rewrite declared complete.

## 4. Draft

Use current names and present-tense rules. Co-locate a rule, its reason, qualifications, implementation status and evidence. Preserve accepted-but-unbuilt behaviour unless explicitly retired. Keep change history in traces, decisions and commits rather than the live rules.

Define terms in the repository’s glossary; put operational obligations in requirements. Route tasks from its agent entry points with explicit triggers, retaining only universal constraints there. Use the repository’s actual filenames and mirror conventions rather than creating new ones. Read manifests, configuration and command help for facts they already own; document the non-obvious convention or gotcha instead of duplicating those inventories.

Styling-only choices belong with code and tests. Retain requirements for meaning, visible structure, reachability, focus, announcements and stored state. Preserve established rule identities; leave tombstones or an explicit old-to-new mapping when removing or moving rules.

**Done when:** every retained rule has one owner and traceable evidence or an explicit coverage gap; pointers cover the relevant task branches; glossary and live rules have distinct jobs.

## 5. Audit and refresh

Use [Audit](references/audit.md) for coverage, consistency and fresh-reader checks. Where delegation is available, assign bounded topic ownership, inspect each resulting diff yourself, and use an independent agent for the final audit. Otherwise record that independence was unavailable and perform the same checks without calling them independent.

At decision checkpoints and before cut-over, compare the target branch with the recorded baseline. Classify changes affecting terminology, behaviour, ownership, evidence or pointers. Reconcile affected topics against an explicitly recorded newer revision and rerun their audits; unrelated changes need no full restart. If the tree is moving too quickly, agree a bounded review snapshot and report its limits.

**Done when:** audit findings are resolved and all target changes through the recorded review SHA are classified and reconciled where relevant. Link checks alone do not satisfy this step.

## 6. Cut over and report

When authority or document locations change, follow [Cut-over](references/cut-over.md) to switch authority, preserve history and verify consumers. For an existing-requirements refresh, mark unnecessary archive or authority changes not applicable and verify the affected reading paths. Use approval already provided; if a gate remains explicit, prepare the complete reviewable result before requesting it.

Report separately: drafted, independently audited, reconciled through a target SHA, validated by named checks, and published or integrated if requested. State failed and unavailable checks. Update the run record so another session can resume without a temporary path or conversation memory.

**Done when:** the current reading path reaches the requirements, historical material has no competing authority, required checks have observed outcomes, and any authorized delivery is complete. A draft PR with conflicts is published work, not completed integration.
