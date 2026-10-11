# CI gate: workflow, floors, ordering, required checks

Template: `assets/bench.yml`. This file explains each decision.

## Shape

- **Separate workflow file.** The publisher needs `contents: write`; the action's README warns against running it on pull requests with write permission. A separate file keeps that scope out of PR workflows.
- **`permissions: {}` at top**, grants per job.
- **`publish` job**: `if: github.event_name == 'push' && github.ref == 'refs/heads/main'` (an explicit event, so a later `merge_group` or `workflow_dispatch` trigger cannot publish by accident); `contents: write`, `deployments: write`; `concurrency.cancel-in-progress: false` ("a run cancelled partway through publishing leaves the stored series half written"); `auto-push: true`; `comment-on-alert: true`.
- **`pull-request` job**: `contents: read`; no `github-token`; `auto-push: false`; `comment-on-alert: false` (it throws without a token); `summary-always: true`; `cancel-in-progress: true`. It reads `gh-pages` anonymously, which works only on a public repo. On a private repo grant a read token.
- **`timeout-minutes`** on every job.
- **Storage**: github-action-benchmark appends to `gh-pages` at `dev/bench/data.js`. `GITHUB_TOKEN` suffices for same-repo push. Create an orphan `gh-pages` branch before the first run (`git switch --orphan gh-pages && git commit --allow-empty -m 'Benchmark data' && git push origin gh-pages`); the second-series fetch hard-fails without it.

## Triggers and path filters

Filter both `push` and `pull_request` on everything that can move a measurement: benchmarked crates, `Cargo.toml`, `Cargo.lock`, `rust-toolchain.toml`, the task runner config, the workflow itself, `.cargo/config.toml` (rustflags move numbers), any workspace-level `benches/` directory, `benches/floors.toml`, the floor checker and its test, and the output check. Filtering push keeps one point per relevant change: "republishing an unchanged crate would let the baseline drift on nothing." Actions has no YAML anchors, so the list is written twice; pin it in a contract test so the two copies cannot diverge.

Do not offer `workflow_dispatch` unless it is verified. With github-action-benchmark it always failed: "No commit information is found in payload". The candidate fix is the action's `ref: ${{ github.sha }}` input; otherwise drop the trigger.

## Thresholds

| Series | Alert | Fail | fail-on-alert |
|---|---|---|---|
| Wall-clock (criterion) | 150% | 300% | true |
| Allocation counts (deterministic) | 110% | 125% (inert while `fail-on-alert` is false) | false initially (no in-repo way to accept a deliberate increase) |

Document beside the thresholds what they cannot see. These are screening alerts, not acceptance criteria.

## Runner, caches, tools

- `ubuntu-latest`. Record the runner in every floor; cross-machine figures are not interchangeable.
- `Swatinem/rust-cache` with `shared-key: bench` (both jobs build the same tree) and `save-if: ${{ github.ref == 'refs/heads/main' }}`. PR-ref caches are readable only by that PR but share the 10 GB quota; ungated, the repo sat at 9.8/10 GB evicting main's entries. Restores still work on PRs by key prefix.
- Do not install tools the job does not use. `mise-action` with `install: false` saved 10 of the first 12 minutes; install single tools by name where needed (`mise install node` before the floor check).
- Install native build dependencies explicitly (the source project needed `libasound2-dev`); a missing one stops the series growing silently.

## Running the benches

```yaml
- name: Warm up
  run: <task runner> bench_warmup > /dev/null
- name: Run benchmarks
  id: bench
  shell: bash        # supplies pipefail; default `bash -e` reports tee's status and publishes partial output
  run: <task runner> bench | tee output.txt
- name: Check bench output
  id: parsed         # every later guard chains on this step
  run: bash scripts/check-bench-output.sh output.txt <min-count>
```

The warm-up must be identical in both jobs; contamination moves the mean, so cold-vs-warm reads as a regression. Assert this in the contract test (warm-up count == job count).

## Floors

**Why.** The ratio gate compares only against main's previous point. A merged regression (19 → 106 ns, fixed to 70 ns, merged deliberately) became the baseline; every later PR read green against 70 ns. A paint regression of 5.5× did the same, and three later PRs read green. The ratio asks "did this change make it worse"; a floor asks "is it still as good as we agreed".

**File.** `benches/floors.toml`, one `[[floor]]` per guarded benchmark: `name` (exact bencher name), `max_ns`, `runner`, `source` (how the figure was derived). Raising a floor is a reviewed diff.

