---
name: rust-benchmark-ci
description: This skill should be used when the user asks to "add benchmarks", "set up criterion", "add a benchmark gate to CI", "track performance regressions", "add github-action-benchmark", "add benchmark floors", "publish a benchmark series to gh-pages", "count allocations in tests", "why is the benchmark job green but empty", "make the bench job faster", "my benchmarks are noisy in CI", "cargo bench in GitHub Actions", "criterion benchmarks", "benchmark regression", "performance gate", or is deciding whether a benchmark number proves a performance claim. Covers criterion harness setup, a github-action-benchmark regression gate with committed floors, allocation-count series, and measurement discipline.
version: 0.1.0
---

# Rust benchmarks with a CI regression gate

## Purpose

Set up benchmarks that a CI gate can trust, and avoid the failure modes that make a benchmark gate report green while measuring nothing. Every rule here was paid for by a real failure in a Rust workspace (criterion 0.8, `benchmark-action/github-action-benchmark`, GitHub-hosted `ubuntu-latest`, gh-pages series). The harness lessons are Rust-specific; the gate, noise and evidence lessons apply to any language.

This skill owns the operational layer: harness configuration, CI wiring, baselines, floors, time budget, and which numbers decide what. Evidence labels and the evidence ledger are in `references/measurement-discipline.md`. For general performance method (diagnosis, budgets, paired-run statistics, Amdahl and roofline models, allocation strategy, SIMD) defer to the `performance-engineering` skill; do not restate it.

## The one idea to keep

A CI benchmark gate on shared runners is a **blow-up alarm, not a precision instrument**. Hosted runners vary by tens of percent between runs and roughly 2x between runner classes. Design for that explicitly:

- Set thresholds above runner noise (proven settings: alert 150%, fail 300% for wall-clock; alert 110% for deterministic counts, with a 125% fail that only bites once `fail-on-alert` is turned on).
- Write the blind spots down as design: a 10% regression passes; ten commits at +20% each never trip a previous-point gate; a first run with no baseline passes.
- Size criterion's measurement budget to what the threshold can resolve, not to criterion's defaults.
- Back the ratio gate with committed absolute floors, because a previous-point comparison silently re-baselines on every merged regression.
- Decide small effects (under ~20%) only with paired, interleaved A/B runs inside one CI job, never by comparing two separate runs, and never by comparing a local number with a CI number.

## Setup order for a new project

Work through these in order. Each step links to its detail.

1. **Choose what to measure** (`references/harness.md` § What to benchmark). Real production paths through public APIs, on realistic fixtures. No micro-benchmarks of helpers; no benchmarks of unimplemented paths; nothing dominated by harness (GPU, disk, UI context).
2. **Add criterion correctly** (`references/harness.md` § Cargo configuration). `default-features = false, features = ["cargo_bench_support"]`, `harness = false` on every `[[bench]]`, `bench = false` on every `[lib]` and `[[bin]]`, `[profile.bench]` with thin LTO and symbols kept.
3. **Write benches with the idioms** (`references/harness.md` § Idioms; template `assets/bench_template.rs`). `black_box` inputs and outputs, `iter_batched` for per-iteration inputs, `PerIteration` when setup restores mutated state, ×4 size series, self-validating fixtures, stable `<area>_<op>/<param>` names.
4. **Create one command** used identically locally and in CI, with the budget named on the command line (`assets/mise-tasks.toml`). Include `--output-format bencher`. Ban `--quick`. Add a separate whole-binary warm-up command.
5. **Exclude benches from the test runner** while still compiling them: `cargo nextest run --workspace --all-targets --locked -E 'not kind(bench)'`, and keep `cargo clippy --all-targets`.
6. **Add the workflow** (`references/ci-gate.md`; template `assets/bench.yml`). Create an orphan `gh-pages` branch first. Separate file, `permissions: {}` at top, publish job on the default branch only, read-only PR job with no token, path filters on everything that can move a number, `shell: bash` around `| tee`, identical warm-up in both jobs.
7. **Add the output sanity check**: copy `assets/check-bench-output.sh` to the project's `scripts/` and run it immediately after the bench step so a run that parses zero benchmarks fails instead of passing.
8. **Add floors** once a benchmark has CI history (`references/ci-gate.md` § Floors; `assets/check-bench-floors.ts`, its test, `assets/floors.toml`). Declare Node ≥ 22.18 in the task runner's tools. Seed figures from CI runs, never from a laptop.
9. **Optionally add an allocation-count series** (`references/allocation-series.md`; `assets/counting_alloc.rs`). Assert shapes in tests; publish the same numbers from the same tests.
10. **Decide required vs advisory** explicitly (`references/ci-gate.md` § Required checks). A path-filtered workflow cannot be a required check without an always-running stub. Advisory gates get merged past; record the decision either way.

## Gates that go green while measuring nothing

Check every one of these on a new setup. Each happened.

