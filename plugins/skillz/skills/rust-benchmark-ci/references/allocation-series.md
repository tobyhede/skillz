# Allocation-count series

Wall clock hides an allocation behind a cache hit. Allocation counts are deterministic, so they get tight thresholds, no warm-up, and assertions in ordinary tests.

Template: `assets/counting_alloc.rs`.

## Where the allocator lives

- An integration test (`tests/allocation.rs`) is its own binary, so `#[global_allocator]` there reaches nothing shipped and needs no feature gate.
- Gate the file `#![cfg(not(target_arch = "wasm32"))]` if the workspace builds WASM with `--all-targets`.
- No crate: `dhat` 0.3.3 is stale with a maintenance disclaimer and pulls eight crates; `allocation-counter` has had no release since 2023. The mechanism is ~40 lines. Use `dhat` on a branch to diagnose which callsite allocates; do not commit it.
- Duplicate the allocator per test binary that needs it, with comments naming the copies.

## How it counts

- `const`-initialised `thread_local! { static BLOCKS: Cell<usize> = const { Cell::new(0) }; }`. A lazily initialised thread-local allocates on first access, inside the allocator.
- Thread-local rather than atomic: correct under plain `cargo test` (tests share a process, each on its own thread) as long as measured work stays on the calling thread. Work across a multi-threaded runtime needs atomics and nextest's process-per-test isolation; say so in that test.
- Do not override `realloc`/`alloc_zeroed`; the defaults route through the counted `alloc`.
- `measure(f) -> (Allocations, T)` returns the value so drops fall outside the span and the work is not optimised away.
- Keep anything that allocates (reading env vars, formatting) outside measured spans.

## What to assert

Shapes, never absolute numbers. "An absolute count rots on a compiler release or a dependency bump, and the fix is always to edit the number, which teaches everyone to edit the number." Each assertion is one of:
- zero;
- a ceiling derived from the input that stays true if the path gets cheaper;
- equality between two sizes of the same work;
- linear growth by cross-multiplication: `assert!(large.bytes * small_cells <= small.bytes * large_cells)`.

A failing assertion is a finding: record what allocates and why (a dated `FINDING:` comment or a ticket) before relaxing it.

## Publishing the series

The same tests print what they measured, then assert; a failed assertion fails the run before anything is published. A separate binary re-running the paths would let published and asserted numbers drift apart.

- Gate printing on an env var (`<PROJECT>_MEMORY_SERIES=1`) so ordinary test runs are silent.
- Prefix each line with a marker, one `customSmallerIsBetter` object per line: `MARKER {"name": "<series> blocks", "unit": "blocks", "value": N}`.
- Do not publish points asserted zero or equal to another point.
- Collect: `MARKER_ENV=1 cargo test --package <p> --test allocation --locked -- --nocapture | tee allocations.txt` under `shell: bash`.
- Assemble with coreutils (`grep -o`, `cut`, `sort`, `paste`) into a JSON array; fail if empty, if any crate published nothing, or if two records share a name. See the assemble step in `assets/bench.yml`.
- Action settings: `tool: customSmallerIsBetter`, `skip-fetch-gh-pages: true` after the forced fetch, alert 110%, fail 125%, `fail-on-alert: false` until there is a way to accept a deliberate increase.

## Memory safety vs memory behaviour

Separate them. Miri and sanitizers check safety and had low yield in a mostly-safe codebase; allocation counts and retained-growth tests check behaviour and caught real regressions. A leak test that "compiles but has never been run" is not evidence; make sure some tier runs it.
