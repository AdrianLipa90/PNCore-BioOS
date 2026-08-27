# T36 Identity Analog Adapter Binding v0.1

Status: IMPLEMENTED CROSS-REPO BINDING CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: BioOS v0.4

## Purpose

This binding places T36 identity semantics above the 256-byte physical record.

The semantic authority is:

```text
repo   AdrianLipa90/PNV-State-Memory
branch feat/pnv-state-memory-analog-native
module src/pnv_state_memory/t36_identity_state.py
schema T36_IDENTITY_CRYSTAL
```

The physical realization authority remains:

```text
repo   AdrianLipa90/PNCore-BioOS
tool   tools/t36_identity_record_v01.py
adapter tools/t36_identity_analog_adapter_v01.py
format T36I_BINARY_V0_1
bytes  256
```

## Native semantic identity state

The analog-native T36 identity state contains:

```text
CRYSTAL_ID
genesis_anchor_commitment
origin_binding_sha256
pnvector_payload_sha256
source_context_sha256
basis_binding
configuration_sha256
phase_index
boot_epoch
spinor_sheet
T^36 geometry
4PI spinor cycle
2PI projective cycle
f0 = 783/100 Hz
f_ID = 783/200 Hz
```

The semantic state preserves the existing split between stable crystal identity and evolving configuration/time state.

## Adapter-only structure

The T36I realization carries machine-format fields such as:

```text
magic
record version
record length
vector dimension field
flags
little-endian integer layout
```

These fields belong to `T36I_BINARY_V0_1` realization evidence.

The adapter maps the seven 32-byte bindings plus `phase_index` and `boot_epoch` into the semantic T36 identity state and derives `spinor_sheet = phase_index & 1` there.

## Identity hierarchy

```text
CRYSTAL_ID
  -> persistent identity anchor

SEMANTIC_COMMITMENT
  -> exact T36 identity/configuration/time state

CHECKPOINT_OBJECT_ID
  -> lineage and evidence-bearing State Memory object

REALIZATION_ID
  -> exact 256-byte T36I materialization
```

A configuration update keeps the same `CRYSTAL_ID` and creates a changed semantic commitment.

A phase step keeps the same `CRYSTAL_ID` and creates a changed semantic commitment.

A representation-policy change may keep the same semantic commitment while creating a changed `REALIZATION_ID`.

## Flags witness

The current physical admission requires the low binding bits `0x7`. Additional realization flags may vary under a versioned adapter policy.

The behavioral witness compares two 256-byte records carrying identical semantic fields and distinct valid flag words:

```text
flags = 0x00000007
flags = 0x0000000f
```

Result:

```text
SEMANTIC_COMMITMENT equal
REALIZATION_ID      distinct
```

This confirms that T36I policy bits belong to machine realization rather than semantic crystal identity.

## 4PI continuity

State Memory now exposes semantic continuity helpers:

```text
validate_identity_continuity(parent, child)
four_pi_closed(parent, descendant)
```

The semantic 4PI closure requires:

```text
same CRYSTAL_ID / genesis identity context
same configuration binding
same boot_epoch
phase_index(descendant) = phase_index(parent) + 2
```

The resulting spinor sheet returns to the starting sheet.

## Materialization

`materialize_t36i(state, flags=...)` chooses a physical T36I realization from semantic state. The adapter policy supplies the realization flags while semantic fields come from the State Memory object.

`decode_t36i(raw)` reconstructs semantic state, computes its semantic commitment, computes the exact realization identity and emits a realization binding.

`verify_t36i()` re-establishes both identities from the attached realization.

## Evidence

State Memory semantic source:

```text
t36_identity_state.py f59ad9e021451e2fcc75d91281762ba69c95bde1
```

BioOS physical record source:

```text
t36_identity_record_v01.py c079582523e5dd89089d5de1ca33d1d6f78b1b54
```

Behavioral checks performed during implementation:

```text
256-byte T36I pack/unpack geometry              PASS
flags-policy semantic invariance                PASS
flags-policy realization-identity distinction   PASS
phase progression changes semantic commitment   PASS
phase_index +2 semantic 4PI closure             PASS
configuration evolution preserves CRYSTAL_ID    PASS
boot continuation preserves CRYSTAL_ID           PASS
```

State Memory GitHub Actions remain infrastructure-unresolved with zero executable step records in the current private-runner path. Source promotion therefore remains candidate.

## Next gate

With both identity and phase represented analog-natively, Identity NEXUS can move to:

```text
T36_IDENTITY_CRYSTAL
  + T36_PHASE_FIELD
  + Dictionary term semantic states
  -> NEXUS semantic working state
```

The float64 phase surface then remains an ingress/egress adapter at the runtime boundary.
