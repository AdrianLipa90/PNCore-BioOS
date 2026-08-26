# PNMap v0.1 — Unified Relational Mapping Contract

Status: ARCHITECTURE CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false

## Purpose

PNMap defines one admitted mapping primitive for logical, storage, memory and device projections.
The mapping authority remains the relational object graph; architecture-specific structures are realizations/caches of an admitted mapping.

## Core contract

```text
(anchor, selector, context, authority)
 -> resolver
 -> unique target
 -> evidence
```

Roles:

- `ANCHOR` — mapping root or starting object;
- `SELECTOR` — requested relation/address selector;
- `CONTEXT` — exact current generation;
- `AUTHORITY` — PNCAP/capability or architecture grant;
- `RESOLVER` — deterministic traversal/translation;
- `TARGET` — resolved PNObject/PNResource;
- `EVIDENCE` — content-addressed resolution evidence.

## Projections

### PNFS

```text
PNObject anchor + relation selector + PNStore generation
 -> admitted PNFS relation traversal
 -> PNObject generation
```

### x86 memory

```text
CR3 mapping anchor + virtual selector + address-space generation
 -> admitted hardware page walk
 -> physical PNResource frame
```

The x86 page-table hierarchy is therefore a physical realization of admitted PNMap relations. It is not semantic authority.

## Invariant

```text
OBJECT_IDENTITY != ADDRESS != PATH
```

Address and path are projections. PNObject identity and generation remain authoritative.

## GREMLIN audit

Explicit relation graphs were compared with GREMLIN v0.5:

- PNFS resolution vs x86 page walk: structurally isomorphic = true;
- PNFS resolution vs classic process/VMA/page-fault/allocator model: structurally isomorphic = false;
- relational hypothesis evaluation: 2/2 PASS, `SUPPORTED_BY_DECLARED_TESTS`;
- critic: PASS.

This is candidate-selection evidence only.
