# PNFS Object Identity and Addressing Contract v0.1

Status: `NORMATIVE CANDIDATE`

## 1. Identity domains

PNFS SHALL maintain four independent identity domains:

```text
FILE_ID
CONTENT_COMMITMENT
CHECKPOINT_OBJECT_ID
REALIZATION_ID
```

Their equality MUST NOT be used as an invariant.

### FILE_ID

`FILE_ID` identifies the persistent logical file lineage.

It MUST remain stable across:

- content edits;
- checkpoint creation;
- namespace rename;
- movement between directories;
- movement between physical devices;
- creation or removal of additional realizations.

### CONTENT_COMMITMENT

`CONTENT_COMMITMENT` identifies the logical content state admitted for a given generation or checkpoint.

A logical content change MUST produce a new content commitment.

### CHECKPOINT_OBJECT_ID

`CHECKPOINT_OBJECT_ID` identifies a crystallized State Memory state.

Each checkpoint MUST bind at least:

```text
FILE_ID
parent checkpoint
content commitment
tau boundary
liminal-segment commitment
```

### REALIZATION_ID

`REALIZATION_ID` identifies one physical/materialized representation of a logical state.

Two realizations MAY carry the same `FILE_ID`, `CONTENT_COMMITMENT`, and `CHECKPOINT_OBJECT_ID` while having distinct realization identities.

## 2. PNODE

The canonical PNFS object descriptor is `PNODE`.

Minimum logical schema:

```text
PNODE {
  file_id
  object_type
  current_checkpoint
  current_tau
  semantic_class
  relations[]
  realization_set[]
  policy
}
```

`PNODE.current_checkpoint` MUST reference the latest checkpoint admitted by State Memory for the selected lineage head.

`PNODE.realization_set[]` MUST contain references to physical realizations and their validation status.

## 3. Semantic address

The canonical PNFS semantic address is:

```text
(FILE_ID, tau, relation)
```

where:

- `FILE_ID` selects the logical lineage;
- `tau` selects a content coordinate or interval;
- `relation` selects a relational projection or semantic binding.

A byte offset MAY be exposed by a compatibility adapter as a realization coordinate.

## 4. Namespace path

A path SHALL be represented as a mutable namespace binding:

```text
PATH -> FILE_ID
```

Rename and directory movement MUST preserve `FILE_ID`.

Two paths MAY reference the same FILE_ID where the namespace policy permits aliases.

## 5. Relations

PNFS relations are typed edges attached to PNODEs.

Initial relation vocabulary:

```text
LINKS_TO
DERIVED_FROM
CHECKPOINT_OF
MIRROR_OF
ENCODES
DEPENDS_ON
SUPERSEDES
BELONGS_TO
```

Unknown relation types MUST be rejected until explicitly registered by the active PNFS relation registry.

## 6. Identity verification

On open, checkpoint promotion, snapshot creation, realization import, or recovery, PNFS MUST verify all identity links required by the selected operation.

Any mismatch between declared and reconstructed commitments SHALL yield `FAIL_CLOSED`.

## 7. Required error classes

Implementations MUST distinguish at least:

```text
PNFS_IDENTITY_MISMATCH
PNFS_UNKNOWN_RELATION
PNFS_NAMESPACE_CONFLICT
PNFS_CHECKPOINT_BINDING_MISMATCH
PNFS_REALIZATION_BINDING_MISMATCH
```
