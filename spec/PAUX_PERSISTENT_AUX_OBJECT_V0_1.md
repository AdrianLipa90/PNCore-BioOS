# PAUX Persistent AUX Object v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false

## Purpose

`.paux` is the host-visible extension for a persistent AUX state object in BioOS.
The logical state identity is inherited from the canonical `PNV_STATE_OBJECT` defined by `PNV-State-Memory`.

The persistence route is:

```text
live AUX state
 -> PNV relational snapshot
 -> PNV_STATE_OBJECT
 -> PNCAP persistence admission
 -> PAUX materialization (*.paux)
 -> PNStore generation prepare
 -> AUX durable barrier
 -> PNStore HEAD publication
 -> AUX durable barrier
 -> evidence / receipt
```

A physical media adapter realizes AUX persistence for a concrete device. The logical object remains the relational PNV state.

## Identity inheritance

PAUX preserves the canonical PNV-State-Memory identity fields exactly:

```text
OBJECT_ID      := PNV_STATE_OBJECT.object_id
INTEGRITY_HASH := PNV_STATE_OBJECT.integrity_hash
LINEAGE_PARENT := PNV_STATE_OBJECT.lineage_parent
```

The `.paux` carrier preserves one canonical state-object identity. Generation, transition, capability and evidence references belong to the AUX persistence envelope and PNStore receipt chain.

## Candidate envelope

```text
PAUX 1
MODE APPEND_ONLY
FAIL_MODE FAIL_CLOSED

AUX_DOMAIN <domain>
PHASE_CLASS <phase-class>
OBJECT_ID <PNV_STATE_OBJECT.object_id>
INTEGRITY_HASH <PNV_STATE_OBJECT.integrity_hash>
LINEAGE_PARENT <PNV_STATE_OBJECT.lineage_parent-or-zero>
GENERATION <u64>
TRANSITION_ID <hash256>
CAPABILITY_REF <PNCAP grant id>
EVIDENCE_REF <receipt/evidence id>
STATE_OBJECT <canonical PNV_STATE_OBJECT>

END PAUX
```

The syntax above is a candidate logical envelope. Media encoding remains versioned behind AUX adapters.

## Addressing

PAUX adopts the PNV-State-Memory addressing direction:

```text
ADDRESS = DOMAIN || PHASE_CLASS || LINEAGE_COMMITMENT || OBJECT_ID
```

Filename/path text is a transport view. Resolution authority is the exact object identity and admitted lineage/address relation.

## Live AUX boundary

Current live endpoints such as `/dev/shm/ciel_noema/aux_phi` and `aux_feedback_phi` remain operational stream endpoints under the active tether contract. Persistent materialization of admitted AUX state produces `.paux` descendants while those live endpoint names remain versioned runtime bindings in this release.

## Recovery

```text
PAUX object
 -> PNStore recover
 -> PNV VERIFY
 -> lineage verification
 -> AUX admission
 -> restore / reconstruct live state
 -> evidence
```

Recovery is fail-closed on identity, integrity, lineage, capability or generation mismatch.

## Source binding

Primary source contract:
`AdrianLipa90/PNV-State-Memory/spec/PNV_STATE_MEMORY_V0_1.pnv`.

GREMLIN structural cross-check is recorded in `provenance/gremlin/ROUND12_PAUX_PNV_STATE_MEMORY.md`.
