//! Allocation shapes for <the hot paths>. Template for `tests/allocation.rs`.
//!
//! An integration test is its own binary, so the `#[global_allocator]` below reaches this file
//! and nothing shipped. No crate: the mechanism is a `GlobalAlloc` that forwards to `System` and
//! counts. Use `dhat` on a branch to find *which* callsite allocates; do not commit it.
//!
//! Assert shapes, never absolute numbers: zero, a ceiling derived from the input, or equality /
//! linear growth across sizes. An absolute count rots on a compiler or dependency bump and teaches
//! everyone to edit the number. A failing assertion is a finding: record it before relaxing.
//!
//! With `<PROJECT>_MEMORY_SERIES=1`, each test prints what it measured before asserting, and CI
//! publishes those lines as a `customSmallerIsBetter` series. Published and asserted numbers come
//! from the same run, so they cannot drift apart.
#![cfg(not(target_arch = "wasm32"))]

use std::alloc::{GlobalAlloc, Layout, System};
use std::cell::Cell;
use std::hint::black_box;

thread_local! {
    // `const` initialisation: a lazily initialised thread-local allocates on first access, which
    // would allocate from inside the allocator. `Cell<usize>` has no drop glue.
    //
    // Thread-local rather than atomic: everything measured here runs on the calling thread, so
    // this stays correct under plain `cargo test`, where tests share a process. Work measured
    // across a multi-threaded runtime needs `AtomicUsize` and process-per-test isolation.
    static BLOCKS: Cell<usize> = const { Cell::new(0) };
    static BYTES: Cell<usize> = const { Cell::new(0) };
}

/// `System`, plus a count of blocks and bytes handed out. `realloc` and `alloc_zeroed` are not
/// overridden: `GlobalAlloc`'s defaults route them through `alloc` and `dealloc`, so they are
/// counted without the counting being written twice.
struct Counting;

// SAFETY: `GlobalAlloc`'s contract is discharged entirely by `System`. Every method forwards to
// `System` with the layout and pointer it was handed and returns exactly what `System` returned,
// including null on failure. The counters observe `layout.size()` only, and their `const`
// storage cannot allocate, so they cannot re-enter this allocator.
unsafe impl GlobalAlloc for Counting {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        BLOCKS.with(|blocks| blocks.set(blocks.get() + 1));
        BYTES.with(|bytes| bytes.set(bytes.get() + layout.size()));
        // SAFETY: `layout` is the caller's, forwarded unchanged; the caller met `alloc`'s
        // non-zero-size requirement.
        unsafe { System.alloc(layout) }
    }

    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        // SAFETY: `ptr` came from `System.alloc` via this allocator with this `layout`.
        unsafe { System.dealloc(ptr, layout) }
    }
}

#[global_allocator]
static ALLOCATOR: Counting = Counting;

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
struct Allocations {
    blocks: usize,
    bytes: usize,
}

fn snapshot() -> Allocations {
    Allocations { blocks: BLOCKS.with(Cell::get), bytes: BYTES.with(Cell::get) }
}

/// Runs `f` and answers what it allocated. The value is returned rather than dropped inside, so
/// frees fall outside the span and the optimiser cannot discard the work.
fn measure<T>(f: impl FnOnce() -> T) -> (Allocations, T) {
    let before = snapshot();
    let value = f();
    let after = snapshot();
    (Allocations { blocks: after.blocks - before.blocks, bytes: after.bytes - before.bytes }, value)
}

/// Matched literally by the workflow's assemble step; change both or neither.
const SERIES_MARKER: &str = "<PROJECT>-MEMORY-SERIES";

/// Reading the variable allocates, so call this only outside measured spans.
fn publishing() -> bool {
    std::env::var("<PROJECT>_MEMORY_SERIES").is_ok_and(|value| value == "1")
}

/// One `customSmallerIsBetter` object per line. `name` is a literal and a permanent series key.
fn publish(name: &str, allocations: Allocations) {
    if !publishing() {
        return;
    }
    for (unit, value) in [("blocks", allocations.blocks), ("bytes", allocations.bytes)] {
        println!(r#"{SERIES_MARKER} {{"name": "{name} {unit}", "unit": "{unit}", "value": {value}}}"#);
    }
}

// ---- Example assertions; replace with the project's paths. ----

#[test]
fn steady_state_read_allocates_nothing() {
    let thing = mycrate::Thing::populated_for_tests(64, 64);
    let (allocations, value) = measure(|| thing.read());
    black_box(value);
    // Asserted zero, so not published: a point fixed at zero is not a series.
    assert_eq!(allocations, Allocations::default(), "a steady-state read must not allocate");
}

#[test]
fn derive_grows_at_most_linearly() {
    let (small_cells, large_cells) = (16 * 16, 64 * 64);
    let small_thing = mycrate::Thing::populated_for_tests(16, 16);
    let large_thing = mycrate::Thing::populated_for_tests(64, 64);
    let (small, a) = measure(|| small_thing.derive());
    let (large, b) = measure(|| large_thing.derive());
    black_box((a, b));
    publish("thing_derive/64x64", large);
    assert!(
        large.bytes * small_cells <= small.bytes * large_cells,
        "derive bytes grew more than linearly in the cell count: {small:?} -> {large:?}"
    );
}
