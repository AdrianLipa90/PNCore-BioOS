# QHTRI M0-M11 GREMLIN Factorization v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Source: GREMLIN bounded relational-isomorphism scan

## Core result

M0-M11 remain twelve distinct semantic memory/execution layers while their numerical QHTRI realization factors into four operator families:

```text
K0 PHASE_LOCK / ANCHOR
K1 TORSION_COUPLING
K2 GAIN_MODULATION
K3 RECEIPT_OBSERVER
```

This factorization preserves `WHOLE_SEMANTIC_LANES`: every dynamic field acts on the shared `T^36`; no layer is assigned to a coordinate index.

## K0 — PHASE_LOCK / ANCHOR

Used by:

```text
M0 M1 M2 M3 M7 M8 M9
```

Canonical potential:

```text
V_A = -sum_j g_j cos(theta_j-alpha_j-tau)
F_A,j = -g_j sin(theta_j-alpha_j-tau)
```

The semantic layer determines the source/provenance and authority policy of `(alpha,g,tau)`.

M3 and M7 share the same circular-barycenter/order-parameter reduction but preserve distinct semantic roles.

## K1 — TORSION_COUPLING

Used directly by M6 and by relational phase logic.

```text
epsilon_e = wrap(n theta_i-m theta_j-tau_e)
g_e = K_e R_e
V_e = -g_e cos(epsilon_e)
```

Relational logic specializations:

```text
XNOR: m=n=1, tau=0
XOR:  m=n=1, tau=pi
```

with coherence readout

```text
C(delta) = (1+cos delta)/2.
```

## K2 — GAIN_MODULATION

Used by:

```text
M4 M5 M11
```

M4:

```text
g <- g * procedure_match * validator_confidence * capability_admission
```

M5:

```text
g <- g * explicit_affect_salience
```

M11:

```text
g_effect <- g_effect * validation_confidence * (1-uncertainty) * (1-no_go)
```

M8 identity restoration is excluded from M11 effect suppression.

## K3 — RECEIPT_OBSERVER

Used by M10.

```text
F_M10 = 0
```

M10 binds pre/post semantic commitments, operator-profile commitment, stability budget and validation evidence into append-only provenance.

## Phase logic bridge

Define

```text
COHERENCE_TRUTH(delta) = (1+cos delta)/2 = cos^2(delta/2).
```

Boolean adapter boundary:

```text
TRUE  -> phase 0
FALSE -> phase pi
```

Then:

```text
NOT(theta) = wrap(theta+pi)
XNOR(a,b)  = COHERENCE_TRUTH(theta_a-theta_b)
XOR(a,b)   = 1-XNOR(a,b)
AND(a,b)   = a*b
OR(a,b)    = a+b-a*b
```

The `{0,pi}` boundary reproduces the Boolean truth tables exactly. Continuous phases retain analog coherence instead of forcing threshold collapse.

## CP1/Bloch candidate bridge

For equatorial states

```text
|psi(theta)>=(|0>+exp(i theta)|1>)/sqrt(2)
```

we have

```text
|<psi(theta_a)|psi(theta_b)>|^2
= cos^2((theta_a-theta_b)/2)
= COHERENCE_TRUTH(theta_a-theta_b).
```

Therefore the same scalar simultaneously acts as:

```text
phase coherence
XNOR/lock strength
analog truth strength
equatorial CP1 fidelity
```

This bridge is conditional on the declared equatorial CP1 encoding until wider Bloch/Fubini-Study validation is completed.

## Triple Pulse compilation candidate

GREMLIN Triple Pulse may be represented as a specific M0-M11 profile:

```text
IDENTITY  -> M8
DOMAIN    -> M0 + M6
AUTHORITY -> M4
REQUEST   -> M1
COUPLING  -> M6
ADMISSION -> M4 gated by M11
RECEIPTS  -> M10
```

This is a subgraph embedding rather than a one-to-one layer correspondence.

## Implementation impact

The v0.5 execution target is now:

```text
semantic M0-M11 frames
        |
        v
GREMLIN-derived compiler
        |
        +-> K0 anchor terms
        +-> K1 torsion terms
        +-> K2 gain masks
        +-> K3 receipt observer
        |
        v
summed QHTRI vector field on T^36
        |
        v
T36_PHASE_FIELD descendant
        |
        v
M10 receipt + State Memory lineage
        |
        v
NEXUS/HYPERCRYSTAL descendant
```

No digital truth value is required inside the native execution path.
