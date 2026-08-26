# PNStore v0.1

Status: ARCHITECTURE CANDIDATE / LOGICAL CONTRACT

PNStore persists PNObject generations. v0.1 specifies logical durability and recovery behavior before binding to a physical block driver.

## Commit path

```text
candidate records
 -> generation cell
 -> COMMIT evidence
 -> durable boundary
 -> alternate HEAD advance
```

The design inherits the useful PNH5 invariant: committed generations are immutable, torn/uncommitted tails are not current state, and HEAD recovery must prefer the last fully verified COMMIT.

## Head

Two alternating HEAD slots are reserved at the logical contract level:

```text
HEAD_A = (generation_id, commit_id, digest)
HEAD_B = (generation_id, commit_id, digest)
```

Current is the newest fully verified admitted head.

## Exactly-once mutation

Every state-changing request carries a stable transition identity. Retrying an already committed transition returns the existing generation/evidence pair rather than allocating a duplicate generation.

## Block backend boundary

A physical backend must provide `READ_EXTENT`, `APPEND_EXTENT`, `DURABLE_BARRIER`, and `HEAD_SLOT_WRITE`. These are backend capabilities, not new PNV semantic opcodes.

## Recovery

```text
read HEAD_A + HEAD_B
 -> verify
 -> select newest valid committed generation
 -> scan bounded commit tail if required
 -> discard/unreference uncommitted tail
 -> expose current generation
```
