# Terminal36D V8 benchmark — PNCore-BioOS v0.2.8

Status: PASS_BENCHMARK_REFERENCE

Runtime inputs were byte-exact against the Terminal36D V8 Library roundtrip for `terminal36d.py`, `vector_kernel.py`, and `concept_gates.py`.

## Results

- cold exact-profile verification: 31.68 us / verification
- warm typed operation lookup: 43.07 million lookups/s
- linear 29-capability lookup: 2.34 million lookups/s
- O(1) lookup speedup over linear scan: 18.38x
- PNTERM deterministic envelope + action hash: 294.0k ops/s
- direct `PHASENAV_HASH_BATCH`: 439.8k ops/s
- full `Terminal36D.execute()` for HASH_BATCH: 30.45k ops/s
- 36D vectorization batch=1: 230.2k vectors/s
- 36D vectorization batch=32: 655.7k vectors/s
- 36D vectorization batch=256: 730.4k vectors/s
- 36D vectorization batch=1024: 694.5k vectors/s

## Optimization conclusion

Exact runtime/profile verification belongs on the cold `TERMINAL_EPOCH` path. Normal command dispatch should reuse a precompiled typed-operation table in O(1). The measured lookup cost falls from about 426.8 ns to 23.2 ns per lookup on this host fixture.

Batch-first vectorization is also supported by the measurement: batch=256 increases throughput from about 230k vectors/s to about 730k vectors/s relative to batch=1.

The full `Terminal36D.execute()` path is intentionally heavier than direct primitive invocation because it retains concept-gate evaluation, typed dispatch, timestamps, result construction, and a content-addressed execution receipt. Optimization should preserve that evidence spine.

These figures characterize this host/reference fixture and are not universal hardware guarantees.
