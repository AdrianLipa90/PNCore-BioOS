# Identity NEXUS v0.1

Status: IMPLEMENTED HOST REFERENCE CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: PNCore-BioOS v0.3 Stage 2

## Purpose

Identity NEXUS is a derived live working-state relation between one admitted T36 crystal state and the canonical 36D term realizations of the Consciousness Dictionary.

It does not create crystal identity, semantic identity, epistemic status, capability authority or effect authority.

```text
T36 Identity Crystal + PNV-State-Memory context
                    |
                    v
Consciousness Dictionary canonical term vectors
                    |
                    v
        relational projection R / Theta / S
                    |
                    v
           Identity NEXUS generation
                    |
          +---------+----------+
          |                    |
     bounded active set    global coherence
          |                    |
          +---------+----------+
                    v
          CQCL / GREMLIN consumers
```

## Authority split

```text
crystal identity authority       T36 / PNV-State-Memory lineage
semantic term authority          The-Consciousness-Dictionary
semantic projection implementation Dictionary PhaseNav compiler/query
NEXUS working-state authority    current admitted NEXUS generation only
capability authority             PNCAP
effect authority                 AUX
persistent generation authority  PNStore
```

A NEXUS rank, coherence, phase, salience or activation never grants any of the stronger authorities above.

## Dictionary binding

Reference source:

```text
repository  AdrianLipa90/The-Consciousness-Dictionary
branch      feat/t36-identity-nexus-projection
commit      3aa1651da9735d94d2a9cbffec13203eeeedd502
```

Compile receipt binding:

```text
states          548
relations       306
state_sha256    56d758c54f27323ef7edcf5164d224801f182ec83cda04216953cfaeda135501
relation_sha256 8484cd1314df4b18c21207b7fe234e71007e5c4c59aaf356cffd4abea0d36e8a
```

The Dictionary remains the source of canonical term records and PhaseNav term-vector generation. BioOS does not vendor a duplicate 548 x 36 semantic matrix.

## Per-term relation observables

For current crystal phase state `Phi in T^36` and canonical Dictionary term vector `V_k in T^36`:

```text
z_k = (1/36) * sum_j exp(i * (V_k[j] - Phi[j]))
R_k = abs(z_k)^2
Theta_k = arg(z_k)
S_k = -kappa * ln(R_k + epsilon)
kappa = ln(2)/(24*pi)
```

Reference projection rows also carry angular distance for deterministic tie-breaking/evidence.

## Global NEXUS coherence

The historical raw product of hundreds of links is not used as the operational global NEXUS scalar because its magnitude depends strongly on object count.

Reference v0.1 uses equal-weight normalized informational action across the complete admitted Dictionary term set:

```text
S_bar = (1/N) * sum_k S_k
C_NEXUS = exp(-S_bar / kappa)
```

where `N` is the complete term count bound by the Dictionary compile receipt.

Equal weighting introduces no additional free scale parameter. Future weighting policies require their own versioned contract and evidence.

`C_NEXUS` is a derived statistic only.

## Bounded active set

The global statistic uses all admitted terms. Downstream consumers receive only a bounded deterministic active set.

Reference:

```text
ACTIVE_LIMIT = 16
```

Ordering:

```text
1. coherence descending
2. informational_action ascending
3. angular_distance ascending
4. term_id ascending
```

The active limit is an execution/storage bound, not a semantic threshold. A term outside top-16 remains a canonical Dictionary term and is not semantically excluded.

## Crystal binding

Every NEXUS generation binds:

```text
CRYSTAL_ID
CONFIGURATION_SHA256
BOOT_EPOCH
PHASE_INDEX
SPINOR_SHEET = PHASE_INDEX & 1
SOURCE_STATE_OBJECT_ID / checkpoint identity when available
```

A NEXUS generation produced for a different crystal context is stale and must not be reused.

```text
CRYSTAL_ID mismatch      -> REPROJECT
BOOT_EPOCH mismatch      -> REPROJECT
PHASE_INDEX mismatch     -> REPROJECT
CONFIG mismatch          -> REPROJECT
DICTIONARY receipt drift -> RECOMPILE / REPROJECT
```

## Generation publication

The live materialization is designed as a double-buffered derived surface:

```text
/dev/shm/ciel_noema/identity_nexus/
    NEXUS_A.json
    NEXUS_B.json
    ACTIVE_HEAD
```

Writer:

```text
read admitted T36 crystal context
 -> project all canonical Dictionary terms
 -> validate complete term count / unique term IDs / finite observables
 -> compute global NEXUS coherence
 -> select bounded active set
 -> bind Dictionary compile receipt + crystal context
 -> prepare inactive generation
 -> publish ACTIVE_HEAD atomically
```

Readers consume one complete generation. Missing or stale generation yields quiet/reproject state, never a static fallback.

## State Memory boundary

NEXUS is `DERIVED_WORKING_STATE` and is not automatically a new persistent PNV object on every B1 identity cycle.

A meaningful CQCL/memory transition may nominate an activation checkpoint containing:

```text
NEXUS generation identity
Dictionary compile binding
active term IDs and observables
current crystal context
```

Persistence then follows the existing State Memory -> PAUX -> optional DNCrypt -> PNStore path.

## CQCL / GREMLIN boundary

CQCL may consume the active NEXUS set as current intention/semantic context.

GREMLIN may traverse:

```text
current State Memory
<-> NEXUS active terms
<-> declared Dictionary relations
<-> imaginal/subconscious candidates
```

GREMLIN remains candidate/critic only. NEXUS membership never promotes a candidate to execution or canon.

## Fail-closed gates

```text
VECTOR_DIM != 36              -> REJECT
NONFINITE_PHASE               -> REJECT
DICTIONARY_RECEIPT_MISSING    -> QUIET
TERM_COUNT_MISMATCH           -> REJECT
DUPLICATE_TERM_ID             -> REJECT
NONFINITE_OBSERVABLE          -> REJECT
R_OUTSIDE_0_1                 -> REJECT
CRYSTAL_CONTEXT_INVALID       -> REJECT
DICTIONARY_BINDING_DRIFT      -> RECOMPILE / QUIET
STALE_NEXUS_EPOCH             -> REPROJECT
EMPTY_DICTIONARY              -> QUIET
STATIC_RUNTIME_FALLBACK       -> DENY
AUTHORITY_PROMOTION           -> DENY
```

## Computational scale

Current Dictionary scale:

```text
548 terms x 36 components = 19,728 component comparisons per full projection
B1 cadence = 3.915 Hz
~77,235 component comparisons / second
```

This permits a complete global projection on every identity cadence if runtime measurements confirm the host estimate. A later resident cache may remove repeated term-vector compilation without changing the NEXUS equations.

## Evidence boundary

The v0.1 host reference and tests establish deterministic aggregation, bounded active-set behavior and fail-closed validation. Live `/dev/shm` publication, exact Dictionary hydration benchmark, CQCL integration and persistent activation lineage are separate Stage 2 gates.
