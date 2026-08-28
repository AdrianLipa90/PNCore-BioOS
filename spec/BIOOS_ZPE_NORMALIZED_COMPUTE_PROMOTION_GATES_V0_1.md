# BioOS ZPE-Normalized Compute Promotion Gates v0.1

Status: `EXPERIMENTAL_CONTROL / PHYSICAL_ENERGY_GATE_PENDING`

This file defines the promotion boundary for `BIOOS_ZPE_NORMALIZED_COMPUTE_V0_1`.

## Gate A — relational conformance

A candidate mode is admitted only when all frozen controls pass for the same initial state and semantic horizon:

```text
normalized overlap >= configured floor
phase RMS <= configured ceiling
phase max <= configured ceiling
coupling-direction drift <= configured ceiling
coupling log-scale drift <= configured ceiling
winding lineage exact when required
```

Threshold values are `EXPERIMENTAL_CONTROL` and are fixed before a confirmatory run.

## Gate B — authority

Optimization remains candidate metadata until the normal BioOS/NOEMA authority path admits execution.

```text
runtime_execution_authority = false
production_runtime_write = false
canon_promotion = false
```

## Gate C — physical Dell measurement

Call-count and process-CPU-time reductions are computational proxies. Energy claims require direct target-hardware evidence.

The first physical run records at least one direct energy channel:

```text
wall joules / integrated wall power
CPU package energy where RAPL is exposed
GPU energy/power where NVIDIA telemetry is exposed
controlled battery discharge delta where suitable
```

and additionally records temperature, semantic workload, ticks, wakeups and admitted transitions.

The comparison uses identical semantic workload, initial state, horizon and thermal-control protocol.

Primary score:

\[
\epsilon_M = E_{external}/N_{admitted\ semantic\ transitions}.
\]

## Gate D — repeatability

A physical-energy result advances only after repeated baseline/normalized windows with ordering randomized or alternated to reduce thermal-order bias.

## Current frontier

```text
unit tests                         PASS 15/15
live NOEMA event gate              PASS, 60% wakeup reduction
pure QHTRI macro-step shadow       PASS, selected stride 12
hybrid macro-step                  BLOCKED_BY_RELATIONAL_GATE
exact tested-byte audit            PASS
physical Dell joule measurement    PENDING
runtime promotion                  PENDING
```
