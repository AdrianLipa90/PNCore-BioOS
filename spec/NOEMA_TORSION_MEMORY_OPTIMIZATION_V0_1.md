# NOEMA Torsion Memory Optimization v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: PNCore-BioOS v0.2.7

## Canonical sparse form

The runtime stores one canonical record per admitted resonance edge and compiles it once per memory generation into contiguous arrays:

```text
i[]
j[]
m[]
n[]
tau[]
g[] = K[]*R[]
L_bound
```

Reverse-edge duplication is absent.

Each Kuramoto step evaluates every active edge exactly once and accumulates its two endpoint contributions.

```text
complexity = O(N+E)
memory = O(N+E)
```

The current H-band surface has `N=36` and at most 630 canonical unordered edges.

## Generation compilation

Compilation occurs when a new torsion-memory generation is prepared. A published generation is immutable with respect to compiled edge geometry.

Cached values are invalidated by any change in:

```text
MEMORY_EPOCH
SOURCE_GRAPH_DERIVATION_ID
COUPLING_POLICY_ID
EDGE_SET
```

## Dirty connected-component update

When topology is unchanged and a state/evidence transition dirties only one connected component, phase flow / basin evidence may be recomputed for that component only.

The component result still carries the parent `MEMORY_EPOCH`. A topology change invalidates component caches and triggers a full graph-component rebuild.

No partial component update may publish a mixed memory generation.

## Reference optimization evidence

Reference host checks require:

- compiled/uncompiled derivative equivalence;
- finite precomputed Euler bound;
- deterministic canonical edge arrays;
- exact component membership;
- no stale component reuse across epoch changes.

Performance figures are fixture-specific evidence rather than universal guarantees.
