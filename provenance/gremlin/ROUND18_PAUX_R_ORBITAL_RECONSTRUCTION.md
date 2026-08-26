# GREMLIN Round 18 — PAUX-R Orbital Reconstruction

Status: BOUNDED / READ_ONLY / CANDIDATE AUDIT

## Question

Can an orbital model plus quantized residual implement the existing PAUX-R reconstruction evidence spine while preserving a separate reconstruction identity?

Existing PAUX-R spine:

```text
PNV_STATE_OBJECT(SOURCE)
 -> RELATIONAL_MODEL(MODEL)
 -> RECONSTRUCT(TRANSFORM)
 -> RECONSTRUCTION_METRICS(METRICS)
 -> QUALITY_GATE(CONDITION)
 -> RECONSTRUCTION_ID(IDENTITY)
 -> RECEIPT(EVIDENCE)
```

Orbital reconstruction spine:

```text
SOURCE_OBJECT_ID(SOURCE)
 -> ORBIT_MODEL_QRESIDUAL(MODEL)
 -> RECONSTRUCT(TRANSFORM)
 -> QUALITY_METRICS(METRICS)
 -> QUALITY_GATE(CONDITION)
 -> RECONSTRUCTION_ID(IDENTITY)
 -> RECEIPT(EVIDENCE)
```

Result:

```text
structurally_isomorphic = true
comparison_sha256 = c4e08146e287620a27ecc66fa41e52dcac4316d716d47d38c28e3010daa70a1a
hypothesis_id = gremlin:hypothesis:sha256:3e8f3fa852f31ec599fbd8bd7682c2ff156bc66f2a28776177339fedba41186b
```

Hypothesis statement:

> Orbital-model plus quantized-residual reconstruction preserves the PAUX-R reconstruction evidence spine while keeping a separate reconstruction identity.

Evaluation: `SUPPORTED_BY_DECLARED_TESTS`.

## Critic boundaries

- source `OBJECT_ID` remains a provenance reference;
- every representation carries its own `RECONSTRUCTION_ID`;
- quality metrics are explicit and versioned;
- smallest representation is selected only among profiles that pass the declared gate;
- unresolved bands use residual reconstruction rather than invented harmonic fits;
- exact PAUX-C remains preferred where it is already the appropriate representation;
- PAUX-R remains `RECONSTRUCTION_ONLY`;
- GREMLIN cannot promote reconstructed state into capability or effect authority.
