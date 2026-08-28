# BioOS PNLF Liminal Persistence v0.1

Status: ARCHITECTURE CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false

## Persistence spine

```text
PNObject / FILE_ID
  -> PNCS TAU FRAME
  -> whole-lane T36 block witness
  -> PNV-State-Memory Liminal segment
  -> State Memory consolidation checkpoint
  -> BioOS PNLF persistence manifest
  -> PNH5 binary realization container
```

The content parameter is scalar tau. Laboratory wall-clock belongs to realization evidence. The T36 lane supplies block-level relational/integrity evidence. State Memory supplies generation identity, lineage and recovery boundaries.

## Cross-repository commitment holonomy

The persistence binding follows one exact chain:

```text
PNCS.frame_commitment(frame)
  -> StateMemory.carrier_commitment
  -> BioOS.tau_frame_commitment

PNCS.witness_commitment(frame.witness)
  -> StateMemory.t36_witness_commitment
  -> BioOS.t36_witness_commitment
```

BioOS derives `FILE_ID`, `CONTENT_COMMITMENT` and `CHECKPOINT_OBJECT_ID` from a `PNV-LIMINAL-CHECKPOINT/0.1` object through `binding_from_state_checkpoint()`. A persistence manifest supplied with a checkpoint verifies generation and `tau_end` against that checkpoint before admission.

## Identity

```text
FILE_ID != CONTENT_COMMITMENT != CHECKPOINT_OBJECT_ID
TAU_FRAME_COMMITMENT != T36_WITNESS_COMMITMENT
```

The file identity is Genesis anchored. Content commitment changes with admitted content. Checkpoint identity changes with State Memory generation and lineage. Carrier and witness commitments remain separate integrity axes.

## PNLF generation

A BioOS persistence manifest binds:

```text
FILE_ID
CONTENT_COMMITMENT
CHECKPOINT_OBJECT_ID
TAU_FRAME_COMMITMENT
T36_WITNESS_COMMITMENT
[tau_start, tau_end]
active Liminal Memory layers
PNCS codec contract
State Memory contract
realization profile
```

## PNH5 view and binary realization

`.pnh5` preserves the same PNLF file/content identity through two linked layers:

```text
PNH5 VIEW
  -> dataset path/schema compatibility metadata
  -> PNH5 CONTAINER
  -> physical binary realization
```

The container implementation is `tools/pnh5_container_v01.py`. `TAUF` records are opaque exact PNCS tau-frame realizations. `CHKP` records are opaque canonical State Memory checkpoint serializations. BioOS verifies the manifest, record stream, record digests, checkpoint linkage and global container seal.

`write_pnh5()` performs temporary-file write, flush, fsync, atomic replace and reopen validation.

## GREMLIN codec relation

PNCS owns the GREMLIN isomorphic compiler specialization. The codec is formed from three bounded relational fragments:

```text
PNCS TAU FRAME <-> T36 WITNESS <-> State Memory
State Memory <-> BioOS PNLF FILE <-> PNH5 VIEW
PNH5 VIEW <-> PNH5 CONTAINER
```

The shared merge nodes are `K.LIMINAL.SEGMENT` and `K.PNH5.VIEW`. GREMLIN performs the isomorphic union first and then materializes one candidate KAKU set, one RADICAL, deterministic OPERATORS and one READ_ONLY PNV conformance program. Canon promotion remains an explicit authority boundary.

## Evidence

The pre-container local executable candidate receipts total 30/30 PASS across Liminal/State semantics, bounded analog perturbation, tau self-calibration and a 128 KiB binary end-to-end file roundtrip.

`PNH5_FIRST_REAL_CONTAINER_RECEIPT_V0_1` adds the first executed file realization closure:

```text
2477 source bytes
-> 39 exact TAU FRAME records
-> 15447-byte .pnh5
-> reopen
-> exact decode
```

Source and decoded SHA-256 are both:

```text
a3ce8b582c092ef91dea9e1125fc102ff71b1bd91da927e3aa2419147e21c061
```

The container ID is:

```text
b3326338a09c993b0afd6e0a482b572ee4ca620e9fe51f1950f4aea69b4d3f98
```

Evidence status: LOCAL_EXECUTABLE_CANDIDATE. Physical carrier validation remains a separate gate.
