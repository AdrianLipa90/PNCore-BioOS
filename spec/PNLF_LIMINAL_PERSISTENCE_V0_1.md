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

## Identity

```text
FILE_ID != CONTENT_COMMITMENT != CHECKPOINT_OBJECT_ID
```

The file identity is Genesis anchored. Content commitment changes with admitted content. Checkpoint identity changes with State Memory generation and lineage.

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

PNCS owns the GREMLIN isomorphic compiler specialization. The shared invariant connects `PNCS TAU FRAME`, `PNCS T36 WITNESS`, `PNV-State-Memory LIMINAL SEGMENT`, `BioOS PNLF FILE` and `PNH5 VIEW`. GREMLIN materializes candidate KAKU/RADICAL/OPERATORS and a READ_ONLY PNV conformance program. Canon promotion remains an explicit authority boundary.

## Evidence

Local executable candidate receipts recorded before repository integration total 30/30 PASS across Liminal/State semantics, bounded analog perturbation, tau self-calibration and a 128 KiB binary end-to-end file roundtrip. Physical carrier validation is the next evidence gate.
