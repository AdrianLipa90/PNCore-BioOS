# PN Analog State Algebra (PASA) v0.1

Status: ARCHITECTURE CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: BioOS v0.4

## Purpose

PASA introduces the encoding-independent native state contract for BioOS. The system-level object is defined by relations, exact symbolic/rational structure, measured observables with provenance, phase geometry, lineage and identity. Binary layouts, IEEE-754 arrays, JSON, PNStore extents, DNCrypt envelopes and device-specific memory formats are realization adapters.

The architectural direction is:

```text
SYSTEM MEANING / RELATIONAL STATE
        -> canonical semantic normal form
        -> object identity / lineage
        -> realization adapter chosen by destination
        -> bytes / words / packets only at the physical boundary
```

## Fundamental invariants

```text
OBJECT_IDENTITY != PATH
OBJECT_IDENTITY != ADDRESS
OBJECT_IDENTITY != ENCODING
OBJECT_IDENTITY != REALIZATION_FORMAT
STATE_SEMANTICS  != IEEE754_LAYOUT
STATE_SEMANTICS  != PNSTORE_EXTENT
STATE_SEMANTICS  != DNCRYPT_ENVELOPE
```

Existing v0.3 formats remain valid reference realizations. They are demoted from native ontology to adapters; no v0.3 bytes are deleted by this contract.

## Native state object

A native analog-relational state is modeled as:

```text
PN_ANALOG_STATE = (
  identity_context,
  domain,
  observables,
  relations,
  geometry,
  temporal_state,
  lineage,
  evidence
)
```

The state may contain continuous observables, but its canonical identity is formed from a deterministic semantic normal form rather than an arbitrary floating-point byte image.

## Canonical value classes

### EXACT_INTEGER

```text
INTEGER(sign, magnitude)
```

Canonical zero has one representation.

### EXACT_RATIONAL

```text
RATIONAL(p,q)
q > 0
gcd(|p|,q) = 1
```

Examples:

```text
f0 = RATIONAL(783,100) Hz
harmonic = RATIONAL(p,q)
resonance = RATIO(m,n)
```

### SYMBOLIC_CONSTANT

Versioned symbolic constants remain symbolic in native semantics:

```text
PI
TAU = 2*PI
KAPPA = ln(2)/(24*PI)
```

A realization adapter may evaluate them numerically at a declared precision.

### PERIODIC_PHASE

A phase is a value on a declared periodic domain, not a raw float:

```text
PHASE(
  cycle = 2*PI | 4*PI | declared_period,
  coordinate,
  orientation,
  source_evidence
)
```

Exact phase coordinates may use rational turns. Measured phase coordinates use OBSERVED_SCALAR and preserve measurement evidence.

### OBSERVED_SCALAR

Measured values are represented semantically as:

```text
OBSERVED_SCALAR(
  quantity,
  unit,
  estimate,
  uncertainty,
  source_receipt,
  observation_generation
)
```

The estimate may be realized by float64, float32, fixed point, rational interval or another adapter. The semantic state binds quantity/unit/uncertainty/provenance and declared comparison policy.

### RELATION

A relation is an ordered semantic object:

```text
RELATION(type, source_id, target_id, parameters, evidence)
```

Commutative/symmetric relation types declare their own canonical endpoint ordering.

## Semantic normal form

Identity requires a deterministic normal form. PASA v0.1 canonicalization therefore requires:

```text
1. versioned schema and domain
2. normalized exact rationals
3. normalized symbolic expressions
4. normalized phase domain/orientation
5. deterministic map-key ordering
6. deterministic relation ordering
7. explicit units
8. explicit uncertainty/provenance for measured values
9. no implicit host precision
10. no path/address fields inside semantic identity
```

The normal form may be serialized for hashing, transport or persistence, but that serialization is an identity procedure rather than the native state model itself.

## Identity derivation

A native state identity is content-addressed over the semantic normal form:

```text
SEMANTIC_COMMITMENT = HASH256(
  DOMAIN("PN-ANALOG-STATE/v0.1") ||
  CANONICAL_SEMANTIC_NORMAL_FORM
)
```

The selected hash function and canonical serialization are versioned identity mechanisms. Changing an adapter without changing the semantic normal form must leave the semantic commitment unchanged.

## T36 realization

The native T36 phase state is:

```text
T36_PHASE_FIELD = {
  dimension = 36,
  phase_domain,
  phi[0..35],
  clock_binding,
  crystal_context,
  evidence
}
```

The current `36 x float64-le = 288 bytes` surface becomes one adapter:

```text
T36_PHASE_FIELD
 -> ADAPTER IEEE754_F64_LE_36
 -> 288 bytes
```

It is no longer the definition of the T36 state.

## T36 Identity realization

`T36_IDENTITY_CRYSTAL` remains the semantic identity state. The current exact 256-byte `T36I` record becomes:

```text
T36_IDENTITY_CRYSTAL
 -> ADAPTER T36I_BINARY_V0_1
 -> 256 bytes
```

`CRYSTAL_ID` remains semantic identity. Record layout is realization evidence.

## Persistence realization

PNStore remains the first exact persistence adapter:

```text
PN_ANALOG_STATE
 -> State Memory checkpoint
 -> selected PAUX functional codec
 -> optional DNCrypt adapter
 -> PNStore binary realization
 -> physical device adapter
```

PNStore byte geometry does not define State Memory semantics.

## Runtime rule

Native computation should consume semantic/relational state where an implementation exists. Binary decode/encode occurs at explicit adapter boundaries.

No existing binary adapter is removed until semantic-equivalence tests prove that the analog-native path reproduces the same admitted state and receipts.

## Promotion boundary

PASA v0.1 is an architecture candidate. Required gates include:

```text
semantic normal-form implementation
cross-adapter identity invariance tests
T36 float64 adapter roundtrip
T36I adapter roundtrip
State Memory analog-object lineage
PAUX functional codec registry
PNStore adapter equivalence
DNCrypt adapter equivalence
NEXUS/CQCL consumption without binary-format dependency
```
