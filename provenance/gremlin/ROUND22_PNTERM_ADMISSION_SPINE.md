# GREMLIN Round 22 — PNTERM admission spine

Status: SUPPORTED_BY_DECLARED_STRUCTURAL_TESTS
Bounded: true
Canon allowed: false

## Candidate question

Does the first PNTERM command path preserve the existing BioOS source → canonicalization → identity → selector → authority → resolver → target → evidence relation spine?

## Result

```text
structurally_isomorphic = true
comparison_sha256 = d7deca48d51c5b7d1f8ee3a47af827bae9a345f3847c6775e1631ed078f38fbd
signature_sha256 = e82b4f4e3d774711616f83cd6f6644a89a1a6e5c633d047778580fd8d0095402
```

Candidate statement:

> PNTERM v0.1 preserves the existing source-to-authority-to-target-to-evidence admission spine.

The result is `SUPPORTED_BY_DECLARED_STRUCTURAL_TESTS`. It remains a structural candidate/audit result with `canon_allowed=false`.

## Falsification gates

The candidate is rejected if terminal dispatch can:
- bypass exact PNCAP matching;
- write directly to a device instead of AUX;
- interpret shell metacharacters as hidden execution operators;
- dispatch an unknown verb;
- replay an admitted RX sequence;
- violate the requirement that every admitted result carries command/result evidence.
