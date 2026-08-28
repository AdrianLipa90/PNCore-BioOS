# PNFS Write and Checkpoint Contract v0.1

Status: `NORMATIVE CANDIDATE`

## 1. Logical write model

PNFS SHALL model authoritative file evolution as:

```text
S_n -> Lambda_n(tau) -> S_{n+1}
```

where:

- `S_n` is the last verified State Memory checkpoint;
- `Lambda_n(tau)` is the admitted liminal segment;
- `S_{n+1}` is the next crystallized checkpoint.

The canonical logical history is append-oriented.

## 2. Write transaction phases

A logical write transaction MUST execute the following phases in order:

```text
BEGIN_LIMINAL_SEGMENT
ADMIT_TAU_FRAME*
VERIFY_T36_WITNESS*
SEAL_LIMINAL_SEGMENT
CRYSTALLIZE_CHECKPOINT
PERSIST_REALIZATION
PUBLISH_HEAD
```

`PUBLISH_HEAD` is permitted only after all required durability gates for the selected policy have passed.

## 3. Tau-frame admission

Each admitted content frame MUST be produced by the active PNCS scalar-τ codec contract.

Each frame MUST expose:

```text
frame_commitment
witness_commitment
tau_start
tau_end
payload_length
```

Tau intervals MUST be strictly ordered within a single lineage segment.

Overlapping or reversed intervals MUST yield `FAIL_CLOSED`.

## 4. Whole-lane T36 witness

Each frame or configured frame group MUST carry a whole-lane T36 witness according to the active PNCS contract.

The witness commitment MUST be bound into the liminal segment before crystallization.

## 5. Liminal segment seal

The sealed liminal segment MUST bind at least:

```text
FILE_ID
parent CHECKPOINT_OBJECT_ID
tau_start
tau_end
aggregate frame commitment
aggregate T36 witness commitment
active semantic layers
evidence metadata
```

A segment with unresolved commitment mismatch MUST remain uncrystallized.

## 6. Checkpoint crystallization

State Memory SHALL create the next checkpoint only from a verified sealed liminal segment.

The resulting checkpoint MUST bind:

```text
FILE_ID
parent checkpoint
generation
tau_end
cumulative content commitment
liminal segment commitment
```

Generation MUST increase monotonically on a single linear lineage head.

## 7. Physical persistence

A physical realization MUST be written through the active PNFS placement policy.

The persistence sequence for a durable local realization SHOULD be:

```text
write records
flush userspace buffers
fsync file
fsync containing directory when rename/replace is used
publish realization metadata
```

Atomic replacement MUST use a same-filesystem temporary target followed by rename/replace semantics.

## 8. Head publication

`PNODE.current_checkpoint` MUST be advanced only after the selected durability class has been satisfied.

If physical persistence fails after checkpoint construction and before head publication, the previous published checkpoint remains authoritative.

## 9. Concurrency

A single FILE_ID lineage head MUST have one serialization authority for checkpoint publication.

Concurrent writers MAY build candidate liminal segments in parallel, but conflicting parent checkpoint identities MUST be resolved before publication.

## 10. Required error classes

```text
PNFS_TAU_ORDER_VIOLATION
PNFS_T36_WITNESS_FAILURE
PNFS_LIMINAL_SEAL_FAILURE
PNFS_PARENT_CHECKPOINT_CONFLICT
PNFS_DURABILITY_GATE_FAILURE
PNFS_HEAD_PUBLICATION_CONFLICT
```
