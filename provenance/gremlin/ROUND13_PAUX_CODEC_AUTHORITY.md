# GREMLIN Round 13 — PAUX codec authority boundary

Status: CANDIDATE / bounded structural audit

## Question

Can compressed PAUX profiles preserve the same recovery/authority relation spine as PAUX-EXACT?

## Explicit graphs

PAUX-EXACT and PAUX-C lossless used the roles:

```text
SOURCE_STATE -> CANONICAL_OBJECT -> ENCODING -> RESTORE -> VERIFY_EXACT -> EVIDENCE
```

PAUX-R used:

```text
SOURCE_STATE -> CANONICAL_OBJECT -> ENCODING -> RESTORE -> VERIFY_RECONSTRUCTION -> EVIDENCE
```

## Result

```text
PAUX-EXACT <-> PAUX-C_LOSSLESS
structurally_isomorphic = true
comparison_sha256 = 37de39ea7c13634daf23a19239b72ca3929a00b597ebde559658ef244d038b96

PAUX-EXACT <-> PAUX-R_RECONSTRUCTION
structurally_isomorphic = false
comparison_sha256 = 0538bfe2f4633d8f15905f8e8d05223e2cc53b8898c15a29ccd911eb01497ca2
```

Hypothesis:

`PAUX-C lossless preserves the exact PAUX authority/recovery relation spine.`

```text
hypothesis_id = gremlin:hypothesis:sha256:3515022ac76654f60c65e0197a50dda16c33b3c8e984e83aa7993ba3a9379392
verdict = SUPPORTED_BY_DECLARED_TESTS
tests = 2/2 PASS
evaluation_sha256 = c2333d2d603e8c412be92a74eed2ea1ad151b8a5a2603a58f498be40b895442d
```

## Engineering consequence

PAUX-C may participate in exact recovery after successful decode and exact object verification. PAUX-R uses a separate reconstruction evidence class with `SOURCE_OBJECT_ID` and `RECONSTRUCTION_ID`.
