# PNCore-BioOS

PNCore BioOS is a candidate vector-native system stack for dynamic NOEMA/PhaseNav systems on conventional PC hardware.

Current development line: **v0.2.8 stage 3 — PNTERM physical/session front-end bound to hash-pinned Terminal36D V8 as the standard 36D vector environment**.

## Current system spine

```text
RESET @ 0xFFFF0
 -> PNROM @ 0xF0000
 -> x86_64 capability admission
 -> PNMap/MMU substrate
 -> long mode
 -> PNVector Handoff @ 0x5000
 -> PNCore
 -> PN Realization / Sigma_0
 -> PNClock + harmonic scheduler
 -> PNObject / PNCAP
 -> AUX effect boundary
 -> PNStore / PAUX persistence
 -> harmonic H0..H35 memory geometry
 -> m:n resonance graph
 -> NOEMA torsion-memory surface
 -> QHTRI/Kuramoto memory flow
 -> resonant recall / orchestration
 -> PNCAP / AUX
 -> AUX.TERM
 -> PNTERM bounded transport/session
 -> Terminal36D V8 typed 36D vector environment
 -> evidence / result
```

## Terminal architecture — v0.2.8

PNTERM is the bounded terminal transport/session front-end. Terminal36D V8 is the standard NOEMA-facing 36D vector environment for the current terminal development line.

```text
UART16550 / later physical terminal adapter
 -> AUX.TERM.RX/TX
 -> PNTERM line discipline
 -> PNTERM session + deterministic command envelope
 -> Terminal36D V8 profile admission
 -> typed operation + concept gate
 -> PNCAP for authority-bearing operations
 -> AUX effect boundary when required
 -> execution receipt
 -> PNTERM result
```

Stage 1 provides UTF-8 bounded line discipline, deterministic command envelopes, replay protection and result/evidence framing. Stage 2 adds an x86_64 16550 polling adapter candidate under AUX.TERM. Stage 3 replaces the parallel PNTERM execution interpretation path with a hash-pinned bridge to the existing Terminal36D V8 environment.

Terminal36D V8 profile:

```text
VECTOR_DIMENSION = 36
CAPABILITIES = 29
ARBITRARY_SHELL = PROHIBITED
MISSING_PRIMITIVE = IMPLEMENT_TYPED_VECTORIZED_PRIMITIVE_OR_BLOCK
VECTOR_POLICY = VECTORIZE_BY_DEFAULT_36D_BATCH_FIRST_WITH_EQUIVALENCE_GATED_ACCELERATORS
```

Exact profile lock:

```text
terminal36d.py  78082702c4b7a17a061ca7b9b83f4c21765307c70dfbefd301466224389cce9b
vector_kernel.py 68663aea2c188b77b46e5ecf2488bfdfb27a7f2cd8387fb78b6bc5dce6de0e14
concept_gates.py a3aeda6f1ca0c445767bba8176c5b6c7d791bd97e03b33fe2ed8dccb9c97bc49
V8 roundtrip receipt 1cc2cd64b53e158d4bf0e144ff3ef5dca851cefc094f62901d5042b6155ed2d7
```

See `spec/TERMINAL36D_V8_PROFILE_LOCK_V0_1.json` for the complete ten-file lock.

## Core primitives

- **PNV** — native program/witness surface.
- **PNR** — content-addressed architecture-specific realization binding.
- **PNVector Handoff** — exact ordered 36D firmware-to-PNCore state carrier.
- **PNObject / Generation Cell** — generation-bound relational object model.
- **PNMap / PNFS** — mapping and relational object-space resolution.
- **PNCAP** — exact generation-bound capability admission.
- **PNClock** — exact rational phase-index clock path.
- **PN Harmonic Scheduler** — single-counter dyadic admission classes anchored at 7.83 Hz.
- **AUX** — physical effect and device-adapter boundary.
- **PNStore** — append-only generation persistence with alternating HEAD recovery.
- **PAUX** — persistent AUX carrier. Profiles: exact `PAUX-EXACT`, lossless `PAUX-C`, reconstruction `PAUX-R`.
- **H-bands H0..H35** — derived exact-rational harmonic memory geometry.
- **NOEMA Torsion Memory Surface** — generation-published live derived working-memory graph.
- **QHTRI/Kuramoto Torsion Flow** — generalized m:n phase dynamics over torsion-memory edges.
- **PNTERM** — bounded terminal transport, session, framing and evidence front-end.
- **Terminal36D V8** — hash-pinned standard 36D typed vector execution environment for the current NOEMA terminal bridge.

