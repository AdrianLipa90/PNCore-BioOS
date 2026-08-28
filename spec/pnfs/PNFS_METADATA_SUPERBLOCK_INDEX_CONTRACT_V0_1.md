# PNFS Metadata, Superblock and Index Contract v0.1

Status: `NORMATIVE CANDIDATE`

## 1. Metadata plane

PNFS SHALL maintain a metadata plane logically separated from payload realizations.

The metadata plane SHALL represent at least:

```text
filesystem identity
format version
registered device set
namespace roots
PNODE registry
checkpoint heads
realization registry
snapshot roots
retention roots
index generations
provenance anchors
```

## 2. Superblock

Each PNFS metadata store MUST have a superblock containing at least:

```text
PNFS_MAGIC
format_version
filesystem_id
superblock_generation
metadata_root_commitment
namespace_root_commitment
realization_registry_commitment
active_index_generation
previous_superblock_commitment
superblock_commitment
```

A superblock publication MUST be atomic according to the host realization contract.

## 3. Mirrored superblocks

The implementation SHOULD maintain at least two independently readable superblock generations on a persistent metadata device.

Recovery SHALL select the newest fully verified generation whose referenced metadata roots validate.

## 4. Append-oriented metadata log

Authoritative metadata mutations SHALL first be expressed as append-oriented metadata records.

Initial metadata record classes:

```text
PNODE_CREATE
PNODE_UPDATE
NAMESPACE_BIND
NAMESPACE_UNBIND
CHECKPOINT_HEAD_ADVANCE
REALIZATION_ADD
REALIZATION_STATE
SNAPSHOT_ADD
SNAPSHOT_REMOVE
RETENTION_STATE
INDEX_ROOT_ADVANCE
```

Each record MUST bind its parent metadata generation and record commitment.

## 5. Index

Indexes are acceleration structures over authoritative PNFS metadata and content-addressed objects.

An index MUST be reconstructible from authoritative records and checkpoints.

Initial required indexes:

```text
PATH -> FILE_ID
FILE_ID -> PNODE
CHECKPOINT_OBJECT_ID -> checkpoint location
CONTENT_COMMITMENT -> realization references
REALIZATION_ID -> physical location/state
SNAPSHOT_ID -> checkpoint root
```

## 6. Index publication

A rebuilt or incrementally updated index SHALL be written as a candidate generation, verified, and then published by advancing the active index root.

A failed candidate index MUST leave the previous verified index generation active.

## 7. Metadata-to-payload ordering

A new payload realization MUST reach the durability state required by policy before metadata publishes it as an authoritative available realization.

A metadata record MAY describe a `CANDIDATE` or `WRITTEN` realization before publication, provided its state is explicit.

## 8. Metadata recovery

Metadata recovery MUST verify:

```text
superblock commitment
previous-generation link
metadata root commitment
namespace root commitment
PNODE/checkpoint bindings
realization registry bindings
index generation commitment
```

A damaged newest generation SHALL permit fallback to the newest earlier fully verified generation.

## 9. Cache authority

In-memory caches MAY accelerate namespace, PNODE, checkpoint, and realization lookup.

Each cached object MUST carry a generation/freshness token tied to the authoritative metadata state.

Stale cache entries MUST be invalidated or revalidated before mutation authority is granted.

## 10. Required error classes

```text
PNFS_SUPERBLOCK_FAILURE
PNFS_METADATA_CHAIN_FAILURE
PNFS_METADATA_ROOT_FAILURE
PNFS_INDEX_GENERATION_FAILURE
PNFS_INDEX_STALE
PNFS_METADATA_PAYLOAD_ORDER_FAILURE
```
