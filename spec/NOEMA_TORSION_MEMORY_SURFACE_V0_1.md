# NOEMA Torsion Memory Surface v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: PNCore-BioOS v0.2.7

## Purpose

The torsion-memory surface is a live derived working-state layer over the admitted PAUX harmonic memory spine. It binds resolved H-band phase/frequency state to canonical Stage-3 resonance edges without replacing persistent identity or capability authority.

```text
PAUX / PNStore
 -> Stage-2 harmonic fits
 -> Stage-3 resonance graph
 -> NOEMA torsion memory generation
 -> QHTRI/Kuramoto memory flow
 -> recall candidate
 -> PNCAP
 -> scheduler
 -> AUX
```

Authority remains:

```text
OBJECT_ID authority = PNV_STATE_OBJECT
capability authority = PNCAP
effect authority = AUX
persistent generation authority = PNStore
```

The torsion surface is `DERIVED_WORKING_STATE`.

## Node state

For each active memory band `H_i`:

```text
NODE H_i
THETA theta_i
OMEGA omega_i
AMPLITUDE A_i
FIT_DERIVATION_ID
SOURCE_OBJECT_ID
LINEAGE_REF
```

An H-band participates only when upstream phase/frequency provenance is admitted. `PHASE_UNKNOWN` or `FREQUENCY_UNRESOLVED` produces an inactive node rather than a numeric placeholder.

## Torsion edge

A canonical Stage-3 edge stores `i < j` and

```text
f_i/f_j = m/n
R_ij
DELTA_ij
```

The torsion-memory edge is

```text
EDGE(i,j,m,n,tau_ij,K_ij,R_ij)
tau_ij := DELTA_ij
```

`K_ij` requires an explicit versioned coupling-policy source. Missing coupling authority gives `K_ij=INACTIVE`, not a guessed value.

The normative phase residual is

```text
epsilon_ij = wrap(n*theta_i - m*theta_j - tau_ij)
```

This preserves the exact Stage-3 `m:n` invariant.

Reverse view follows Stage-3 semantics:

```text
m:n -> n:m
tau_ji = -tau_ij mod 2*pi
R_ji = R_ij
```

Only the canonical edge is stored.

## Affine phase transport and holonomy

An admitted edge implies the local transport relation

```text
theta_j = (n/m)*theta_i - tau_ij/m
```

or

```text
T_{j<-i}(theta) = a*theta + b
a = n/m
b = -tau_ij/m
```

A path composes these affine transports. A closed cycle has phase-independent torsion holonomy only when its composed scale satisfies

```text
A_cycle = 1.
```

For such a cycle the residual offset

```text
H_cycle = wrap(B_cycle)
```

is the discrete torsion/holonomy defect recorded by the working surface.

For 1:1 cycles this reduces to the oriented sum of torsion offsets.

## Generation publication

The surface is double-buffered:

```text
MEMORY_SURFACE_A
MEMORY_SURFACE_B
ACTIVE_MEMORY_HEAD
```

Writer:

```text
read head G_n
 -> prepare inactive G_{n+1}
 -> validate complete node/edge set
 -> validate finite resolved values
 -> validate canonical edge uniqueness
 -> bind source graph derivation
 -> publish ACTIVE_MEMORY_HEAD atomically
```

Readers observe one complete generation only.

Every recall/orchestration record carries `MEMORY_EPOCH`. If selection epoch differs from execution epoch:

```text
STALE_MEMORY_EPOCH -> RESELECT
```

## Quiet live state

If the current live AUX trajectory has no admitted Stage-2 rational fit / Stage-3 edge graph, the surface publishes:

```text
STATUS QUIET_UPSTREAM_UNRESOLVED
ACTIVE_NODE_COUNT 0
EDGE_COUNT 0
```

It does not invent theta, omega, tau or K values.

## Runtime materialization

Current reference live root:

```text
/dev/shm/ciel_noema/torsion_memory/
```

This is a runtime materialization of the derived surface. It does not become persistent authority merely by existing under `/dev/shm`.
