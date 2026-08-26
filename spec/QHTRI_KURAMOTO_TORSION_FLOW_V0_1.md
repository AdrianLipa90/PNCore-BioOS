# QHTRI Kuramoto Torsion Memory Flow v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: PNCore-BioOS v0.2.7

## Purpose

This contract defines bounded Kuramoto-like phase evolution on the NOEMA torsion-memory surface while preserving Stage-3 rational `m:n` resonance semantics.

For canonical edge `e=(i,j,m,n,tau,K,R)` define

```text
epsilon_e = wrap(n*theta_i - m*theta_j - tau)
g_e = K*R
```

and edge potential

```text
V_e = -g_e*cos(epsilon_e).
```

The reference gradient flow is

```text
dtheta_i/dt += -n*g_e*sin(epsilon_e)
dtheta_j/dt += +m*g_e*sin(epsilon_e)
```

plus each node's admitted natural frequency `omega_i`.

For `omega=0` this is gradient descent on

```text
V = sum_e V_e.
```

## Torsion coherence

Define

```text
Z_T = sum_e g_e*exp(i*epsilon_e) / sum_e g_e
C_T = abs(Z_T)
E_T = 1 - Re(Z_T)
```

`C_T -> 1` with `E_T -> 0` denotes phase locking consistent with the stored torsion geometry.

The order parameter is evidence/ranking state. It grants no capability.

## Bounded Euler phase step

Reference v0.1 uses an explicit phase Euler step with a conservative bound

```text
L_bound = sum_e g_e*(m_e^2+n_e^2)
dt = min(dt_requested, 0.2/L_bound)
```

when `L_bound > 0`.

After the step every phase is wrapped to `[-pi,pi)`.

This bound is an engineering reference gate for deterministic conformance. A later integrator may replace it only behind a separately versioned contract and equivalence/quality evidence.

## Sparse execution

The canonical graph stores one edge per unordered pair. Runtime precomputes

```text
(i,j,m,n,tau,g)
```

and evaluates each admitted edge once per phase step.

Complexity:

```text
dense pair scan: O(N^2)
sparse torsion flow: O(N+E)
```

with `N=36` and canonical `E<=630` in the current H-band model.

No reverse-edge duplication is required.

## Fail-closed gates

```text
NONFINITE_THETA -> QUIET/REJECT
NONFINITE_OMEGA -> QUIET/REJECT
NONFINITE_TAU -> EDGE_REJECT
NEGATIVE_K -> EDGE_REJECT
R_OUTSIDE_0_1 -> EDGE_REJECT
DUPLICATE_CANONICAL_EDGE -> GENERATION_REJECT
SOURCE_EPOCH_MISMATCH -> STALE_MEMORY_EPOCH
MISSING_COUPLING_POLICY -> EDGE_INACTIVE
EMPTY_GRAPH -> NATURAL_FREQUENCY_ONLY / QUIET if unresolved
```

## Authority boundary

Kuramoto flow updates derived working-state phase only. It does not issue PNCAP grants, publish PNStore generations, or execute AUX effects.