**Checker.** `assets/check-bench-floors.ts`, outside the action ("fighting a tool with no concept of a floor"). It reads the same `output.txt`, parses a strict TOML subset by hand (no dependency; anything outside the subset is an error because "a floor this function misreads is a guard that does not hold"), and:
- passes unguarded benchmarks and results equal to the floor;
- fails a guarded name missing from output (a rename cannot drop a guard);
- fails a non-ns unit;
- reports measured, floor, runner, excess in ns and %.

**Seeding.** From at least two CI attempts of an accepted change, ~45% headroom over the worse attempt, well below the pre-fix figure. A floor seeded at 2× a laptop number flapped (101–114 ns against 100) on PRs that did not touch the crate. Do not tune code (e.g. `repr(align(8))`) just to pass a floor; that change was reverted. Label any laptop-derived figure "starting figure, not yet CI-measured".

**Test it.** Run its `node:test` suite in a gate and include it in the path filter (the template does both). The source project shipped 26 tests that no CI tier ran. Declare `node = "22.18"` or later in the task runner's tools: the checker relies on native type stripping.

## Ordering after a failing gate

`fail-on-alert: true` fails its step, and default `success()` skips everything after it, including the floor check and the allocation series.

- Guard every later step: `if: ${{ !cancelled() && steps.<earlier non-gate id>.outcome == 'success' }}`. Not `success()`, not the job status, not the gate's own outcome.
- Chain steps on their own predecessor (measure → parsed, assemble → measure, fetch → assemble, publish → fetch); floor steps chain on parsed.
- A second series run by the same action needs its own fetch, because the first step's outcome cannot say whether it failed before or after fetching gh-pages, and the action commits locally even without auto-push:
  ```bash
  git checkout --quiet --force --detach "$GITHUB_SHA"   # never fetch into a checked-out branch
  git fetch origin +gh-pages:gh-pages                   # + required: the PR comparison left an unpushed local commit
  ```
  then `skip-fetch-gh-pages: true` on the second action step.
- Put the floor check last; assert no step follows it.
- Verify with a real failing run: gate red, every later step green, job concluded failure.

## Required checks and merge queue

- A required check from a path-filtered workflow that does not trigger reports nothing and blocks the PR forever. A job skipped by `if:` reports "skipped" and satisfies the check; an untriggered workflow does not.
- To require it: an always-triggered stub or aggregate job (`if: always()`, `needs: [...]`) carrying the context name, with a script that compares each result to what the event should produce.
- With a merge queue, add a `merge_group` trigger or the queue waits forever.
- A shorter job is easier to require ("a three-minute job is a much easier thing to require than a twelve-minute one").
- Advisory gates leak: two floor breaches reached main in the source project. If staying advisory, record it as a decision and review cumulative drift at release against a baseline nominated before results are seen.

## Security hardening

- Every action pinned to a 40-char SHA with a version comment; ban `@v1`, `@main`, `@master`. Assert per file: the bench workflow once sat a major version behind the others.
- `persist-credentials: false` on checkout; no `pull_request_target`; no `${{ }}` interpolation in `run:` except `$GITHUB_SHA`.
- Lint with `actionlint` and `zizmor --offline .github/workflows`.

## Pin the workflow with a contract test

No contract script ships with this skill; write one for the project from this checklist once the workflow settles. Every pin in the source project's contract came from a bug. A shell script asserted, against the workflow file: both bench commands verbatim, the `--quick` ban, path filter entries (each exactly twice), native deps, warm-up once per job, series names, tools and thresholds per job, a literal unquoted `fail-on-alert: true`, the forced fetch and detach, the after-gate guard shape and chain, floor check last, SHA pins, `shared-key`, cache save gates, `not kind(bench)` in the test command, `bench = false` in manifests. Derive counts from the number of jobs, so a new job missing a step fails. Prove each assertion has teeth with a fixture suite that mutates copies (unbenchmarked crate, defaulted budget, asymmetric warm-up, `--quick`, step after gate, `success()` guard, unforced fetch, quoted gate, floor not last, stale pin, commented-out timeout).

Shell gotcha found there: `producer | grep -q` under pipefail kills the producer with SIGPIPE (exit 141); it failed 160 of 200 runs on Linux. Use `grep pattern >/dev/null` instead.
