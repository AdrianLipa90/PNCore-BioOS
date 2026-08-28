# PNFS Cross-Repository Authority Contract v0.1

Status: `NORMATIVE CANDIDATE`

## 1. Purpose

This contract assigns normative ownership for PNFS semantics across the existing PhaseNav repositories.

The authority graph is:

```text
PNCS
  -> scalar-tau codec and T36 witness semantics

PNV-State-Memory
  -> liminal-segment validation and checkpoint lineage

PNCore-BioOS / PNFS
  -> object integration, namespace, physical realization, placement and compatibility surfaces
```

## 2. PNCS authority

PNCS SHALL own:

```text
scalar-tau symbol alphabet
TauFrame construction and decoding
frame commitment
whole-lane T36 witness construction
witness commitment
exact PNH5 TauFrame realization adapter
GREMLIN candidate compilation for codec relations
```

PNFS consumers MUST use an explicitly identified PNCS codec contract version.

## 3. PNV-State-Memory authority

PNV-State-Memory SHALL own:

```text
Liminal segment schema
parent-checkpoint continuity
semantic-layer admission
checkpoint object construction
checkpoint object identity
checkpoint serialization validation
contiguous recovery lineage rules
```

PNFS MUST treat a checkpoint as authoritative only after validation by the active State Memory contract.

## 4. PNCore-BioOS / PNFS authority

PNCore-BioOS SHALL own:

```text
PNODE integration
FILE_ID integration policy
namespace bindings
PNH5 container framing and manifest
REALIZATION_ID
multi-device placement
physical durability policy
FUSE/POSIX compatibility mapping
snapshot roots
retention and garbage collection
cross-repository provenance aggregation
```

## 5. Commitment holonomy

The following bindings MUST be preserved exactly:

```text
PNCS.frame_commitment
  -> StateMemory.carrier_commitment
  -> BioOS/PNFS tau-frame commitment binding

PNCS.witness_commitment
  -> StateMemory.t36_witness_commitment
  -> BioOS/PNFS T36 witness commitment binding

StateMemory.checkpoint_object_id
  -> BioOS/PNFS PNODE.current_checkpoint
  -> PNH5 manifest checkpoint identity
```

## 6. GREMLIN boundary

GREMLIN MAY:

- propose relational-isomorphism fragments;
- merge compatible candidate fragments;
- compile candidate KAKU, RADICALS and OPERATORS;
- generate candidate codec relations;
- audit commitment paths.

GREMLIN outputs SHALL remain `CANDIDATE_ONLY` until admitted by the owning contract and validator.

Runtime authority, filesystem head publication, checkpoint promotion and garbage collection decisions require their respective owning validators.

## 7. Version binding

Every persisted PNFS object or realization that depends on cross-repository semantics MUST record the contract identifiers required to decode and validate it.

At minimum, a PNH5 realization MUST identify:

```text
PNCS codec contract
State Memory checkpoint contract
PNFS realization contract
```

## 8. Upgrade rule

A contract upgrade MUST provide one of:

```text
exact backward reader compatibility
explicit migration transform with receipt
explicit version-pinned legacy reader
```

A migration that changes logical content MUST emit a new content commitment and checkpoint lineage event.

## 9. Validation failure ownership

The component that owns the failed invariant MUST emit the primary failure class.

BioOS/PNFS MAY wrap that failure with realization or operation context while preserving the original class and evidence.

## 10. Required cross-repository receipt fields

```text
FILE_ID
PNCS contract id
State Memory contract id
PNFS contract id
input commitment set
output commitment set
validator identities
verdict
```
