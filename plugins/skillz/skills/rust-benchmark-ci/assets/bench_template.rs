//! Benchmarks for <the paths this crate sits on, and why they are hot>.
//!
//! Run with `mise run bench`. The `--output-format bencher` flag it passes is not cosmetic:
//! CI parses the output with a regex that only matches that format.
//!
//! Template: replace `mycrate`, `Thing`, and the fixture corpus. Keep the idioms.

use criterion::{BatchSize, BenchmarkId, Criterion, criterion_group, criterion_main};
use mycrate::Thing;
use std::hint::black_box;

/// Each step quadruples the work, so whole-structure cost shows up as growth across the series
/// instead of hiding inside one size. Held fixed so stored measurements stay comparable:
/// append sizes, never reshape them.
const SIZES: &[(usize, usize)] = &[(16, 16), (32, 32), (64, 64), (128, 128), (256, 256)];

/// Realistic content, including the malformed and half-finished input real use leaves behind.
/// Duplicated in `tests/allocation.rs`: a bench target and a test target cannot import each other.
const CORPUS: &[&str] = &["<valid>", "<nested>", "<malformed>", "<half-typed>"];

fn size(cols: usize, rows: usize) -> BenchmarkId {
    BenchmarkId::from_parameter(format!("{cols}x{rows}"))
}

/// Builds a populated fixture through the public API and proves it landed. A rejected write that
/// only logs would otherwise be measured as an empty structure and report a plausible number.
fn populated(cols: usize, rows: usize) -> Thing {
    let mut thing = Thing::with_shape(cols, rows); // test-only constructor, see references/harness.md
    let mut expected = 0;
    for row in 0..rows {
        for (col, text) in CORPUS.iter().cycle().skip(row % CORPUS.len()).take(cols).enumerate() {
            thing.write(col, row, text);
            expected += 1;
        }
    }
    assert_eq!(thing.occupied(), expected, "every fixture write is accepted");
    thing.settle(); // measure the steady state, not the first pass that fills every cache
    thing
}

/// A read whose cost should not depend on size; same sizes as `derive`, so it can be subtracted.
fn read(c: &mut Criterion) {
    let mut group = c.benchmark_group("thing_read");
    for &(cols, rows) in SIZES {
        let thing = populated(cols, rows); // built once per size, outside the timed closure
        group.bench_function(size(cols, rows), |b| b.iter(|| black_box(black_box(&thing).read())));
    }
    group.finish();
}

/// Degenerate sizes expose fixed per-call cost that the smallest real size hides.
fn derive(c: &mut Criterion) {
    let mut group = c.benchmark_group("thing_derive");
    group.bench_function("empty", |b| {
        let thing = Thing::with_shape(0, 0);
        b.iter(|| black_box(black_box(&thing).derive()))
    });
    for &(cols, rows) in SIZES {
        let thing = populated(cols, rows);
        group.bench_function(size(cols, rows), |b| b.iter(|| black_box(black_box(&thing).derive())));
    }
    group.finish();
}

/// The restore is the setup rather than part of the routine, and `BatchSize::PerIteration` keeps
/// the two alternating: a larger batch runs every setup first, so all but the first edit would be
/// a no-op write of content already present.
fn edit(c: &mut Criterion) {
    let mut group = c.benchmark_group("thing_edit");
    for &(cols, rows) in &SIZES[..3] {
        // Kept small on purpose: building a populated fixture per size is itself expensive.
        // `set` takes `&self` here (interior mutability). If it takes `&mut self`, two closures
        // cannot both borrow the fixture: wrap it in a `RefCell` and borrow inside each closure.
        let thing = populated(cols, rows);
        let target = thing.index(cols / 2, rows / 2); // hoisted: minting an index is not an edit's cost
        group.bench_function(size(cols, rows), |b| {
            b.iter_batched(
                || thing.set(target, "<restored>").expect("restore"),
                |()| black_box(&thing).set(black_box(target), "<edited>").expect("edit"),
                BatchSize::PerIteration,
            )
        });
    }
    group.finish();
}

criterion_group!(benches, read, derive, edit);
criterion_main!(benches);
