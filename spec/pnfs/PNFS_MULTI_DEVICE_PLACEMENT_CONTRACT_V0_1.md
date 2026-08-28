# PNFS Multi-Device Placement Contract v0.1

Status: `NORMATIVE CANDIDATE`

## 1. Placement model

PNFS SHALL treat physical storage as a set of realizations governed by durability and performance policy.

The initial Dell G5 deployment profile is:

```text
HOT   -> NVMe
WARM  -> internal SATA HDD
COLD  -> external USB storage
```

The namespace SHALL remain device-independent.

## 2. Device role metadata

Each registered storage target MUST expose:

```text
device_id
realization_class
transport
mount_or_device_binding
health_state
writable_state
durability_capabilities
capacity_state
```

## 3. Placement classes

Initial placement classes:

### HOT

Optimized for active liminal state, current indexes, recent checkpoints, write absorption, and frequently accessed realizations.

### WARM

Optimized for durable canonical payload extents, checkpoint generations, and lower-cost retained state.

### COLD

Optimized for sealed mirrors, archival generations, and disaster-recovery copies.

## 4. Durability policies

PNFS MUST support explicit durability policies.

Initial policies:

```text
D0_VOLATILE_CANDIDATE
D1_LOCAL_SINGLE
D2_LOCAL_DUAL
D3_LOCAL_PLUS_OFFLINE_MIRROR
```

A policy MUST define which realization acknowledgements are required before `PUBLISH_HEAD`.

Example:

```text
D1_LOCAL_SINGLE: one verified local persistent realization
D2_LOCAL_DUAL: two verified persistent realizations on distinct registered devices
D3_LOCAL_PLUS_OFFLINE_MIRROR: D2 plus one verified removable/offline-capable mirror
```

## 5. Placement and identity

Moving or copying a logical state between devices MUST preserve:

```text
FILE_ID
CONTENT_COMMITMENT
CHECKPOINT_OBJECT_ID
```

Each physical copy MUST receive its own `REALIZATION_ID`.

## 6. Promotion and eviction

Placement migration SHALL be represented as realization creation followed by verification and policy-governed retirement of the previous realization.

An HOT eviction MUST preserve the minimum durability class required by the PNODE policy.

## 7. Device loss

A missing removable device SHALL mark its realizations `UNAVAILABLE`.

Other verified realizations remain eligible according to policy.

A device reappearance MUST trigger realization validation before the copy returns to `VERIFIED` state.

## 8. Health and write admission

A device with a failed health gate, read-only state, unresolved filesystem error, or insufficient capacity MUST be excluded from new authoritative realization placement.

## 9. Cross-device atomicity

Cross-device publication MUST use staged realization states:

```text
CANDIDATE
WRITTEN
VERIFIED
PUBLISHED
RETIRED
```

A multi-device durability policy is satisfied only when the required number and class of realizations have reached `VERIFIED`.

## 10. Required error classes

```text
PNFS_DEVICE_UNAVAILABLE
PNFS_DEVICE_HEALTH_FAILURE
PNFS_CAPACITY_FAILURE
PNFS_PLACEMENT_POLICY_UNSATISFIED
PNFS_REALIZATION_COPY_FAILURE
PNFS_REALIZATION_VERIFY_FAILURE
```
