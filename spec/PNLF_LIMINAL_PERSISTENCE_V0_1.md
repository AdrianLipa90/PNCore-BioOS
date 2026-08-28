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
  -> realization adapter
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

## PNH5 compatibility view

`.pnh5` is the hierarchical dataset compatibility view over the same PNLF file/content identity. Dataset paths and schemas are view metadata while the source PNLF manifest remains the persistence binding.

## GREMLIN codec relation

PNCS owns the GREMLIN isomorphic compiler specialization. The codec is formed from two bounded relational fragments joined on the shared `K.LIMINAL.SEGMENT` node:

```text
PNCS TAU FRAME <-> T36 WITNESS <-> State Memory
State Memory <-> BioOS PNLF FILE <-> PNH5 VIEW
```

GREMLIN performs the isomorphic union first and then materializes one candidate KAKU set, one RADICAL, deterministic OPERATORS and one READ_ONLY PNV conformance program. Canon promotion remains an explicit authority boundary.

## Evidence

Local executable candidate receipts recorded before repository integration total 30/30 PASS across Liminal/State semantics, bounded analog perturbation, tau self-calibration and a 128 KiB binary end-to-end file roundtrip. Physical carrier validation is the next evidence gate.
