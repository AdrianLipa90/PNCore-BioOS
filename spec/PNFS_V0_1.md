# PNFS v0.1 — Relational Object View

Status: ARCHITECTURE CANDIDATE

PNFS is a view/resolution layer over PNObject + PNStore.

## Fundamental rule

```text
OBJECT IDENTITY != PATH
```

A path is a deterministic projection of named relations.

Example:

```text
root --NAME:system--> object_A --NAME:genesis--> object_B
```

may be rendered as:

```text
/system/genesis
```

but `object_B` remains identified by its PNObject identity and generation.

## Core relations

Initial relation vocabulary:

```text
CONTAINS
NAMES
DEPENDS_ON
DERIVES_FROM
REALIZES
BINDS
EXPOSES
PARENTS
EVIDENCES
```

This is relation vocabulary, not CPU/PNV opcode vocabulary.

## Resolve

```text
(start_object, relation_query, current_generation)
 -> admitted relation traversal
 -> unique object generation
```

Ambiguous resolution returns an explicit unresolved set. It is never resolved by wall-clock recency or arbitrary ordering.

## Files

A conventional file is represented as a DATA PNObject plus one or more VIEW relations. File-like byte access is therefore compatibility behavior over PNObject payload extents.
