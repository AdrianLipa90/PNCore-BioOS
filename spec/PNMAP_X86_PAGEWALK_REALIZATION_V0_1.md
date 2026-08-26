# PNMap x86 Page-Walk Realization v0.1

Status: GREMLIN_CANDIDATE / STATIC_PHYSICAL_BINDING_IMPLEMENTED
Epistemic operator: CHYBA

GREMLIN relational comparison found the supplied x86 page-walk graph and PNFS/PNMap resolve graph structurally isomorphic under the explicit roles `ANCHOR, CONTEXT, AUTHORITY, SELECTOR, RESOLVER, TARGET, EVIDENCE`.

Comparison SHA-256:
`a95f358cc1916cc756cf0d0b79657228f1e2dfdba1a88e2272012c5b0e24b80e`

GREMLIN hypothesis receipt:
`4c2af4e0cf35eaabb3912f737621964bb2e643851abe937f3fcd6eee06f31e14`

The first PNROM realization uses CR3 `0x7000`, PML4[0] `0x00008003`, PDPT[0] `0x00009003`, PD[0] `0x00000083`, and emits a bounded PNMap evidence record at `0x5400` after exact entry verification.

Content-addressed PNObject/PNR identity remains the exact object-authority layer for this candidate.
