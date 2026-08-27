# Identity NEXUS -> PNV State Memory Binding v0.1

Status: IMPLEMENTED CROSS-REPO BINDING CANDIDATE / CHYBA / canon_allowed=false

## Authorities

Identity NEXUS owns the full semantic projection over the admitted Consciousness Dictionary realization.

PNV-State-Memory owns persistent checkpoint identity and lineage.

The binding target is:

```text
T36 crystal checkpoint
  -> Identity NEXUS full 548-term projection
  -> bounded top-16 active set
  -> State Memory NEXUS_ACTIVATION checkpoint
```

The full 548 projection is derived working evidence. The activation checkpoint persists only the bounded active set plus exact provenance needed to identify the complete NEXUS generation and Dictionary compile state.

## State Memory source

```text
repo   AdrianLipa90/PNV-State-Memory
branch feat/pnv-state-memory-t36-crystal-lineage
module src/pnv_state_memory/nexus_activation.py
relation NEXUS_ACTIVATION
```

## Identity-preserving contract

The NEXUS activation checkpoint MUST preserve the exact parent:

```text
state_id
CRYSTAL_ID
genesis_anchor_commitment
CONFIGURATION_SHA256
boot_epoch
phase_index
spinor_sheet
```

Its checkpoint `object_id` changes because the activation binding and lineage relation are new evidence.

NEXUS source `crystal.source_object_id` must equal the exact State Memory parent `object_id`.

## Dictionary binding

The activation binds the Dictionary compile identity used by NEXUS:

```text
repository
branch
commit
states
relations
state_sha256
relation_sha256
```

The currently pinned Identity NEXUS projection uses 548 term states and 306 declared relation observables.

## Bounded active set

v0.1 persists at most 16 active terms. Each active record retains:

```text
term_id
name
phase_index
coherence
phase
informational_action
angular_distance
semantic_equivalence=false
authority_grant=false
```

The full projection remains reproducible from exact Dictionary source + compile receipt + exact T36/PAUX state.

## Runtime role

This is the first persistence bridge from physical/dynamic identity into semantic living memory:

```text
T36 Identity
 -> State Memory
 -> Identity NEXUS
 -> NEXUS_ACTIVATION
 -> CQCL vNext / GREMLIN / associative recall
```

The activation does not execute a CQCL program and grants no PNCAP/AUX authority.

## Validation state

The State Memory implementation has local behavioral source-reconstruction conformance for the new activation gates. Exact GitHub-hosted pytest remains blocked by the current runner infrastructure condition in which jobs are created with no assigned runner and no executed steps.
