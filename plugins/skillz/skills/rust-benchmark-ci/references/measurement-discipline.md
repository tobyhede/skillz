# Measurement discipline: which numbers decide what

## Resolution by source

| Source | Can decide | Cannot decide |
|---|---|---|
| CI ratio gate (previous point) | Blow-ups (alert at 150%, fail at 300%) | Anything under tens of %; cumulative drift; accepted regressions |
| CI floors | "Still as good as agreed" for named benches | Unguarded benches |
| Two separate CI runs, control-normalised | Effects of roughly 15–20%+ | Small effects |
| Paired interleaved A/B inside one CI job | Small effects (a pre-declared ~5% rule) | Cross-runner absolute numbers |
| One local run | Shape (growth curve), ratio between variants in one process | Anything about CI numbers |

Local and CI ratios disagree: 4.03× vs 5.58× for one change, 3.27× vs 3.68× for its fix. Two local runs reversed sign on a `Cargo.lock`-only change.

## Evidence labels

Label every performance statement in a PR, ticket or acceptance record with one of:

- **measured**: a number from a run, with the run named (workflow run id, or local command plus machine and load).
- **derived**: computed from measured numbers (a ratio, a control-normalised speedup, ns per item read off a size series). Name the inputs.
- **hypothesized**: a proposed mechanism not yet separated from alternatives by an experiment.
- **unvalidated**: a change that was made but whose effect was not measured. With no run, say so instead of quoting a number.

Keep workload changes (new fixtures, new sizes, a changed budget) distinguishable from performance changes; a number that moved because the bench changed is not a speedup.

For a regression or an optimisation claim, keep a short evidence ledger and leave alternatives open until an experiment separates them:

| Observation | Scope and denominator | Hypothesis | Discriminating experiment | Disconfirming result |
|---|---|---|---|---|
| `paint_derive/fitted` 5.5× slower per cell | CI, one bench, per Cell | Map growth and rehash dominates | Ablation without the map, plus a sampling profile | Cost stays with the map removed |

Keep disconfirmed rows; they show what was ruled out.

## Control normalisation across CI runs

Main's own series moved ~2× on unchanged code. Compare candidate to baseline as a raw ratio and divided by the geometric mean of the same ratio over benchmarks the change cannot touch (the source project used 18). Report both.

## Reruns

Rerun to test whether an apparent regression keeps its sign; a real cost does not reverse between two runs of one commit. Never rerun until green.

## Paired A/B inside CI

Used when local runs were unreliable and the effect was small:
- Build both variants in one job.
- Run in a fixed interleaved order (A B B A B A A B), same process conditions.
- Compare within-job ratios only.
- Run three jobs.
- Declare the decision rule before results (e.g. ≥5% in the same direction in all three jobs), otherwise INCONCLUSIVE. State that this is "a practical consistency rule, not a statistical significance claim."

## Local runs

When a local experiment is the right tool (diagnosis, curve shape):
- Record machine load; skip runs above ~4 load average.
- Order runs pre, tip, tip, pre.
- Give each commit its own `CARGO_TARGET_DIR` and hash binaries: a shared target dir once measured the same binary twice.
- Rebuild old code from `git archive` of the old SHA, not by checking out in the working tree.
- Discard runs whose interval is wider than a few percent rather than averaging them.
- Under load, interleave variants in one process and take the minimum of criterion's raw samples: "interference only adds time."
- Re-measure after a history rewrite.
- For a small effect, use the size with the tightest spread.

## Diagnosing a regression

1. Confirm it on CI with a rerun and control normalisation.
2. Read the size series: ns per item flat = linear, growing ×4 per ×4 step = quadratic.
3. Apportion with ablation variants (remove one piece at a time) plus a sampling profile (samply, perf; build with `[profile.profiling]`). In the source project the profile showed `reserve_rehash` at 26–29%: map growth, not hashing, was the cost. "Removing the map is the fix; making the lookup cheaper is not."
4. Commit the ablation harness or record exactly how to rebuild it; the source project did not, and that profile cannot be re-run.
5. Temporary operation-count instrumentation (counting calls per input size) is a cheap way to confirm complexity; do not ship it.
6. Record the diagnosis in the evidence ledger (§ Evidence labels), disconfirmed rows included.

## Acceptance record

For a change that claims a performance effect, record:
- baseline SHA, and the workflow run that stored the point it compared against;
- candidate SHA and at least two CI attempts;
- every protected series, not only the target (reject a fix that slowed render frames 5–17% while improving paint, despite a green gate);
- raw and control-normalised speedups;
- reruns and why;
- floors added or changed, with runner and source.

## Time arithmetic in tests

For deadline or scheduling logic, test the arithmetic with chosen `Duration` values; never sleep in CI.
