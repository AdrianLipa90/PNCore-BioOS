# PN Realization Adapter v0.1

Status: ARCHITECTURE CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: BioOS v0.4

## Purpose

Define the boundary between encoding-independent PN analog-relational state and a concrete machine/device representation.

A realization adapter is a bidirectional, versioned map:

```text
SEMANTIC_STATE <-> REALIZATION
```

subject to explicit fidelity and authority rules.

## Adapter contract

Every adapter declares:

```text
ADAPTER_ID
SOURCE_SCHEMA
TARGET_FORMAT
DIRECTION
FIDELITY_CLASS
CANONICALIZATION_VERSION
SOURCE_SEMANTIC_COMMITMENT
REALIZATION_COMMITMENT
ROUNDTRIP_POLICY
EVIDENCE_REF
```

## Fidelity classes

```text
EXACT_SEMANTIC
    decode(encode(S)) is semantically identical to S.

EXACT_SAMPLE
    exact sampled/quantized observation bytes are preserved,
    while the semantic object retains the declared observation model.

LOSSLESS_TRANSFORM
    representation differs but exact semantic/sample recovery is required.

RECONSTRUCTION
    decoded state is a separately identified reconstruction with explicit metrics.
```

A reconstruction never inherits exact-source identity merely because it is similar.

## Adapter identity rule

```text
SEMANTIC_ID != REALIZATION_ID
```

Changing realization without changing semantic state must preserve `SEMANTIC_ID` and produce a new or reused `REALIZATION_ID` according to the target format's content identity.

## Initial v0.4 adapter registry

```text
IEEE754_F64_LE_36
    T36 phase/sample surface <-> 288-byte float64-le vector

T36I_BINARY_V0_1
    T36 Identity semantic state <-> exact 256-byte T36I record

PNVH_BINARY_V0_1
    36D bootstrap semantic handoff <-> 416-byte PNVH record

PAUX_EXACT_V0_1
    admitted analog state/sample <-> exact PAUX carrier

PAUX_C_V0_1
    admitted analog state/sample <-> reversible compressed PAUX carrier

PAUX_R_V0_1
    source semantic state -> reconstruction representation

PNSTORE_MEDIA_V0_1
    persistence generation <-> 4096-byte extent / 64KiB media geometry

DNCRYPT_BINARY_ENVELOPE_V0_1
    admitted plaintext realization <-> authenticated encrypted representation

TERMINAL36D_V8
    typed 36D execution state <-> current Terminal36D runtime representation
```

## Authority

Adapters do not gain semantic, capability or effect authority from serialization.

```text
semantic identity -> State Memory / source semantic object
capability         -> PNCAP
effect             -> AUX
persistent current -> PNStore admitted generation
```

## Decode admission

A decoded representation becomes admitted semantic state only after:

```text
representation integrity
 -> adapter-specific verification
 -> semantic normalization
 -> semantic commitment recomputation
 -> lineage/context validation
 -> domain admission
```

## Encode admission

Encoding a semantic state for a destination requires an explicit destination/profile choice. The destination selects representation; representation never selects semantic meaning.

```text
STATE + DESTINATION + POLICY
 -> ADAPTER_SELECTION
 -> ENCODE
 -> REALIZATION_RECEIPT
```

## Migration rule

v0.4 is additive. Existing v0.3 binary contracts remain frozen references. Migration proceeds by wrapping them with adapters and proving equivalence before any native consumer stops reading the legacy representation directly.
