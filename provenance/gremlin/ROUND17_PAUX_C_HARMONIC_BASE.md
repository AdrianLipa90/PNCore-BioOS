# GREMLIN Round 17 — PAUX-C Harmonic Base Selection

Status: BOUNDED / READ_ONLY / CANDIDATE AUDIT

## Question

Can harmonic candidate base discovery improve PAUX-C delta selection while preserving the exact lossless recovery spine?

Baseline spine:

```text
PAUX_FRAME(SOURCE)
 -> PREVIOUS_BASE(CANDIDATE)
 -> DELTA_XOR64(TRANSFORM)
 -> EXACT_DECODE(TRANSFORM)
 -> OBJECT_INTEGRITY_VERIFY(CONDITION)
 -> RECEIPT(EVIDENCE)
```

Harmonic-base spine:

```text
PAUX_FRAME(SOURCE)
 -> HARMONIC_BASE(CANDIDATE)
 -> DELTA_XOR64(TRANSFORM)
 -> EXACT_DECODE(TRANSFORM)
 -> OBJECT_INTEGRITY_VERIFY(CONDITION)
 -> RECEIPT(EVIDENCE)
```

Result:

```text
structurally_isomorphic = true
comparison_sha256 = 5fcb970d7ff29be9bbf9354106385c4964d44ab061bb26bbab1a0f8231cc2779
hypothesis_id = gremlin:hypothesis:sha256:232fe27b17713119f2aea91c6c52e0f4d8fe77135ccc8edce95afd29b36a5e5d
```

Hypothesis statement:

> Harmonic candidate base selection changes only exact base discovery while preserving the PAUX-C lossless recovery spine.

Evaluation: `SUPPORTED_BY_DECLARED_TESTS`.

## Critic boundaries

- previous frame is always an eligible baseline;
- selection uses exact changed-word cost after candidate generation;
- a harmonic candidate cannot worsen the selected changed-word cost;
- no sinusoidal or floating predictor enters PAUX-C decode;
- corrupted deltas remain detectable by exact verification;
- unresolved harmonic state produces no harmonic candidate;
- live static AUX remains on the existing RUN path;
- GREMLIN has no authority to select a live recovery state or promote a codec result.
