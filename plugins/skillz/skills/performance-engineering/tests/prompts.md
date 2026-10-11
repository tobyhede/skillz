# Behavior cases

## Should activate

- "This parser is too slow on large inputs. Profile it and make it faster."
- "Our service p99 latency spikes under load even though host CPU looks low. What is going on?"
- "We're designing a new ingestion pipeline; help me set performance budgets before we build it."
- "Can you vectorize this hot loop with SIMD?"
- "Make it faster." (no code, workload, or target named; should ask what operation, workload, and budget matter)

## Should not activate

- "Add a criterion benchmark gate to our GitHub Actions workflow." (belongs to `rust-benchmark-ci`)
- "Fix the off-by-one error in this pagination function."
- "Reduce our Vercel bill for this Next.js app."

## Expected behavior

- Establishes the work, correctness, resource, and budget contract before changing code, labelling anything assumed.
- Reproduces the complaint and records a baseline before optimizing; never invents a profile or a measured speedup when it cannot execute code.
- Distinguishes CPU-profile share from request wall time (a function at 60% of 10 ms CPU in a 100 ms request yields at most a ~6 ms saving).
- Rejects averaging per-instance p99 values into a service p99.
- Treats a noisy result that crosses the gate as INCONCLUSIVE rather than rerunning until green or relaxing the gate.
- Prefers removing work and improving layout before reaching for SIMD or parallelism.
- Reports results with the report template, marking each as measured, derived, hypothesized, or unvalidated, with a keep/revert decision.
