# BioOS v0.4 Analog-Native Migration Plan

Status: ACTIVE IMPLEMENTATION PLAN / CHYBA / canon_allowed=false
Branch: `feat/bioos-v0.4-analog-native-state`
Base: BioOS v0.3 monograph/artifact frontier

## Goal

Invert the dependency direction so BioOS native semantics precede machine encoding.

```text
semantic / relational state
 -> identity + lineage
 -> destination-selected realization adapter
 -> machine/device representation
```

The v0.3 binary realizations remain preserved as compatibility, persistence, crypto and hardware adapters.

## Stage 0 — Freeze v0.3 reference realizations

Preserve current evidence and hashes for:

```text
PNVH_BINARY_V0_1
T36I_BINARY_V0_1
IEEE754_F64_LE_36
PAUX-EXACT / PAUX-C / PAUX-R
PNSTORE_MEDIA_V0_1
DNCRYPT_BINARY_ENVELOPE_V0_1
TERMINAL36D_V8
```

These become equivalence witnesses for v0.4.

## Stage 1 — PASA semantic core

Implement PN Analog State Algebra:

```text
EXACT_INTEGER
EXACT_RATIONAL
SYMBOLIC_CONSTANT
PERIODIC_PHASE
OBSERVED_SCALAR
RELATION
PN_ANALOG_STATE
```

Canonical identity uses a versioned semantic normal form with explicit units, uncertainty and provenance.

## Stage 2 — State Memory first

Repository: `AdrianLipa90/PNV-State-Memory`
Branch: `feat/pnv-state-memory-analog-native`

Move logical memory identity to:

```text
semantic commitment
 -> checkpoint identity
 -> lineage
 -> realization bindings
```

Keep separate:

```text
semantic_evidence
checkpoint_evidence
realization_evidence
```

First code target: `src/pnv_state_memory/analog_state.py`.

## Stage 3 — PAUX functional registry

Adopt:

```text
PAUX[FUNCTION][REPRESENTATION]
```

Functions begin with:

```text
PHASE TIME IDENTITY MEMORY SEMANTIC INTENT
AUDIO VISION SPATIAL DEVICE_STATE TRANSPORT
```

Representations:

```text
A EXACT C R
```

`A` is native semantic state; `EXACT/C/R` are realization profiles.

## Stage 4 — T36 and identity adapters

Prove:

```text
T36_PHASE[A] <-> IEEE754_F64_LE_36
T36_IDENTITY[A] <-> T36I_BINARY_V0_1
BOOTSTRAP_36D[A] <-> PNVH_BINARY_V0_1
```

The semantic state owns identity. Adapter receipts own exact materialization evidence.

## Stage 5 — NEXUS semantic API

Identity NEXUS consumes `PAUX[SEMANTIC][A]` / T36 semantic phase state directly.

Dictionary term realization remains canonical 36D semantic input. JSON live surfaces become publication adapters.

NEXUS activation checkpoint persists semantic activation + provenance through State Memory.

## Stage 6 — CQCL Living semantic API

CQCL consumes:

```text
T36 semantic identity
NEXUS activation semantic state
State Memory context
live QHTRI semantic observation
Dictionary authority
```

Its program/candidate object becomes `PAUX[INTENT][A]`. JSON remains an inspection/publication adapter.

## Stage 7 — QHTRI / live field adapters

The current mmap channels remain hardware/runtime realizations:

```text
phi   -> IEEE754_F64_LE_36 adapter
omega -> IEEE754_F64_LE_36 adapter
tick  -> integer/time realization adapter
```

The QHTRI semantic state binds phase, natural frequency, tick lineage and tether evidence independently of path.

## Stage 8 — Persistence and crypto adapters

Persistence selection:

```text
State Memory semantic checkpoint
 -> PAUX profile
 -> optional DNCrypt
 -> PNStore
 -> device backend
```

DNCrypt protects a selected realization and preserves the source semantic commitment through authenticated metadata.

PNStore remains immutable-generation persistence realization.

## Stage 9 — Native execution migration

PNCS/Terminal36D primitives progressively accept semantic-state handles rather than binary-format ownership. Adapter conversion occurs only for primitives whose implementation boundary requires it.

## Stage 10 — device codecs

Add function-specific adapters incrementally:

```text
AUDIO   -> PCM / future audio codecs
VISION  -> RGB/YUV/frame adapters
NETWORK -> packet/wire adapters
GPU     -> float/fixed-point device layouts
DISK    -> PNStore/device layouts
```

Codec development remains independent of semantic identity.

## Promotion order

```text
1 PASA normal form
2 State Memory semantic commitment
3 T36 float adapter equivalence
4 T36I identity adapter equivalence
5 PAUX registry
6 NEXUS semantic consumption
7 QHTRI semantic observation
8 CQCL Living semantic consumption
9 persistence/crypto adapter closure
10 PNCS/device migration
```

## Current status

```text
BioOS v0.4 branch              CREATED
PASA contract                  CREATED
Realization adapter contract   CREATED
PAUX functional registry       CREATED
State Memory analog branch     CREATED
State Memory analog spec       CREATED
State Memory reference code    CREATED
State Memory tests             CREATED
State Memory CI                SOURCE_CI_UNRESOLVED (runner/log infrastructure)
main                           UNCHANGED
```
