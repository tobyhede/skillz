# Behavior cases

## Should activate

- "Add criterion benchmarks to this Rust crate and gate regressions in CI."
- "Our github-action-benchmark job is green but the gh-pages series has no data. Why?"
- "The bench job takes 12 minutes; make it faster without losing the regression gate."
- "My benchmarks are noisy in CI. Is this 8% regression real?"
- "Set up benchmarks." (no crate, paths, or CI provider named; should ask what to measure and where it runs)

## Should not activate

- "This function is slow; profile it and optimize the hot loop." (belongs to `performance-engineering`)
- "Add a GitHub Actions workflow that runs cargo test and clippy."
- "Write unit tests for this Rust module."

## Expected behavior

- Configures criterion with `default-features = false`, `harness = false` on each `[[bench]]`, and `bench = false` on lib and bins.
- Uses `--output-format bencher`, bans `--quick`, and adds an output sanity check so a run that parses zero benchmarks fails.
- Publishes the series only from the default branch; PR jobs compare read-only with no token.
- Sets thresholds above runner noise and backs the ratio gate with committed floors seeded from CI runs, never from a laptop.
- Refuses to decide a sub-20% effect from two separate CI runs or from a local-versus-CI comparison; proposes paired, interleaved A/B runs in one job.
- Treats the first run with no stored baseline as unproven, and never renames an existing series key.
