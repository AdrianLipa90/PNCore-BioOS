# NOEMA Memory Orchestration Binding v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: PNCore-BioOS v0.2.7

## Purpose

The orchestration binding converts a torsion-consistent memory basin into a recall candidate and preserves the exact authority chain before any AUX effect.

```text
TORSION_MEMORY_SURFACE
 -> locked component / basin evidence
 -> RECALL_CANDIDATE
 -> MEMORY_EPOCH_MATCH
 -> LINEAGE_MATCH
 -> PNCAP
 -> PN Harmonic Scheduler
 -> AUX
 -> evidence
```

## Recall candidate

A candidate contains only evidence/ranking fields:

```text
CANDIDATE_ID
MEMORY_EPOCH
NODE_SET
EDGE_SET_REF
TORSION_COHERENCE
TORSION_ENERGY
RELATION_WEIGHT
SOURCE_OBJECT_IDS
LINEAGE_REF
DERIVATION_REFS
```

It contains no grant and no effect authority.

Reference engineering thresholds for the first conformance fixture are versioned as:

```text
MIN_TORSION_COHERENCE 0.95
MAX_TORSION_ENERGY 0.05
MIN_EDGE_COUNT 1
```

They are recall-ranking gates, never security authority.

## Deterministic ranking

Passing candidates are ordered by

```text
score = TORSION_COHERENCE*RELATION_WEIGHT - TORSION_ENERGY
```

then stable `CANDIDATE_ID` for exact tie breaking.

## Admission chain

A ranked candidate may proceed only when all gates pass in order:

```text
candidate exists
MEMORY_EPOCH == current epoch
LINEAGE_REF exact match
PNCAP generation-bound capability match
scheduler admission
AUX availability
```

Outcomes:

```text
no candidate -> QUIET_NO_CANDIDATE
stale epoch -> STALE_MEMORY_EPOCH / RESELECT
lineage mismatch -> LINEAGE_MISMATCH
PNCAP deny -> PNCAP_DENY
scheduler quiet -> SCHEDULER_QUIET
AUX unavailable -> AUX_UNAVAILABLE
all gates -> AUX_ADMITTED
```

Only `AUX_ADMITTED` may produce an `AUX_REQUEST` effect record.

## Evidence

Every orchestration decision records at minimum:

```text
CANDIDATE_ID
MEMORY_EPOCH
CURRENT_EPOCH
SOURCE_DERIVATION_REFS
PNCAP_RESULT
SCHEDULER_RESULT
AUX_RESULT
TRANSITION_ID
EVIDENCE_REF
```
