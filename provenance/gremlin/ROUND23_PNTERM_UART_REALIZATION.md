# GREMLIN Round 23 — PNTERM UART realization spine

Status: SUPPORTED_BY_DECLARED_STRUCTURAL_TESTS
Bounded: true
Canon allowed: false

## Candidate question

Does the UART16550 terminal adapter preserve the existing BioOS semantic-identity → physical-realization → admission → physical-transition → state → evidence spine?

## Result

```text
structurally_isomorphic = true
comparison_sha256 = b477fea1bb7ada0554b3f1f8095ecb9e67d0e1050fccba7475eada147040c9f9
signature_sha256 = 1af2349f778fda02caec08c8040e758e3e7820b4419dd2882a0b03f22aa0a2f6
```

Candidate statement:

> PNTERM UART16550 adapter preserves the BioOS identity-to-realization-to-admission-to-physical-transition-to-evidence spine.

Status remains `SUPPORTED_BY_DECLARED_STRUCTURAL_TESTS` with `canon_allowed=false`.

## Falsification gates

The candidate is rejected by:
- physical I/O before exact adapter admission;
- adapter/resource-base mismatch;
- probe mismatch followed by initialization or transfer;
- unbounded polling;
- TX timeout that still writes THR;
- RX timeout that consumes RBR;
- missing physical-transition evidence.
