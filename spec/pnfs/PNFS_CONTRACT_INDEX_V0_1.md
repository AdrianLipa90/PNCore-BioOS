# PNFS Contract Index v0.1

Status: `NORMATIVE CANDIDATE`

## Purpose

This directory defines the v0.1 normative contracts for the PhaseNav Natural File System (PNFS).

PNFS binds semantic object identity, scalar-τ content evolution, State Memory checkpoint lineage, portable `.pnh5` realization, physical placement, recovery, snapshots, garbage collection, and a POSIX/FUSE compatibility surface.

The architectural chain is:

```text
PNFS
  -> PNODE
  -> PNLF logical file
  -> PNCS scalar-τ frames
  -> whole-lane T36 witness
  -> State Memory checkpoint
  -> PNH5 / device realization
```

## Normative vocabulary

The terms `MUST`, `MUST NOT`, `SHALL`, `SHOULD`, `SHOULD NOT`, and `MAY` are normative requirements.

`FAIL_CLOSED` means the requested transition is rejected, the prior verified checkpoint remains authoritative, and no candidate state is promoted.

## Contract set

1. `PNFS_OBJECT_IDENTITY_ADDRESSING_CONTRACT_V0_1.md`
   - FILE_ID, content identity, checkpoint identity, realization identity, PNODE, namespace binding and semantic address.

2. `PNFS_WRITE_CHECKPOINT_CONTRACT_V0_1.md`
   - append path, liminal segment, τ-frame admission, crystallization and fsync boundary.

3. `PNFS_RECOVERY_CONTRACT_V0_1.md`
   - crash recovery, torn-tail handling, checkpoint verification and replay.

4. `PNFS_PNH5_REALIZATION_CONTRACT_V0_1.md`
   - portable `.pnh5` container semantics and exact cross-repository commitments.

5. `PNFS_MULTI_DEVICE_PLACEMENT_CONTRACT_V0_1.md`
   - NVMe/HDD/USB realization placement and durability classes.

6. `PNFS_POSIX_FUSE_CONTRACT_V0_1.md`
   - userspace filesystem surface, POSIX path compatibility and mutation mapping.

7. `PNFS_RETENTION_GC_SNAPSHOT_CONTRACT_V0_1.md`
   - snapshots, deduplication, retention states and reclamation.

8. `PNFS_CROSS_REPO_AUTHORITY_CONTRACT_V0_1.md`
   - ownership boundaries between PNCS, PNV-State-Memory and PNCore-BioOS.

## Global invariants

The following identities are distinct namespaces:

```text
FILE_ID
CONTENT_COMMITMENT
CHECKPOINT_OBJECT_ID
REALIZATION_ID
```

A canonical logical address has the form:

```text
(FILE_ID, tau, relation)
```

A POSIX path is a mutable namespace binding to `FILE_ID`.

The content carrier is scalar τ. Whole-lane T36 is the relational/integrity witness. State Memory is the crystallization authority. BioOS/PNFS is the integration and realization authority.

## Required provenance

Every implementation-level state transition that changes authoritative storage state MUST emit enough provenance to recover:

- input FILE_ID;
- parent checkpoint identity;
- admitted τ interval;
- content commitment;
- T36 witness commitment;
- resulting checkpoint identity;
- realization identity when physical persistence occurred;
- validator result.

Silent exception swallowing is forbidden. Validation failures MUST be externally observable and MUST preserve the prior verified state.
