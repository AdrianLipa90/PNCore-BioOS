# QHTRI Torus Character Field v0.2

Status: ARCHITECTURE_CANDIDATE / OPERATOR_FACTORIZATION
Epistemic operator: CHYBA
Canon promotion: explicit authority only

## Purpose

This revision compiles the force-producing part of the QHTRI M0-M11 analog gate fabric into one sparse character field on `T^36` while preserving all twelve semantic layer identities, gain/admission semantics and M10 lineage.

The existing v0.1 executor remains the reference implementation. v0.2 introduces an equivalent compiled representation and a second reference evaluator used for conformance.

## Character primitive

For

```text
theta in T^36
ell in Z^36
chi_ell(theta)=exp(i ell.theta)
```

define

```text
V_r(theta) = -g_r cos(ell_r.theta-tau_r)
F_r(theta) = -g_r sin(ell_r.theta-tau_r) ell_r.
```

The total field is

```text
V(theta) = sum_r V_r(theta)
F(theta) = sum_r F_r(theta).
```

## Existing kernels as exact specializations

### Anchor/lock

Each anchor lane `j` becomes

```text
ell=e_j
phase_offset=target_j+tau.
```

Thus

```text
-g_j cos(theta_j-target_j-tau)
```

is one character term.

### Rational torsion

Each edge `(i,j,m,n,tau,K,R)` becomes

```text
ell=n e_i-m e_j
g=K R.
```

This reproduces exactly

```text
epsilon=n theta_i-m theta_j-tau
F_i=-n g sin(epsilon)
F_j=+m g sin(epsilon).
```

### Phase logic

XNOR/lock and XOR/anti-lock use

```text
ell=e_a-e_b
```

with `tau=0` and `tau=pi` respectively. Their scalar coherence observable remains

```text
C=(1+cos Delta)/2.
```

## Revised numerical factorization

The earlier Gate IR v0.1 exposed four families:

```text
K0_PHASE_LOCK_ANCHOR
K1_TORSION_COUPLING
K2_GAIN_MODULATION
K3_RECEIPT_OBSERVER.
```

v0.2 merges only the first two force laws:

```text
KCHI_TORUS_CHARACTER_FIELD
K2_GAIN_MODULATION
K3_RECEIPT_OBSERVER.
```

M3 and M7 still use the complex circular barycenter, represented as the reducer primitive

```text
PHASE_CENTROID.
```

The reducer prepares a target consumed by `KCHI`; it does not add a fourth force law.

## Gate IR identity split

v0.2 deliberately carries two commitments.

`character_field_commitment` binds the compiled mathematical character terms only. Layer names, provenance references and semantic admission state are excluded from this digest.

`operator_profile_commitment` binds the complete semantic operator profile: character terms with layer/source metadata, M4/M5/M11 modulation state, M10 observer state, reducer state and all M0-M11 layer statuses.

Consequently two executions can have the same numerical vector field and different semantic/provenance identity:

```text
same character_field_commitment
!= necessarily same operator_profile_commitment.
```

M10 v0.3 receipts bind both digests.

## Character normalization

The mathematical real potential has exact gauges

```text
(ell,tau,g) ~ (-ell,-tau,g)
(ell,tau,g) ~ (ell,tau+2pi k,g)
(ell,tau,g) ~ (ell,tau+pi,-g).
```

The current compiled fabric already requires non-negative gains. Gate IR v0.2 additionally orients `ell` so its first non-zero component is positive and wraps `tau` to the principal interval.

No tolerance-based hash collapse is allowed. Incoming binary floating values remain distinct if principal wrapping leaves distinct binary values, even when they represent mathematically period-equivalent parameters to within floating arithmetic.

### No gcd reduction

`ell` is an exact integer harmonic mode. Replacing

```text
ell=d ell0
```

by `ell0` changes harmonic order and extrema. Therefore Gate IR must preserve all integer coefficients exactly.

```text
GCD_REDUCTION=false.
```

## Stability bound

For one term

```text
H_r=g_r cos(ell_r.theta-tau_r) ell_r ell_r^T
```

so

```text
||H_r||_2 <= |g_r| ||ell_r||_2^2.
```

Therefore

```text
L_character = sum_r |g_r| ||ell_r||_2^2
```

is a conservative global bound for the compiled field.

For anchors this contributes `g_j`; for `m:n` torsion it contributes

```text
g(m^2+n^2),
```

exactly reproducing the existing `TORSION_INTEGRATOR_BUDGET_V0_1` rule.

## Conformance requirements

The v0.2 reference evaluator must pass:

```text
character_force(theta, GateIRv02(fabric)) == qhtri_force(theta,fabric)
character_stability_bound(GateIRv02(fabric)) == stability_bound(fabric)
```

within floating-point roundoff.

Additional invariants:

```text
orientation gauge preserves field/profile commitments
gcd-reduced rational modes have distinct character-field commitments
source/provenance changes may preserve field commitment while changing profile commitment
M10 receipt binds both commitments
M8 remains protected
M10 remains append-only
no authority is granted by compilation
```

## Authority boundary

This factorization changes representation and identity accounting only after conformance. It grants no PNCAP capability, no automatic execution admission, no canonical promotion and no permission to mutate protected M8 or append-only M10 state.
