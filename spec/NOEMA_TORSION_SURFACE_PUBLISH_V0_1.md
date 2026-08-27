# NOEMA Torsion Surface Publish Contract v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: PNCore-BioOS v0.2.7 stage 2

## Purpose

Define the only admitted route for publishing a derived torsion-memory generation onto the root-owned live NOEMA surface.

## Writer principal

Live publication requires a versioned `SURFACE_WRITER_PRINCIPAL` admitted by PNCAP for the exact target generation.

Absence of an admitted writer is a normal fail-closed state:

```text
PUBLISH_BLOCKED_OWNER_GATE
```

Changing directory ownership or permissions ad hoc is outside this contract.

## Atomic generation publication

For active head `A`, prepare `B`:

```text
READ ACTIVE_HEAD
PREPARE INACTIVE_GENERATION
VERIFY COMPLETE_GENERATION
VERIFY SOURCE_TICK
VERIFY PNCAP WRITER GRANT
PUBLISH INACTIVE_GENERATION
FLIP ACTIVE_HEAD
EMIT EVIDENCE
```

The symmetric route applies from `B` to `A`.

Readers consume only the generation named by `ACTIVE_HEAD`.

## Source ownership isolation

The writer grant applies only to the derived torsion-memory surface. It never grants writes to:

```text
phi
omega
g
tau
tick
aux_phi
aux_feedback_phi
```

## Effect boundary

Publishing derived working memory is not an AUX physical effect.

Any later orchestration action still requires a separate PNCAP admission and AUX transition.
