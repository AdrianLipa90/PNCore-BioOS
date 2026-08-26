# GREMLIN Round 16 — PAUX Harmonic Resonance Graph

Status: BOUNDED / READ_ONLY / CANDIDATE AUDIT

## Question

Can phase-locked low-order harmonic relations be represented as derived PNCore relation edges while preserving state, capability and effect authority?

## Compared relation graphs

Resonance graph spine:

```text
H_BAND_FITS(SOURCE)
 -> EXACT_RATIO(TRANSFORM)
 -> PHASE_INVARIANT(TRANSFORM)
 -> LOCK_QUALITY(CONDITION)
 -> RESONANCE_EDGE(DERIVED)
 -> RECEIPT(EVIDENCE)
```

PNCore relation spine:

```text
PNOBJECT_RELATIONS(SOURCE)
 -> RELATION_TYPE(TRANSFORM)
 -> RELATION_INVARIANT(TRANSFORM)
 -> RELATION_QUALITY(CONDITION)
 -> GRAPH_EDGE(DERIVED)
 -> RECEIPT(EVIDENCE)
```

Result:

```text
structurally_isomorphic = true
comparison_sha256 = b0b1a3becab1b884cfe56548b74197ad46c8b90541ed6c77fa83321a2cd04860
hypothesis_id = gremlin:hypothesis:sha256:f4477b2aa2ab7cc9f2294014b16dec60ccaf8620057fdfb39507abf234475ec1
```

Hypothesis statement:

> Phase-locked low-order harmonic relations can be represented as derived PNCore relation edges without changing state or capability authority.

Evaluation: `SUPPORTED_BY_DECLARED_TESTS`.

## Critic boundaries

- only Stage-2 `RATIONAL_FIT` records participate;
- lineage series must match;
- at least four synchronized windows are required;
- pair order is bounded to 16;
- phase-lock coherence must be at least 0.90;
- reverse relations are derived, not duplicated;
- graph edges remain `DERIVED_INDEX`;
- PNCAP remains capability authority;
- AUX remains effect authority;
- GREMLIN cannot promote the graph to canon or trigger recall.

The current live AUX fixture has no Stage-2 harmonic fit, so its Stage-3 graph is empty.
