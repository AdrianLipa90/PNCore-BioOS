# GREMLIN Round 15 — PAUX Harmonic Estimator

Status: BOUNDED / READ_ONLY / CANDIDATE AUDIT

## Question

Can bounded rational harmonic estimation preserve the already admitted Stage-1 derivation spine from an AUX phase source to a derived H-band orbital-memory index?

## Compared relation graphs

Estimator graph:

```text
AUX_WINDOW(SOURCE)
 -> VERIFY
 -> RATIONAL_LATTICE(CANDIDATE)
 -> HARMONIC_FIT(TRANSFORM)
 -> QUALITY_GATE(CONDITION)
 -> H_BAND(DERIVED)
```

Orbital-memory graph:

```text
PAUX_STATE(SOURCE)
 -> PHASE_SOURCE(VERIFY)
 -> HARMONIC_RATIO(CANDIDATE)
 -> ORBITAL_GEOMETRY(TRANSFORM)
 -> ADMISSION(CONDITION)
 -> HARMONIC_INDEX(DERIVED)
```

GREMLIN relational-isomorphism result:

```text
structurally_isomorphic = true
comparison_sha256 = 6b3e808db99e39e944ac6eaf3fb10917daced3990275d4e4ed5dfcbb03f7e166
hypothesis_id = gremlin:hypothesis:sha256:55a6ccb3482e46027f2ed78c9de1eb36aa46ecab87605c6a83df81c680ff9b67
```

Hypothesis statement:

> Bounded rational harmonic estimation preserves the admitted PAUX harmonic-orbital derivation spine from phase source to H-band index.

Evaluation: `SUPPORTED_BY_DECLARED_TESTS`.

## Critic boundaries

The candidate is retained only with all of the following boundaries:

- a harmonic fit remains `DERIVED_INDEX`;
- `RATIONAL_FIT` records model fit evidence, score and margin;
- static or ambiguous windows produce `FREQUENCY_UNRESOLVED`;
- scheduler `B0..B7` remains distinct from memory `H0..H35`;
- PNV state identity is unchanged;
- PNCAP remains capability authority;
- AUX remains effect authority;
- no new PNV opcode is introduced;
- GREMLIN has no promotion or execution authority.

The live 128-frame AUX observation was static and therefore provides a negative control rather than a harmonic-frequency claim.
