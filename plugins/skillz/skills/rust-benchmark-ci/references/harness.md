# Harness: criterion, Cargo, and bench code

## What to benchmark

- Benchmark behaviour that exists, on inputs drawn from existing tests. "A benchmark of an unimplemented path is a fiction with a number attached."
- Benchmark the path production actually takes. The source project first benchmarked a locked fallback path; the production (commander) path was added later and behaved differently. Where two paths exist, measure both over the same fixtures in paired groups.
- Refuse micro-benchmarks of helpers: they "invite optimising something no workload waits on."
- Exclude what dominates but is not the code under test: disk (use an in-memory `Storage` stand-in), GPU, UI framework context, MIDI/network (in-memory adapters). If the harness would be "most of the number", omit that step and say so in the bench doc comment.
- Give separable costs separate groups (e.g. a derive pass and a fold pass), so a later move of work between them is visible rather than netting out.
- Add a sibling benchmark at the same sizes when attribution matters: cost of A = frame − revision-read, measured over identical fixtures.

## Cargo configuration

```toml
# crate Cargo.toml
[lib]
bench = false          # otherwise `--benches` runs the libtest harness, which rejects --output-format

[[bin]]
name = "app"
bench = false          # same reason

[dev-dependencies]
criterion = { version = "0.8", default-features = false, features = ["cargo_bench_support"] }  # drops rayon, plotters

[[bench]]
name = "core"
harness = false

[[bench]]
name = "stored"
harness = false
required-features = ["persistence"]   # feature-dependent benches
```

```toml
# workspace Cargo.toml
# `bench` inherits `release`. Full LTO across criterion's tree is a slow link on every
# run, and stripped symbols make profiling useless. A comparison gate needs a profile
# identical between runs, not one identical to the shipped binary.
[profile.bench]
lto = "thin"
strip = "none"

[profile.profiling]
inherits = "release"
debug = true
```

Rejected alternatives, with reasons:
- A separate excluded bench crate: second lockfile, falls out of `cargo deny`.
- `required-features` as the way to turn on *test-only* features for benches (it remains right for gating a feature-dependent bench, as above): Cargo enables dev-dependency features per package, not per target, so use the self-dev-dependency pattern below instead.
- iai-callgrind (instruction counts, ~1% precise): the right upgrade for precision, rejected only because Valgrind has no Apple Silicon support and the maintainer could not run it locally. Reconsider if the team is on Linux/x86.
- bencherdev/bencher: could subsume ratio gate and floors; not adopted for one occurrence. Reconsider if floors grow beyond a handful.

## Command and budget

Set the budget once, on the command line, in the task runner, and use that task both locally and in CI:

```
cargo bench --package <a> --package <b> --benches --locked -- \
  --output-format bencher --warm-up-time 0.5 --measurement-time 1 --sample-size 10 --nresamples 1000
```

- `--output-format bencher` is load-bearing: CI parses with a regex that only matches `test <name> ... bench: <N> ns/iter (+/- <M>)`. Say so in each bench file's module doc.
- `--benches` keeps integration-test harnesses out.
- Never `--quick`: it drops names from bencher lines (silent zero) and was not faster (17.3 s vs 17.0 s).
- Warm-up task: same command with `--measurement-time 0.1`, output to `/dev/null`. Criterion's per-bench warm-up did not settle first-run contamination of a freshly compiled binary; only a whole-binary discard pass did.

## Keep benches out of tests

`cargo nextest run --all-targets` runs criterion benches at default budget as tests: ~14 s each, 235 s each on a contended runner, which timed out four merge-queue runs and discarded the numbers anyway. Use `-E 'not kind(bench)'` (filters by target kind, not name). Keep `cargo clippy --all-targets` so benches still compile and cannot rot.

## Idioms

