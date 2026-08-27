# NOEMA Torsion Coupling Policy v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: PNCore-BioOS v0.2.7

## Reference policy

The first bounded coupling policy uses the canonical PhaseNav information scalar

```text
kappa = ln(2)/(24*pi)
```

and the degree of each node in the admitted canonical torsion graph:

```text
K_ij = kappa / max(1, degree_i, degree_j)
g_ij = K_ij * R_ij
```

Policy ID:

```text
DEGREE_MAX_KAPPA_V0_1
```

## Load bound

For node `i` with degree `d_i>0`, every incident edge satisfies

```text
max(d_i,d_j) >= d_i
K_ij <= kappa/d_i.
```

With `0 <= R_ij <= 1`:

```text
sum_j K_ij*R_ij <= d_i*(kappa/d_i) = kappa.
```

Thus the raw resonance-weighted coupling load of each node is bounded by the canonical `kappa`, independent of graph density.

The generalized `m:n` multipliers remain represented explicitly in the Kuramoto Euler/Lipschitz bound; this load theorem does not remove that separate stability gate.

## Properties

```text
SYMMETRIC TRUE
DETERMINISTIC TRUE
FREE_SCALE_PARAMETERS 0
TOPOLOGY_DEPENDENT TRUE
RECOMPILE_ON_TOPOLOGY_CHANGE TRUE
RECOMPILE_ON_EPOCH_GRAPH_CHANGE TRUE
```

The policy is compiled once per memory generation with the sparse canonical graph.

## Evidence boundary

Reference conformance checks density sweeps, deterministic recompilation, graph relabeling, monotonic mixed `m:n` potential descent, and close 1:1 locking.

Global-minimum convergence is not an admission requirement for mixed multi-harmonic graphs; the dynamic contract requires bounded monotonic gradient behavior and explicit basin evidence instead.