| Cause | Symptom | Guard |
|---|---|---|
| criterion's default output format | Action's regex matches nothing, stores zero benchmarks, passes | Always pass `--output-format bencher`; run `scripts/check-bench-output.sh` |
| `--quick` | Drops bench names from bencher lines; same silent zero; not even faster | Ban the flag in a contract test (`references/ci-gate.md` § Pin the workflow) |
| `[lib]` / `[[bin]]` libtest harness receives `--output-format` | Task fails before criterion runs | `bench = false` on lib and bins; pass `--benches` |
| `bench \| tee` under default `bash -e` | Panic hidden, partial output published | `shell: bash` on the step (adds pipefail) |
| First run, no stored baseline | Action logs "Could not find data.js", skips comparison, green | Treat the first green as unproven |
| Fixture write rejected silently (logged, no subscriber) | Measures an empty structure, plausible number | Assert fixtures landed before timing |
| Mutating bench with large `BatchSize` | All but the first iteration time a no-op | `BatchSize::PerIteration` |
| Native dependency missing on runner | Bench target fails to build; series stops growing | Install it explicitly; watch series growth |
| Floor step skipped after ratio gate fails | Second check never runs | `if: ${{ !cancelled() && steps.<prior>.outcome == 'success' }}` |
| `workflow_dispatch` with github-action-benchmark | Always fails "No commit information is found in payload" | Drop the trigger or pass `ref:`; verify every advertised trigger |
| Job timeout | Reports `cancelled`, indistinguishable from a superseded run | Treat `cancelled` on a non-superseded run as failure |

## Rules for CI numbers

- Only the default branch publishes. PR jobs compare read-only, with no token, so a PR cannot move the baseline it is judged against.
- Path-filter push as well as pull_request, so the series gets one point per change that could have moved it and does not drift on noise. Include the floors file and checker in the filter.
- Never rename a series key (`name:`). A rename starts an empty series. Append new sizes rather than renaming existing ids.
- Keep warm-up identical in every job that feeds or reads a series. First-run contamination shifts the mean (2.9× on a fresh binary), so an asymmetric warm-up manufactures regressions. Measurement budgets may differ; warm-ups must not.
- Treat a config change (budget, profile, warm-up) as a baseline break; let that PR's own run be the experiment and say so in the PR.
- Normalise across runs by a control set: the geometric mean of benchmarks the change cannot touch. The project saw main's own unchanged series move ~2x.
- Rerun before believing a regression; a real cost does not reverse sign between two runs of one commit. Never rerun until green.
- Reject a fix that moves cost to another path, even when the gate is green. A loose threshold is not acceptance.

## Rules for local numbers

A local run answers shape and ratio questions only (does cost grow linearly; which variant is cheaper within one process). It decides nothing about CI. The same change measured 4.03x locally and 5.58x on CI. When a local experiment is the right tool, follow `references/measurement-discipline.md` § Local runs: record load, order runs pre/tip/tip/pre, give each commit its own `CARGO_TARGET_DIR`, hash binaries, prefer the minimum of interleaved samples under load.

## Time budget

Use `--warm-up-time 0.5 --measurement-time 1 --sample-size 10 --nresamples 1000`, not criterion's defaults, which spent 10.5 of a 12.5-minute job buying precision the gate cannot read. Do not subset benchmarks on PRs; that drops the large sizes the series exists for. Details: `references/harness.md` § Command and budget.

## Accepting a performance change

Record, in the PR or ticket: baseline SHA and the stored-point run it compared against, candidate SHA, at least two CI attempts, every protected series (not just the target), raw and control-normalised speedup, and any rerun. See `references/measurement-discipline.md` § Acceptance record.

## Additional resources

### Reference files

- **`references/harness.md`** — criterion and Cargo configuration, bench idioms with real excerpts, fixture design, size series, keeping test-only constructors out of shipped code.
- **`references/ci-gate.md`** — workflow design decision by decision, floors, step ordering after a failing gate, caches, security hardening, required-check and merge-queue traps, contract tests that pin the workflow.
- **`references/measurement-discipline.md`** — noise, control normalisation, paired A/B in CI, local experiment discipline, diagnosing a regression, acceptance record.
- **`references/allocation-series.md`** — counting allocator, shape assertions, publishing a deterministic series from the asserting tests.
- **`references/lessons.md`** — chronological failure catalogue: what broke, how it was found, the rule it produced.

### Assets (copy and adapt)

- **`assets/bench.yml`** — two-job GitHub Actions workflow: timing gate, optional allocation series, floor check. Replace `<...>` placeholders and re-pin actions to current SHAs.
- **`assets/mise-tasks.toml`** — `bench` and `bench_warmup` tasks with the named budget. Translate to `just`/`make`/`cargo xtask` if the project has no mise.
- **`assets/bench_template.rs`** — criterion bench file skeleton showing every idiom.
- **`assets/counting_alloc.rs`** — counting `GlobalAlloc`, `measure`, and series publishing, for an integration-test binary.
- **`assets/check-bench-floors.ts`** + **`assets/check-bench-floors.test.ts`** — floor checker (no dependencies) and its 26 `node:test` cases. Runs on Node ≥ 22.18 (native type stripping). The test imports `../check-bench-floors.ts`, so place them at `scripts/` and `scripts/tests/`. Wire the test into a CI gate and the path filter; the source project forgot to.
- **`assets/floors.toml`** — floors file with the field contract in its header.

- **`assets/check-bench-output.sh <output.txt> [min-count] [required-name...]`** — copy to `scripts/`. Fails when the bencher output has fewer parsed benchmarks than expected or lacks a named one. Closes the "zero benchmarks stored, green" hole that the source project guarded only indirectly; new here, tested against sample output but not yet run in a real pipeline.
