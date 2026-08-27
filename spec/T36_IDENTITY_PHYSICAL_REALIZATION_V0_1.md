# T36 Identity Physical Realization v0.1

Status: IMPLEMENTED HOST/ASSEMBLY CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false

This contract refines `T36_IDENTITY_CRYSTAL_V0_1` for the first x86_64 realization. It is normative for the v0.3 implementation branch where it is more specific than the architecture-level wording.

## Hash derivation boundary

The first physical realization does not implement a hidden or approximate SHA-256 primitive inside PNCore. Identity/configuration hashes are derived by deterministic host/provisioning tools and then validated by target code.

Domain-separated derivations are:

```text
CRYSTAL_ID = SHA256(
  ASCII("T36-ID/v0.1") || GENESIS_ANCHOR
)

GENESIS_ANCHOR_COMMITMENT = SHA256(
  ASCII("T36-GENESIS-COMMIT/v0.1") || GENESIS_ANCHOR
)

ORIGIN_BINDING_SHA256 = SHA256(
  ASCII("T36-ORIGIN/v0.1") ||
  CRYSTAL_ID ||
  PNVH_VECTOR_SHA256 ||
  SOURCE_CONTEXT_SHA256 ||
  BASIS_BINDING ||
  PNR_BINDING
)

CONFIGURATION_SHA256 = SHA256(
  ASCII("T36-CONFIG/v0.1") ||
  PNVH_VECTOR_SHA256 ||
  BASIS_BINDING ||
  SOURCE_CONTEXT_SHA256 ||
  PNROM_CODE_BINDING ||
  PNR_BINDING ||
  PROGRAM_BINDING ||
  SCHEDULER_BINDING
)
```

The raw `GENESIS_ANCHOR` is provisioning material. The build receipt records its commitment, not the raw 32 bytes.

## Non-circular PNROM binding

`PNROM_CODE_BINDING` means an ordered binding over code/build inputs with these exact exclusions:

```text
EXCLUDE PNVH_TEMPLATE
EXCLUDE T36_IDENTITY_TEMPLATE
```

This avoids an impossible self-reference in which a final ROM hash would be embedded inside the same ROM bytes being hashed.

The current host utility is:

```text
tools/pnrom_code_binding_v01.py
```

It hashes ordered labeled inputs under domain `PNROM-CODE-BINDING/v0.1`.

`PNR_BINDING` binds the historical `PNR1` relocatable object and the append-only `T36X` extension under domain `PNR-T36-BINDING/v0.1`.

## Physical working addresses

```text
PNVH working record          0x5000   416 bytes
T36 identity working record  0x5900   256 bytes
T36 closure scratch          0x5a00   256 bytes
```

The scratch record is evidence-only boot workspace. It is not persistent identity and does not become a State Memory object.

## PNROM materialization

In long mode PNROM copies:

```text
pnvh_template         -> 0x5000
T36 identity template -> 0x5900
```

and transfers control to:

```text
t36_identity_boot_entry
```

before `pncore_entry`.

## Pre-PNCore admission

`t36_identity_validate` requires:

```text
MAGIC             T36I
VERSION           1.0
RECORD_BYTES      256
VECTOR_DIM        36
FLAGS & 0x7       0x7
PNVH_VECTOR_SHA   exact equality
SOURCE_CONTEXT    exact equality
BASIS_BINDING     exact equality
```

The boot gate then copies the record to scratch and verifies:

```text
sheet(n)   = 0
sheet(n+1) = 1
sheet(n+2) = 0
FOUR_PI_CLOSED(record_n, record_n_plus_2) = TRUE
```

`FOUR_PI_CLOSED` requires unchanged:

```text
CRYSTAL_ID
CONFIGURATION_SHA256
BOOT_EPOCH
```

and exact:

```text
phase_index_b = phase_index_a + 2
```

Failure halts before PNCore admission.

## Append-only PNR extension

Historical `PNR1` bytes remain unchanged. v0.3 adds a 48-byte `T36X` extension with:

```text
magic/version
T36 working address
record bytes
t36_identity_boot_entry
t36_identity_validate
t36_identity_spinor_sheet
t36_identity_advance_tick
t36_identity_four_pi_closed
```

Persistent-device continuation and bare-metal State Memory bindings remain zero until separately admitted.

## State Memory boundary

The physical record supplies the crystal context. PNV-State-Memory owns persistent logical lineage:

```text
CRYSTAL_GENESIS
CRYSTAL_CHECKPOINT
BOOT_GAP
BOOT_CONTINUATION
```

`BOOT_GAP` increments `boot_epoch` exactly once while preserving the last admitted `phase_index` and state. It does not synthesize hidden phase evolution during power-off.

## Evidence boundary

Current implementation evidence may establish:

```text
HOST_RECORD_DERIVATION
EXACT_256_BYTE_CODEC
ASSEMBLY_BUILD
STATE_MEMORY_LINEAGE
PAUX_EXACT_RECONSTRUCTION
```

It does not by itself establish:

```text
QEMU_BOOT
PHYSICAL_BOOT
DEVICE_BACKED_PERSISTENCE
PRODUCTION_GENESIS_PROVISIONING
```
