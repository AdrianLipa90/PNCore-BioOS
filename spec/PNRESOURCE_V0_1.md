# PNResource v0.1 — Physical Resource Binding Candidate

Status: `GREMLIN-SUPPORTED ARCHITECTURE CANDIDATE / CHYBA / NO CANON AUTHORITY`

## Purpose

PNResource projects physical machine resources into the same PNObject generation-transition model used by BioOS state and storage.

A physical resource is admitted through:

```text
physical identity + topology generation + authority
-> bind request
-> coupling
-> admission
-> resource transition
-> resource generation state
-> evidence
```

Representative resource kinds for the first backend are:

```text
CPU_THREAD
RAM_EXTENT
ROM_EXTENT
BLOCK_DEVICE
TIMER
SERIAL_ENDPOINT
FRAMEBUFFER
```

The resource generation binds exact physical/backend identity, topology/environment generation, PNObject identity, phase36 realization/binding when available, PNCAP authority, parent generation and deterministic transition/evidence identity.

## Capability interaction

PNResource operations are requested through PNCAP scopes such as `OBSERVE_RESOURCE`, `BIND_RESOURCE`, `READ_EXTENT`, `APPEND_EXTENT`, `DURABLE_BARRIER`, `MAP_MEMORY`, and `EXECUTE_ON_RESOURCE`.

These are capability operation kinds. Native program semantics continue to use the existing PNCS operator registry.

## First boot use

The minimal x86_64 bootstrap supplies a small initial physical-resource set to PNCore. PNCore then admits those resources as PNObject generations before Genesis receives the initial system state.

## GREMLIN evidence

GREMLIN v0.5 relational audit round 4 compared the common PN transition spine with two explicit physical-resource graphs. The unified PNResource graph was structurally isomorphic to the spine; the layered bus/driver/device-namespace candidate was not. The generated structural hypothesis was `SUPPORTED_BY_DECLARED_TESTS`; critic verdict `PASS`.

This evidence grants candidate status only.
