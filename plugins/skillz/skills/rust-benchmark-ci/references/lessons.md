# Lessons: what broke and the rule it produced

Chronological. Each entry: what happened → how it surfaced → the rule. SKILL.md's "Gates that go green while measuring nothing" table is the checklist distilled from entries 1, 2, 5–8, 11, 13, 14 and 16; this file keeps the history and numbers behind it.

1. **Initial gate went green on nothing.** Criterion's default output did not match the action's regex; zero benchmarks stored. Found by reading the stored data. → Always `--output-format bencher`; assert a minimum parsed count.
2. **`| tee` hid a panic.** Default `bash -e` returns tee's status. → `shell: bash` (pipefail) on every `| tee` step.
3. **Fresh binary measured 2.9× slow.** `parse_source` 1,204 ns first run vs 417 ns settled; criterion's own warm-up did not fix it. → Whole-binary discard pass, identical in every job.
4. **10 of 12 minutes installing unused tools.** → Install only what the job runs.
5. **Libtest harnesses rejected `--output-format`.** → `--benches` plus `bench = false` on lib and bins.
6. **Mutating bench measured no-ops.** Larger batches ran every setup before any routine. → `BatchSize::PerIteration`.
7. **Native dependency missing.** Series would have silently stopped growing. → Install explicitly.
8. **Fixtures silently empty.** Rejected writes only logged. → Assert fixtures landed.
9. **PR caches filled 9.8/10 GB**, evicting main's. → Save caches from main only.
10. **First real regression merged** (19 → 106 → 70 ns). Gate not required; merge re-baselined silently. → Floors.
11. **Manual dispatch never worked** ("No commit information is found in payload"). Its raw numbers still exposed a 10× scaling regression. → Verify every advertised trigger; raw numbers in logs are still evidence.
12. **Budget: 12.5-minute job buying ~2% precision behind a 150% gate.** → Named budget sized to the threshold, ~3× faster, <2% drift. `--nresamples` is a hidden ~2.7 s per bench.
13. **`--quick` produced a silent zero** and was not faster. → Ban it in a contract test.
14. **Benches ran as tests under `nextest --all-targets`**, 235 s each, four merge-queue timeouts unnoticed because timeouts report `cancelled`. → `-E 'not kind(bench)'`; treat unexpected `cancelled` as failure.
15. **Green candidate rejected.** Paint improved but render frames slowed 5–17%; the 150% threshold let it through. Main's own series moved ~2× on unchanged code; a rerun reversed an apparent regression's sign. → Control normalisation, check every protected series, reruns for sign only.
16. **Floors added, then four immediate bugs**: floor step skipped when ratio gate failed; floors file missing from path filters; names with spaces skipped; floor failure skipped allocation steps. → Guard chain on `!cancelled()` + predecessor outcome; floors and checker in filters; test the parser with real criterion output; floor check last.
17. **Advisory gate leaked twice** (floor breaches reached main, recovered in follow-up PRs). → Decide required vs advisory explicitly; requiring needs an always-run stub.
18. **Second series fetch failed** after the PR comparison left an unpushed local commit on gh-pages. → Detach, forced `+gh-pages:gh-pages` fetch, `skip-fetch-gh-pages: true`. Confirmed only by a real failing run.
19. **16×16 hid a 570 ns fixed cost.** → Include `empty` and `single` sizes.
20. **Floor seeded from laptop ×2 flapped** on unrelated PRs. A `repr(align(8))` was added to hold it, then reverted. → Seed from CI attempts with headroom; never tune code to a floor.
21. **Only the fallback path was benchmarked.** → Benchmark the path production takes.
22. **Local results reversed on a `Cargo.lock`-only change.** → Paired interleaved A/B in CI with a pre-declared rule.
23. **`grep -q` under pipefail** failed 160/200 runs with SIGPIPE in the contract script. → `>/dev/null` instead of `-q` after a pipe.
24. **Floor checker tests never wired into CI.** Still open in the source project. → Wire every checker's tests into a gate and its path filter.

Rejected tooling, for the record: iai-callgrind (no Apple Silicon Valgrind; otherwise the precise option), bencherdev/bencher (not worth it for one floor occurrence), dhat as a committed dependency (stale; use on a branch for diagnosis).
