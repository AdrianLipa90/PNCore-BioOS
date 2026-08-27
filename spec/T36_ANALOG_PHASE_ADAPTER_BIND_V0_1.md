# T36 Analog Phase Adapter Binding v0.1

Status: IMPLEMENTED CROSS-REPO BINDING CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: BioOS v0.4

## Purpose

This binding establishes the first concrete BioOS v0.4 proof that semantic state identity precedes machine representation.

The source authority is:

```text
repo   AdrianLipa90/PNV-State-Memory
branch feat/pnv-state-memory-analog-native
module src/pnv_state_memory/t36_phase_adapter.py
```

The semantic layer is:

```text
PAUX[PHASE][A]
  -> T36_PHASE_FIELD
```

The first machine realization is:

```text
PAUX[PHASE][EXACT]
  -> IEEE754_F64_LE_36
  -> 36 x float64-le
  -> 288 bytes
```

## Identity hierarchy

The adapter binds three independent identities:

```text
SEMANTIC_COMMITMENT
CHECKPOINT_OBJECT_ID
REALIZATION_ID
```

`SEMANTIC_COMMITMENT` is derived from the PASA semantic normal form.

`CHECKPOINT_OBJECT_ID` binds lineage, checkpoint evidence and realization bindings.

`REALIZATION_ID` binds exact machine bytes under the adapter domain.

This allows a new realization or new evidence annotation to preserve the same semantic state commitment.

## Semantic T36 phase field

The native phase state is:

```text
T36_PHASE_FIELD = {
  identity_context,
  phi[0..35],
  geometry,
  temporal_state,
  semantic_evidence
}
```

Each sampled phase coordinate enters semantic state as a periodic observation:

```text
PERIODIC_OBSERVATION(
  cycle = 2PI,
  orientation = +1,
  coordinate = OBSERVED_SCALAR(
    quantity = phi[i],
    unit = rad,
    estimate,
    uncertainty,
    source_receipt,
    observation_generation
  )
)
```

The adapter boundary converts admitted finite IEEE-754 values into explicit semantic observations. The resulting semantic commitment carries the source observation provenance and declared temporal context.

## Exact-sample realization

The float64 adapter uses:

```text
ADAPTER_ID      IEEE754_F64_LE_36
FIDELITY_CLASS  EXACT_SAMPLE
FRAME_BYTES     288
DIMENSION       36
```

The realization identity is content-addressed over the exact 288 source bytes.

Exact-source recovery uses the attached realization bytes together with `verify_exact_sample()`.

A deterministic canonical materializer also exists for destinations that request a fresh float64 realization from semantic state.

## Signed-zero witness

IEEE-754 permits distinct byte images for `+0.0` and `-0.0`. PASA canonical phase observation maps both to the same zero-valued semantic coordinate while the realization identity preserves the exact source sample.

Therefore the tested relation is:

```text
SEMANTIC_COMMITMENT(+0.0 sample)
  ==
SEMANTIC_COMMITMENT(-0.0 sample)

REALIZATION_ID(+0.0 bytes)
  !=
REALIZATION_ID(-0.0 bytes)
```

This is the first explicit v0.4 witness of encoding-independent semantic identity.

## State Memory annotation

A realization binding may be added as an `EVIDENCE_ANNOTATION` descendant:

```text
semantic state S
  -> checkpoint O_n
  -> bind IEEE754_F64_LE_36 realization
  -> checkpoint O_n+1
```

with:

```text
SEMANTIC_COMMITMENT(O_n) == SEMANTIC_COMMITMENT(O_n+1)
OBJECT_ID(O_n)            != OBJECT_ID(O_n+1)
```

This provides a persistence path in which materialization evidence evolves while semantic state identity remains stable.

## Runtime materialization

The existing live T36 files under `/dev/shm/ciel_noema` remain the current physical float64 realization boundary. A live v0.4 witness requires an ACTIVE surface, source receipt and current generation context.

The current tool container used for this implementation stage has no mounted `/dev/shm/ciel_noema` surface, so the live-source receipt remains a subsequent gate.

## Evidence

State Memory source blobs:

```text
analog_state.py         af1fefc9850b970ccb4b6ded8474445ad18e05e0
t36_phase_adapter.py    e052a1b3bd0ed80582bc04f874a444a0b8ffb0ef
test_t36_phase_adapter  6a188c5f4df2e18b968e541d8f449e2c911477ff
```

Local behavioral source reconstruction passed the core identity/adapter checks. Private-repository GitHub Actions currently creates the job with no executable step record; CI is classified as infrastructure-unresolved rather than source regression.

## Next gate

The next identity adapter is:

```text
PAUX[IDENTITY][A]
  <->
T36I_BINARY_V0_1
```

After that, Identity NEXUS can consume `PAUX[PHASE][A]` directly and retain float64 only at its input adapter boundary.
