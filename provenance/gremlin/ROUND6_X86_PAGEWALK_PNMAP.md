# GREMLIN Round 6 — x86 Page Walk × PNMap Resolve

Status: CANDIDATE / structural match

GREMLIN independently surfaced a stored relation match between `PNCore-BioOS/x86_page_walk` and `PNCore-BioOS/pnfs_resolve`.

```text
structurally_isomorphic = true
comparison_sha256 = a95f358cc1916cc756cf0d0b79657228f1e2dfdba1a88e2272012c5b0e24b80e
```

Roles preserved: `ANCHOR, CONTEXT, AUTHORITY, SELECTOR, RESOLVER, TARGET, EVIDENCE`.

Hypothesis receipt: `4c2af4e0cf35eaabb3912f737621964bb2e643851abe937f3fcd6eee06f31e14`

The v0.2 physical candidate verifies CR3 and exact page-table entries and emits a bounded PNMap evidence record at `0x5400`.
