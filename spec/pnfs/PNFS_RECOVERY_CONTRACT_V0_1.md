# PNFS Recovery Contract v0.1

Status: `NORMATIVE CANDIDATE`

## 1. Recovery objective

PNFS recovery SHALL restore the latest verified logical state reachable from a valid checkpoint and a valid contiguous liminal tail.

The canonical recovery form is:

```text
RECOVERED_STATE = LAST_VALID_CHECKPOINT + VALID_CONTIGUOUS_LIMINAL_TAIL
```

## 2. Recovery scan order

Recovery MUST proceed in this order:

```text
LOCATE_REALIZATION
VERIFY_CONTAINER_OR_DEVICE_METADATA
LOCATE_CHECKPOINT_CANDIDATES
VERIFY_CHECKPOINT_CHAIN
SELECT_LATEST_VALID_CHECKPOINT
SCAN_LIMINAL_TAIL
VERIFY_TAU_FRAME_SEQUENCE
VERIFY_T36_WITNESSES
STOP_AT_FIRST_INVALID_DEPENDENCY
RECONSTRUCT_CANDIDATE_HEAD
PUBLISH_ONLY_AFTER_VALIDATION
```

## 3. Checkpoint chain

A checkpoint is admissible during recovery only when:

- its object identity reconstructs exactly;
- its FILE_ID matches the selected lineage;
- its parent binding is valid or it is the admitted genesis checkpoint;
- its generation ordering is valid;
- its tau boundary is compatible with its parent;
- its cumulative content commitment is internally valid.

## 4. Torn tail handling

A partial record, invalid record seal, malformed length, invalid tau frame, invalid T36 witness, parent mismatch, or missing dependency terminates replay at that boundary.

All tail records whose validity depends on the first invalid record SHALL be classified as `DISCARDED_TAIL` for that recovery attempt.

The last verified checkpoint remains the recovery floor.

## 5. Contiguity

Tail replay MUST preserve:

```text
checkpoint_parent -> segment_parent
previous_tau_end -> next_tau_start
frame_index ordering
witness binding
```

Any discontinuity SHALL yield `FAIL_CLOSED` for the affected tail.

## 6. Multi-realization recovery

When more than one realization exists, PNFS MAY compare realizations.

A realization selected as recovery authority MUST satisfy the active durability policy and all commitment checks.

If two verified realizations advertise the same checkpoint identity, their reconstructed logical content MUST agree.

If verified realizations expose divergent lineage heads, PNFS MUST surface a lineage conflict and require an explicit resolution policy before publication.

## 7. Recovery provenance

Every recovery attempt MUST emit a receipt containing at least:

```text
FILE_ID
source REALIZATION_ID
last verified CHECKPOINT_OBJECT_ID
admitted tail record count
discarded tail record count
reconstructed CONTENT_COMMITMENT
recovery verdict
first failure class when applicable
```

## 8. Publication rule

Recovery MAY reconstruct candidate state in memory before durable persistence.

The namespace-visible PNODE head SHALL change only after the reconstructed state has passed the required validation and persistence gates.

## 9. Required error classes

```text
PNFS_RECOVERY_NO_VALID_CHECKPOINT
PNFS_RECOVERY_TORN_RECORD
PNFS_RECOVERY_CHAIN_BREAK
PNFS_RECOVERY_TAU_DISCONTINUITY
PNFS_RECOVERY_WITNESS_FAILURE
PNFS_RECOVERY_REALIZATION_DIVERGENCE
```
