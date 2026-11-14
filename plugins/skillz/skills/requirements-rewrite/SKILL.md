---
name: requirements-rewrite
description: Writes requirements that restate accepted ADRs and overlapping guides in current words as a snapshot at a recorded revision, or refreshes an existing snapshot after substantial refactoring or new ADRs. ADRs stay the binding, append-only history, and the repository's CONTEXT.md and ADR workflow are updated to route through the snapshot. Use when asked to consolidate design records into current requirements, bring requirements, specs or current contracts up to date with ADRs written since, reconcile requirements with a refactored codebase, or make conflicting design documents consistent across topics. Not for a routine wording fix, summarizing one ADR, or implementation work.
---

# Requirements rewrite

Produce one current account of intended behaviour, with implementation gaps explicit and historical evidence recoverable. ADRs are the historical authority: they stay binding and the repository keeps writing them. The requirements are a snapshot that restates them as of a recorded revision; read [Snapshot model and workflow impact](references/snapshot-model.md) before Baseline is done. Reuse prior rulings as evidence; reassess their applicability to the current product. Choose document boundaries from current ownership rather than copying the previous run's topic count.

Respect the task's existing scope and authorization. A documentation rewrite does not itself authorize implementing recorded defects, changing product decisions, publishing, or merging. Ask only for missing decisions or actions outside the authorized scope; continue independent work while they are pending.

**Inputs:** the repository and target branch; the task's scope and authorization; the existing requirements, ADR catalogue, overlapping guides and `CONTEXT.md`; and the ADR and domain-modeling workflow the repository follows.

**Deliverables:** requirements documents with snapshot markers; the source disposition and trace; a durable run record; decision requests for unresolved conflicts; edits to the agent entry points, `docs/agents/domain.md` or its equivalent, and the workflow guide; the workflow-impact summary; and a final report of audit, freshness, validation and delivery state.

## 1. Baseline

Identify the actual repository, target branch, source commit, current vocabulary and governing instructions. Read the existing requirements, ADR catalogue and refactor records to establish how they relate. Treat the current code as evidence of implementation, not automatic authority over intent.

Check that the governing instructions agree with the snapshot model, and identify the ADR workflow the repository follows, including `CONTEXT.md` and any domain-modeling skills its agents use. If the instructions rank requirements or other documents above accepted ADRs, do not silently adopt either order: surface the conflict and record it as an open decision for the repository's ADR process. Never archive, rewrite or demote ADRs here. If the user asks to retire them, explain the snapshot model; if they still want it, archive or demote nothing, record the request as an open decision for the ADR process, and continue only with work that leaves the ADRs binding.

Choose a durable run-record location following repository conventions. Record source and target SHAs, scope, document owners, decisions, exact validation commands and next actions using [Evidence and run records](references/evidence.md). Establish which checks can run before drafting depends on them. Keep reusable validators somewhere durable within the authorized scope, such as the repository or the run record, not only a temporary directory.

**Done when:** the source revision, the instructions' agreement with the snapshot model or a recorded conflict, the ADR workflow, scope, record location and verification capability are explicit. Unavailable upstream access or checks are recorded as limits, not inferred successes.

## 2. Inventory

Account for requirements, ADRs, product guides, glossary obligations and relevant refactor decisions. Inspect incoming references, using the list in [Cut-over](references/cut-over.md). Assign each source rule a disposition and each retained rule one authoritative owner. Keep engineering workflow and tooling guidance distinct from product behaviour. Before drafting, write each topic's fresh-reader questions and their expected answers from the sources, as [Audit](references/audit.md) describes, and record them in the run record.

**Done when:** every inventoried source rule is retained, superseded, redirected, historical, presentation-only or an explicit open question, with a reason and destination where applicable. The topic split follows ownership and the tasks that should cause a reader to open each doc. Each topic's reader questions and expected answers are recorded.

## 3. Reconcile

