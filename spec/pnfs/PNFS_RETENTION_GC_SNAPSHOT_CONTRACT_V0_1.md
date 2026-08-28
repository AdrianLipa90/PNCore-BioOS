# PNFS Retention, Snapshot and Garbage Collection Contract v0.1

Status: `NORMATIVE CANDIDATE`

## 1. Retention states

Every retained checkpoint, content object, and realization SHALL have an explicit lifecycle state.

Initial lifecycle states:

```text
ACTIVE
RETAINED
RECLAIMABLE
RECLAIMED
```

`ACTIVE` identifies state reachable from a published PNODE head.

`RETAINED` identifies state protected by snapshot, policy, provenance, mirror, or explicit retention rule.

`RECLAIMABLE` identifies state that has passed reachability and policy checks and is eligible for reclamation.

`RECLAIMED` records completed physical reclamation in provenance.

## 2. Snapshot identity

A PNFS snapshot SHALL be defined by an immutable checkpoint reference plus snapshot metadata:

```text
SNAPSHOT_ID
FILE_ID
CHECKPOINT_OBJECT_ID
creation provenance
retention policy
```

Snapshot creation MUST preserve the referenced checkpoint and every content/realization dependency required by the selected durability class.

## 3. Copy-on-write lineage

A new write after snapshot creation SHALL continue through a new liminal segment and checkpoint lineage.

Shared prior content MAY remain physically deduplicated while logical lineage references remain explicit.

## 4. Deduplication

PNFS MAY share one verified physical content realization across multiple logical references when the relevant content commitment and realization-format contract are identical.

Deduplication MUST preserve independent FILE_ID and checkpoint lineages.

Reference accounting MUST be exact enough to prevent reclamation of an object reachable from any ACTIVE or RETAINED root.

## 5. Reachability roots

The GC root set MUST include at least:

```text
published PNODE heads
retained snapshots
retained provenance anchors
configured mirror roots
open-handle pinned checkpoints
explicit administrative retention roots
```

## 6. Reclamation gate

An object may transition to `RECLAIMABLE` only after:

- reachability scan marks it unreachable from all roots;
- retention policy permits reclamation;
- required mirror policy is satisfied;
- no active recovery operation depends on it;
- no open handle pins it;
- provenance records the candidate decision.

Physical deletion MUST occur only from `RECLAIMABLE`.

## 7. Reclamation order

Dependency-aware reclamation SHOULD proceed from leaf realizations toward metadata references.

PNFS MUST preserve enough tombstone/provenance information to distinguish an intentionally reclaimed realization from an unexplained missing realization.

## 8. Snapshot deletion

Deleting a snapshot SHALL remove its snapshot root binding and trigger a new reachability evaluation.

Shared data remain retained while reachable from any other root.

## 9. Quotas

Quota policy MAY operate over logical bytes, exclusive physical bytes, shared physical bytes, checkpoint count, realization count, or a documented combination.

The accounting basis MUST be exposed to the caller.

## 10. Required error classes

```text
PNFS_GC_REACHABILITY_UNCERTAIN
PNFS_GC_PINNED_OBJECT
PNFS_GC_RETENTION_BLOCK
PNFS_GC_MIRROR_POLICY_BLOCK
PNFS_SNAPSHOT_BINDING_FAILURE
PNFS_DEDUP_BINDING_FAILURE
```
