# NOEMA Torsion Live Observer v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: PNCore-BioOS v0.2.7 stage 2

## Purpose

Construct a live read-only torsion-memory graph from admitted QHTRI phase/frequency telemetry without creating a second owner of the QHTRI oscillator state.

## Candidate precompile

For each unordered oscillator pair `(i,j)`, let the direct natural-frequency ratio be:

```text
omega_i / omega_j
```

The observer finds the nearest reduced rational `m:n` with:

```text
max(m,n) <= 16
RELATIVE_DETUNING <= 0.002
```

The candidate list is compiled only when `omega_sha256` changes.

## Observed phase locking

For a 40-tick observation window:

```text
epsilon_k = wrap(n*phi_i,k - m*phi_j,k)
Z_ij = mean(exp(i*epsilon_k))
R_ij = abs(Z_ij)
tau_ij = arg(Z_ij)
```

Live observer edge admission requires:

```text
R_ij >= 0.90
four consecutive subwindows
at least 3/4 subwindows with R >= 0.90
```

The stored orientation is canonical `i < j`.

Reverse semantics remain:

```text
m:n -> n:m
tau_ji = -tau_ij mod 2*pi
R_ji = R_ij
```

## Coupling

The admitted v0.2.7 reference policy remains:

```text
K_ij = kappa / max(1, degree_i, degree_j)
kappa = ln(2)/(24*pi)
g_ij = K_ij * R_ij
```

Per-node raw coupling load remains bounded by `kappa`.

## Observer-only mode

An admitted observer generation may expose:

```text
36 active QHTRI nodes
derived resonance/torsion edges
source tick range
source hashes
memory epoch
```

but performs no source write and no AUX effect.

```text
RESONANCE -> candidate evidence
candidate evidence -> PNCAP required
PNCAP denial/absence -> NO ACTION
```

## Staleness

An observer generation is bound to its source tick. If the source advances before an orchestration action is admitted:

```text
STALE_SOURCE_TICK -> RECOMPUTE
```