For disagreements, put the source claim beside the code and test evidence. Distinguish intended behaviour, observed implementation and verified coverage. Present unresolved choices as concrete author actions and outcomes, with a recommendation and its consequences; keep rule IDs subordinate to the wording.

Obtain a ruling when the evidence and established authority cannot decide a behavioural conflict. An implementation discrepancy against an unambiguously binding rule needs a gap recorded, not renewed approval of that rule. Record a new answer once and apply it to every affected owner and its trace (the source-to-requirement mapping in the run record). A requirement cannot override an accepted ADR: a resolution that changes what an ADR decides goes through the repository's ADR process, not a requirement edit. A passing test establishes what it asserts, not that the asserted behaviour is the intended design.

**Done when:** every disagreement has evidence and a disposition. Settled topics may proceed independently; an unresolved decision cannot be presented as binding or the whole rewrite declared complete.

## 4. Draft

Use current names and present-tense rules. Give each requirements document the snapshot marker from [Snapshot model and workflow impact](references/snapshot-model.md), and link each rule to its source ADRs. Co-locate a rule, its reason, qualifications and evidence. Record implementation status beside the rule only where the repository keeps status in requirements; otherwise list accepted-but-unbuilt behaviour apart from the rules and link each gap to where the repository tracks build status, such as delivery issues. Preserve accepted-but-unbuilt behaviour unless explicitly retired. Keep change history in traces, decisions and commits rather than the live rules.

Define terms in the repository’s glossary (usually `CONTEXT.md`); put operational obligations in requirements. Route tasks from its agent entry points with explicit triggers, retaining only universal constraints there. Use the repository’s actual filenames and mirror conventions rather than creating new ones. Read manifests, configuration and command help for facts they already own; document the non-obvious convention or gotcha instead of duplicating those inventories.

Styling-only choices belong with code and tests. Retain requirements for meaning, visible structure, reachability, focus, announcements and stored state. Preserve established rule identities; leave tombstones or an explicit old-to-new mapping when removing or moving rules.

**Done when:** every requirements document carries its snapshot marker; every retained rule has one owner, links to its source ADRs, and traceable evidence or an explicit coverage gap; pointers cover the relevant task branches; glossary and live rules have distinct jobs.

## 5. Audit and refresh

Use [Audit](references/audit.md) for coverage, consistency and fresh-reader checks. Where delegation is available, assign bounded topic ownership, inspect each resulting diff yourself, and use an independent agent for the final audit. Otherwise record that independence was unavailable and perform the same checks without calling them independent.

At decision checkpoints and before cut-over, compare the target branch with the recorded baseline. Classify changes affecting terminology, behaviour, ownership, evidence or pointers. Reconcile affected topics against an explicitly recorded newer revision and rerun their audits; unrelated changes need no full restart. If the tree is moving too quickly, agree a bounded review snapshot and report its limits.

**Done when:** audit findings are resolved and all target changes through the recorded review SHA are classified and reconciled where relevant. Link checks alone do not satisfy this step.

## 6. Cut over and report

When the reading path or document locations change, follow [Cut-over](references/cut-over.md) to route readers to the requirements, update the ADR and `CONTEXT.md` workflow, and verify consumers. For an existing-snapshot refresh, advance the markers of the reconciled topics and verify the affected reading paths. Use approval already provided; if a gate remains explicit, prepare the complete reviewable result before requesting it.

Report the workflow impact as [Snapshot model and workflow impact](references/snapshot-model.md) describes, then report separately: drafted, independently audited, reconciled through a target SHA, validated by named checks, and published or integrated if requested. State failed and unavailable checks. Update the run record so another session can resume without a temporary path or conversation memory.

**Done when:** the current reading path reaches the requirements and then ADRs newer than each marker; no ADR was archived, rewritten or demoted; superseded non-ADR guides route to their owner; the repository's workflow guide states how new ADRs reach the snapshot and lists exactly the topics that have requirements; the maintainer has the workflow-impact summary; required checks have observed outcomes, and any authorized delivery is complete. A draft PR with conflicts is published work, not completed integration.
