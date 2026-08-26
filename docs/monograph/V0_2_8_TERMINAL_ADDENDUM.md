# PNCore-BioOS v0.2.8 Terminal Addendum

This addendum extends the repository monograph with the first terminal layers and the Terminal36D V8 standard vector environment.

## Terminal architecture

The terminal line is now:

```text
UART16550 / later physical adapters
 -> AUX.TERM.RX/TX
 -> PNTERM bounded line discipline
 -> PNTERM session and deterministic command envelope
 -> hash-pinned Terminal36D V8 standard 36D vector environment
 -> typed concept/capability gate
 -> PNCAP for authority-bearing operations
 -> AUX effect boundary
 -> execution receipt and PNTERM result
```

Terminal36D V8 is pinned by the exact Library roundtrip profile. It preserves the V7 typed capability manifest with 29 operations and vector dimension 36. PNTERM is the transport/session front-end rather than a parallel execution environment.

The current x86_64 physical terminal candidate is a bounded 16550 polling adapter under `AUX.TERM`, configured for 115200 8N1 in the reference realization. Physical and emulator execution remain explicit later gates.

The bridge freezes Terminal36D semantics while equivalent typed primitives are progressively realized natively in BioOS PNV/assembly layers.

## Benchmark snapshot

The byte-exact V8 benchmark receipt is stored at `provenance/PNCORE_BIOOS_TERMINAL36D_V8_BENCHMARK_V0_2_8.json` and the readable report at `docs/benchmark/TERMINAL36D_V8_BENCHMARK_V0_2_8.md`.

Reference host results:

- cold exact-profile verification: 31.68 us / verification
- warm typed operation lookup: 43.07 million/s
- warm O(1) lookup speedup over linear 29-capability scan: 18.38x
- PNTERM envelope + action hash: 294.0k ops/s
- direct HASH_BATCH primitive: 439.8k ops/s
- full `Terminal36D.execute()` HASH_BATCH: 30.45k ops/s
- 36D vectorization: 230.2k vectors/s at batch=1; 730.4k vectors/s at batch=256

These figures characterize the declared host/reference fixture. The optimization rule is to keep exact profile verification on the cold `TERMINAL_EPOCH` path and use the precompiled O(1) typed-operation table on the warm command path.

## Current generated monograph

The current generated v0.2.8 monograph integrates this terminal architecture and the benchmark chapter:

`PNCore_BioOS_Od_BIOSu_do_Torsyjnej_Pamieci_i_Terminal36D_v0.2.8.pdf`

Exact SHA-256 values for the generated PDF, DOCX and benchmark receipt are pinned in `docs/monograph/V0_2_8_ARTIFACTS.sha256`.
