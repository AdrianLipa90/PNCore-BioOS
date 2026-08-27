# PAUX Functional Codec Registry v0.1

Status: ARCHITECTURE CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: BioOS v0.4

## Purpose

PAUX becomes the function-aware realization family for analog-native PN state. A codec is selected along two independent axes:

```text
PAUX[FUNCTION][REPRESENTATION]
```

`FUNCTION` preserves the semantic role of the state. `REPRESENTATION` declares how that state is materialized for a destination.

## Representation axis

```text
A      analog-native semantic state
EXACT  exact sampled realization
C      compressed lossless realization
R      reconstruction realization
```

`A` is the native semantic layer. `EXACT/C/R` are realization profiles.

## Initial function axis

```text
PHASE
TIME
IDENTITY
MEMORY
SEMANTIC
INTENT
AUDIO
VISION
SPATIAL
DEVICE_STATE
TRANSPORT
```

The registry is extensible through versioned function contracts. Function extensions leave the PNV opcode registry unchanged.

## Examples

```text
PAUX[PHASE][A]
  T36 phase field over declared periodic domains

PAUX[PHASE][EXACT]
  36 x float64-le sampled phase realization

PAUX[MEMORY][C]
  KEYSTATE / REF / RUN / DELTA_XOR64

PAUX[MEMORY][R]
  harmonic model + residual + reconstruction metrics

PAUX[IDENTITY][A]
  T36 crystal identity/context

PAUX[IDENTITY][EXACT]
  T36I 256-byte adapter

PAUX[SEMANTIC][A]
  Dictionary/NEXUS relational activation state

PAUX[INTENT][A]
  CQCL living candidate trajectory / observation state
```

## Selection rule

Codec selection is destination-driven:

```text
SEMANTIC_STATE
 + FUNCTION
 + DESTINATION
 + fidelity requirement
 + capability policy
 -> codec profile
```

Examples:

```text
live RAM/QHTRI         -> A
exact interchange      -> EXACT
lossless persistence   -> C
bounded reconstruction -> R
```

## Identity rule

All profiles bind the same source semantic identity when they realize the same source state.

```text
SOURCE_SEMANTIC_ID constant
REALIZATION_ID     profile-specific
```

For `R`, the reconstruction receives its own reconstruction identity and exact source reference.

## Native computation

State Memory, NEXUS, CQCL, GREMLIN and QHTRI progressively move to `A` semantic state APIs. Binary/quantized adapters serve concrete implementation and I/O boundaries.

## Existing v0.3 migration

The current profiles map as:

```text
old PAUX-EXACT -> PAUX[*][EXACT]
old PAUX-C     -> PAUX[*][C]
old PAUX-R     -> PAUX[*][R]
```

Existing evidence remains retained. v0.4 adds the previously implicit `A` layer and explicit function classification.

## First promotion gates

```text
PHASE[A] <-> PHASE[EXACT] semantic identity/sample invariance evidence
IDENTITY[A] <-> IDENTITY[EXACT] T36I equivalence
MEMORY[A] -> MEMORY[C] -> MEMORY[A] exact recovery
MEMORY[A] -> MEMORY[R] reconstruction evidence
SEMANTIC[A] NEXUS activation through semantic-state API
INTENT[A] CQCL through living-state API
```