**black_box both sides.** `std::hint::black_box` (not criterion's re-export) on inputs and on the result:
```rust
b.iter(|| black_box(black_box(&source).read_revision()))
```

**Per-iteration inputs.** Values consumed by value are built outside the timed routine:
```rust
// The operands are handed over by value, so each iteration's copy is built outside the timed routine.
b.iter_batched(|| operands.clone(), |operands| Interpreter::execute_function(black_box(Function::Add), black_box(operands), black_box(inputs).into()), BatchSize::SmallInput)
```

**Mutating benches.** When setup restores the state the routine mutates, use `PerIteration`:
```rust
/// The restore is the setup rather than part of the routine, and `BatchSize::PerIteration` is what
/// keeps the two alternating: any larger batch runs every setup before the first routine, so all but
/// the first edit would write a Cell that already holds `content` and measure a no-op.
b.iter_batched(|| { source.set(edited, RESTORED).expect("restore"); },
               |()| { black_box(&source).set(black_box(edited), content).expect("edit"); },
               BatchSize::PerIteration)
```
Hoist anything that is not the cost being measured (index minting, lookups) out of the routine.

**Steady state.** Settle the fixture during setup so the bench measures the steady state, not the one cold iteration that first writes every result; advance a counter so each iteration is fresh work:
```rust
let mut tick = settled_tick;
b.iter(|| { tick += 1; black_box(source.execute(black_box(Tick::new(tick)))) })
```

**Share expensive fixtures.** Build once per size, outside the closures; use `OnceLock` for runtimes or frames shared by several groups.

## Naming

- Groups `benchmark_group("<area>_<op>")`, parameters `BenchmarkId::from_parameter(format!("{w}x{h}"))`, variants inside the parameter (`fitted/16x16`).
- The bencher name `group/param` is the permanent key in the stored series and in `floors.toml`. Treat renames as breaking: they start an empty series and drop guards.
- Ids may contain spaces; the floor checker's regex handles that.
- No `Throughput` annotations were needed; per-item cost was read from the size series instead.

## Size series

```rust
/// Each step changes the Cell count fourfold, so whole-map work shows up as growth across the
/// series instead of hiding inside one fixed size. Held at these shapes so recorded measurements
/// stay comparable.
const FRAME_SIZES: &[(usize, usize)] = &[(16, 16), (32, 32), (64, 64), (128, 128), (256, 256)];
```
- ×4 work per step exposes quadratic cost (time growing ×16 per step).
- Vary one axis at a time for shape-specific costs (`NESTED_ROWS = 16`, only columns vary).
- Include degenerate inputs (`empty`, `single`): they exposed a 570 ns fixed per-call cost that 16×16 hid.
- Include a fixed-window ("culled") series beside a fitted one; culled must stay flat. The pair diagnoses per-item vs whole-structure cost.
- Read the curve as cost per item (e.g. ns/Cell 6.5 → 5.6, flat = linear) and as a share of a real budget (e.g. a 60 Hz frame).
- Keep expensive series small on purpose and say why ("pay for it deliberately").
- Cost fixture construction too: building a 256² fixture took 62.9 s because each edit rebuilt the whole map, which was itself an O(n²) defect. `cargo bench -- --list` builds fixtures without measuring.
- Append new sizes; never reshape existing ones.

## Fixtures

Make them representative: the source project tiled a corpus of valid, nested, malformed and half-typed expressions ("Source is malformed for most keystrokes"), cut at the row edge, edits landing inside populated content, cursor mid-grid. Build through the public API only.

Make them self-validating. Silent rejection produces a plausible number for an empty structure:
```rust
// `write` reports a rejected edit through `tracing` and returns nothing, and a bench binary
// installs no subscriber. Unchecked, a fixture that never landed would be measured as an empty
// Grid and still report a plausible number.
assert_eq!(occupied_cells(&app), text.chars().filter(|c| *c != ' ').count(), "every fixture cell is accepted");

// A Tick rejected as a graph error plans nothing, costs a fraction of an executed one,
// and would be reported as a plausible number.
assert!(plan.writes.len() * 32 >= cols * rows, "the fixture executes");
```
Build path-specific fixtures when the generic one would exercise an empty path (dependency edges, deep nesting), and say in the doc comment why the generic one is insufficient.

Doc-comment each bench: what is timed, what is excluded, why the fixture has its shape.

## Test-only constructors without seams in shipped code

Benches often need constructors production cannot reach (custom shapes, in-memory adapters). Keep them out of shipped builds:

```rust
#[cfg(any(test, feature = "test-grid-shapes"))]
pub fn with_shape(cols: usize, rows: usize) -> Self { ... }
```
```toml
[features]
test-grid-shapes = []        # adds no dependencies

[dev-dependencies]
# The crate itself, with test-only features: the only way a package turns a feature on for its own
# integration tests, benches and doctests without every invocation naming it. A dev-dependency never
# reaches a normal build.
mycrate = { path = ".", features = ["test-grid-shapes", "test-output-adapter"] }
```

Bench and test targets cannot import each other. Duplicate fixture code between them, with comments naming each sibling copy, rather than exporting helpers from shipped code.