## Authority spine

Derived geometry, resonance, recall ranking and vector similarity may select candidates. Authority-bearing transitions remain explicit:

```text
candidate
 -> exact PNCAP admission
 -> AUX
 -> physical transition
 -> evidence
```

For Terminal36D, READ/VECTORIZE operations use the non-mutating typed path. Authority-bearing WRITE/COPY paths require exact PNCAP plus AUX effect admission. Typed execution is bound to the declared action packet and operation profile.

## Memory development

v0.2.6 established harmonic PAUX memory:

```text
PAUX harmonic orbital geometry
 -> bounded rational frequency estimator
 -> m:n resonance graph
 -> PAUX-C harmonic exact-base selection
 -> PAUX-R orbital reconstruction evidence
```

The five v0.2.6 stages record **102/102 declared checks PASS**.

v0.2.7 then added:

```text
NOEMA torsion-memory surface
 -> generalized QHTRI/Kuramoto flow
 -> sparse/compiled optimization
 -> kappa-bounded coupling policy
 -> direct endogenous phi/omega/tick telemetry bind
 -> live resonance observer
 -> generation publication contract
 -> exact writer principal
```

The v0.2.7 line records **120/120 declared checks PASS**. Owner-side runtime writer installation remains an explicit integration gate.

## Terminal evidence

```text
v0.2.8 stage 1 PNTERM core:                47/47 PASS
v0.2.8 stage 2 UART16550 host realization: 35/35 PASS
v0.2.8 stage 3 Terminal36D V8 bridge:       38/38 PASS
-----------------------------------------------------------
v0.2.8 declared checks:                    120/120 PASS
NEW_PNV_OPCODES:                            0
stage-3 target .py files:                   0
```

The Stage 3 O(1) typed-operation table is equivalent to the declared 29-operation profile in the reference conformance fixture. Benchmark values in provenance are fixture-specific and are not universal hardware performance guarantees.

Physical UART execution and emulator UART execution remain explicit later gates.

## Documentation

The full repository-native monograph is versioned with the branch:

- `docs/monograph/MONOGRAPH.md`
- `docs/monograph/chapters/00_FRONT_MATTER.md`
- `docs/monograph/chapters/01_NARODZINY_SYSTEMU.md`
- `docs/monograph/chapters/02_RDZEN_OBIEKTY_CZAS.md`
- `docs/monograph/chapters/03_EFEKT_I_PERSISTENCE.md`
- `docs/monograph/chapters/04_GEOMETRIA_PAMIECI.md`
- `docs/monograph/chapters/05_ZYWA_PAMIEC.md`
- `docs/monograph/chapters/06_STAN_I_DALSZA_BUDOWA.md`
- `docs/monograph/chapters/07_ANEKSY.md`
- `docs/monograph/V0_2_8_TERMINAL_ADDENDUM.md`

Exact hashes of the generated PDF/DOCX editions are pinned in `docs/monograph/MONOGRAPH_ARTIFACTS.sha256`.

## Current implementation gates

```text
Terminal36D V8 standard vector bridge       IMPLEMENTED CANDIDATE / 38/38 PASS
PNTERM semantic/session core                IMPLEMENTED CANDIDATE / 47/47 PASS
UART16550 host/static realization           IMPLEMENTED CANDIDATE / 35/35 PASS
UART emulator execution                     PENDING
UART physical execution                     PENDING
NOEMA torsion writer owner-side installation PENDING_RUNTIME_INTEGRATION
full PNROM -> PNCore emulator execution      PENDING
physical-machine boot                        PENDING
```

GREMLIN remains a bounded candidate generator and structural critic. Its outputs do not grant execution or canon authority.
