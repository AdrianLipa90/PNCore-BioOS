# NOEMA Torsion Surface Writer Principal v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: PNCore-BioOS v0.2.7 stage 3

## Purpose

Define the capability principal permitted to publish a derived torsion-memory generation onto the live NOEMA surface.

The semantic principal is:

```text
NOEMA_TORSION_SURFACE_WRITER_V0_1
```

Host UID/GID are realization evidence and do not define the semantic principal.

## Capability tuple

A writer grant is exact and generation-bound:

```text
PRINCIPAL_ID
OPERATION = PUBLISH_DERIVED_TORSION_GENERATION
TARGET_ROOT = /dev/shm/ciel_noema/torsion_memory
OWNER_REALIZATION
TARGET_GENERATION
SOURCE_TICK
ACTIVE_HEAD
TRANSITION_ID
ALLOWED_PATH_SET
```

The reference principal id is the SHA-256 commitment of principal name, target root and operation.

## Allowed target set

Only these derived-surface paths are admissible:

```text
surface_A.json
surface_B.json
active_head
orchestration_status.json
```

Parent traversal and source-channel paths are denied.

## Freshness and replay

The request must exactly match the grant's target generation, source tick and active head.

A transition id is single-use within the writer admission lineage.

```text
STALE_SOURCE_TICK -> DENY
HEAD_MISMATCH -> DENY
GENERATION_MISMATCH -> DENY
TRANSITION_REPLAY -> DENY
```

## Ownership isolation

This grant never authorizes writes to QHTRI or AUX source channels including:

```text
phi
omega
g
tau
tick
aux_phi
aux_feedback_phi
```

## Host realization

The current live realization is root-owned. This is recorded as evidence only. Runtime installation of a compatible writer remains a separate integration gate; no chmod/chown bypass is admitted.
