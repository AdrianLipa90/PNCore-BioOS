# PNFS PNH5 Realization Contract v0.1

Status: `NORMATIVE CANDIDATE`

## 1. Role

`.pnh5` is the portable PNFS realization container for one logical PNLF lineage state or lineage segment set.

It SHALL preserve cross-repository identity and commitment bindings without redefining PNCS codec semantics or State Memory checkpoint semantics.

## 2. Required manifest bindings

A `.pnh5` manifest MUST bind at least:

```text
schema
generation
FILE_ID
CONTENT_COMMITMENT
CHECKPOINT_OBJECT_ID
TAU_FRAME_COMMITMENT
T36_WITNESS_COMMITMENT
tau_start
tau_end
PNCS codec contract
State Memory contract
realization profile
manifest commitment
```

## 3. Required record classes

Initial record classes are:

```text
TAUF  exact PNCS tau-frame realization
CHKP  serialized State Memory checkpoint
META  optional PNFS metadata extension
INDX  optional index acceleration record
```

Unknown mandatory record types MUST be rejected until their semantics are registered.

Unknown explicitly optional record types MAY be skipped only when their framing and commitment remain verifiable.

## 4. Tau frame

Each `TAUF` record MUST carry enough exact material to reconstruct the PNCS tau-frame commitment and T36 witness commitment.

The decoder MUST verify:

- frame record seal;
- exact tau symbol grid;
- frame index;
- whole-lane T36 dimensionality;
- block/content commitment;
- frame commitment;
- witness commitment.

## 5. Checkpoint record

Each authoritative `.pnh5` lineage realization MUST contain at least one `CHKP` record matching the manifest `CHECKPOINT_OBJECT_ID`.

Checkpoint deserialization MUST pass the State Memory checkpoint validator before the record can anchor recovery.

## 6. Container seal

The container SHALL have a deterministic whole-container seal over the encoded manifest and all records in order.

A seal mismatch MUST yield `FAIL_CLOSED`.

## 7. Identity closure

After reopen, the implementation MUST verify:

```text
manifest.FILE_ID == checkpoint.FILE_ID
manifest.CONTENT_COMMITMENT == checkpoint cumulative content commitment
manifest.CHECKPOINT_OBJECT_ID == reconstructed checkpoint object id
manifest.TAU_FRAME_COMMITMENT == reconstructed frame-set commitment
manifest.T36_WITNESS_COMMITMENT == reconstructed witness-set commitment
```

## 8. Byte-exact decode gate

When `.pnh5` represents a byte payload compatibility view, full decode MUST reproduce the canonical payload byte sequence exactly before a `BYTE_EXACT_PASS` receipt may be emitted.

## 9. Atomic file creation

A durable `.pnh5` write SHOULD use:

```text
temporary file
-> write complete container
-> fsync temporary file
-> atomic replace/rename
-> fsync containing directory
```

## 10. Dataset compatibility view

A hierarchical dataset view MAY be exposed over the same FILE_ID and CONTENT_COMMITMENT.

Dataset paths are projection metadata and MUST preserve the underlying PNFS object identity bindings.

## 11. Required error classes

```text
PNH5_MANIFEST_FAILURE
PNH5_RECORD_FRAME_FAILURE
PNH5_TAU_FRAME_FAILURE
PNH5_CHECKPOINT_FAILURE
PNH5_CONTAINER_SEAL_FAILURE
PNH5_IDENTITY_CLOSURE_FAILURE
PNH5_BYTE_EXACT_FAILURE
```
