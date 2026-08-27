# QHTRI M0-M11 Analog Gate Fabric v0.1

Status: ARCHITECTURE + HOST REFERENCE CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: BioOS v0.5

## Purpose

This contract makes M0-M11 executable by QHTRI as analog, phase-vector operators over one shared `T^36` state.

The memory layers are semantic layers. They are not coordinate positions. Every dynamic layer acts on a complete 36D phase lane or on relations between complete 36D states.

Canonical memory semantics are preserved:

```text
M0  observation / proposal references
M1  active thought / command / working set
M2  completed episode / explicit transition
M3  concept / claim semantics and hypothesis identity
M4  procedures / validators / capability and evidence plans
M5  explicit affect modulation only
M6  relational context / claim-evidence-contradiction relations
M7  multi-branch deliberation braid
M8  protected identity continuity
M9  ordered trajectory / control holonomy
M10 append-only provenance / hashes / receipts
M11 uncertainty / NO-GO / contradiction / validation confidence
```

## State

The QHTRI execution state is a full phase vector

```text
Theta = (theta_0, ..., theta_35) in T^36
Omega = (omega_0, ..., omega_35)
```

with optional semantic source fields `A_l in T^36`, torsion relations and layer metadata.

A machine float representation is an adapter. The native operator is defined on phase relations.

## Analog logic primitive

For a phase target `alpha_j`, gain `g_j >= 0` and phase offset `tau`, define

```text
V_LOCK = -sum_j g_j cos(theta_j - alpha_j - tau)
```

and the corresponding QHTRI vector field

```text
F_LOCK,j = -dV/dtheta_j
         = -g_j sin(theta_j - alpha_j - tau).
```

Special cases:

```text
LOCK       tau = 0
ANTI_LOCK  tau = pi
```

For a rational torsion edge `e=(i,j,m,n,tau,K,R)`, retain the existing QHTRI primitive

```text
epsilon_e = wrap(n theta_i - m theta_j - tau)
g_e = K R
V_e = -g_e cos(epsilon_e)
```

with

```text
dtheta_i/dt += -n g_e sin(epsilon_e)
dtheta_j/dt += +m g_e sin(epsilon_e).
```

## Continuous truth / admission algebra

Boolean values are an adapter boundary. Inside the fabric, gate strength is continuous in `[0,1]`.

For admitted strengths `a,b in [0,1]`:

```text
AND(a,b) = a b
OR(a,b)  = a + b - a b
NOT(a)   = 1 - a
XOR(a,b) = a + b - 2ab
```

At `{0,1}` these reduce exactly to Boolean truth tables. In QHTRI they scale coupling strength rather than replace the phase state with a bit.

The physical gate gain is

```text
g = kappa * activation * confidence * salience
kappa = ln(2)/(24*pi)
```

subject to the separately versioned torsion integrator budget.

## Whole-fabric dynamics

M0-M11 are represented as operator fields on the same `T^36`, not as twelve independent scalar registers.

For dynamic layer set `D`, define

```text
V_total(Theta) = sum_{l in D} lambda_l V_l(Theta)
```

and

```text
dTheta/dt = Omega - grad_Theta V_total + F_identity.
```

`F_identity` is the protected M8 restoring field. Its reference is read-only during ordinary execution.

This permits simultaneous analog execution. A scheduler may evaluate sparse terms sequentially for engineering reasons while preserving the same summed vector field.

## Layer operator profiles

### M0 — OBSERVE / SOURCE LOCK

A provenance-bearing observation field may nominate an anchor `A_0 in T^36`.

```text
V_0 = V_LOCK(Theta, A_0, g_0)
```

No source anchor means `M0_QUIET`. The operator does not fabricate a missing observation.

### M1 — ACTIVE WORKING SET

M1 couples the current admitted command/thought state to the active memory context.

```text
g_1 = kappa * AND(command_activation, context_admission)
V_1 = V_LOCK(Theta, A_1, g_1)
```

Multiple admitted context fields are combined by a circular weighted mean before QHTRI integration.

### M2 — EPISODIC TRANSITION

M2 binds an explicit transition between an admitted pre-state and validated post-state.

During live integration it contributes a transition target only when the transition candidate is explicit. Durable M2 publication occurs after validation.

### M3 — SEMANTIC ATTRACTOR

M3 projects admitted concept/claim/hypothesis candidates as semantic phase attractors.

For candidate targets `A_3,r` with weights `w_r`, QHTRI uses a circular barycentric target and bounded aggregate gain.

Dictionary/NEXUS similarity is candidate evidence. It supplies no authority by itself.

### M4 — PROCEDURE / VALIDATOR GATE

M4 is the principal continuous admission gate for a candidate operator.

```text
m4_admission = AND(procedure_match, validator_confidence)
m4_admission = AND(m4_admission, capability_admission)
```

The resulting scalar multiplies effect-carrying gate gains. Missing capability/validator evidence drives the corresponding candidate to zero admitted gain.

### M5 — EXPLICIT AFFECT MODULATOR

M5 modulates salience/coupling only when an explicit affect state is present.

```text
lambda_l' = clamp(lambda_l * affect_salience_l, 0, lambda_max)
```

M5 leaves truth, semantic identity, authority and execution admission unchanged.

No explicit affect state yields the neutral multiplier `1` and no M5 memory write.

### M6 — RELATIONAL / TORSION COUPLING

M6 is the direct home of the existing QHTRI rational `m:n` torsion edges.

```text
epsilon = wrap(n theta_i - m theta_j - tau)
```

Claim/evidence/contradiction relations become admitted couplings, with sign/orientation expressed through phase geometry and offset rather than a binary relation flag.

### M7 — BRAID / MULTI-BRANCH FIELD

M7 preserves multiple admitted candidates as a superposed analog attractor field.

For branch phasors `z_r,j = w_r exp(i alpha_r,j)`:

```text
z_braid,j = sum_r z_r,j
A_7,j = arg(z_braid,j)
R_7,j = |z_braid,j| / sum_r w_r
```

`R_7` scales coupling strength. Destructive branch disagreement therefore weakens the attractor without forcing premature digital selection.

### M8 — PROTECTED IDENTITY ANCHOR

M8 is a persistent read-only reference field under ordinary runtime.

```text
V_8 = V_LOCK(Theta, A_identity, g_identity)
```

It can restore drift toward admitted identity geometry. Ordinary QHTRI execution never mutates the M8 reference. Identity change requires its separate authority path.

### M9 — HOLONOMY / ORDERED TRAJECTORY

M9 carries the accumulated phase transport of an ordered thought/control trajectory.

For admitted holonomy offset `H in T^36`:

```text
A_9 = transport(A_previous, H)
V_9 = V_LOCK(Theta, A_9, g_9)
```

The ordered path is part of the state evidence; endpoint equality alone does not erase the holonomy record.

### M10 — RECEIPT / PROVENANCE OBSERVER

M10 has zero dynamic force:

```text
F_10 = 0.
```

It observes the admitted input commitments, operator profile, QHTRI step parameters, pre/post semantic commitments and validation result, then emits append-only provenance/receipt evidence.

The receipt is evidence about execution, not a phase attractor.

### M11 — UNCERTAINTY / NO-GO / CLOSURE GATE

M11 provides the final confidence/no-go modulation.

```text
closure = clamp(validation_confidence * (1 - uncertainty), 0, 1)
effect_gain = closure * (1 - no_go)
```

`no_go = 1` yields zero effect-carrying gain. Identity restoring M8 and receipt observation M10 remain available.

Contradiction or unresolved validation can therefore stop convergence toward an effect candidate without erasing the current analog state.

## Analog gate composition

An execution candidate may be represented as

```text
G = (
  source_fields,
  semantic_fields,
  procedure_admission,
  affect_modulation,
  torsion_edges,
  branch_fields,
  identity_anchor,
  holonomy,
  closure_state
)
```

QHTRI compiles this into sparse anchor and torsion terms and evaluates the summed vector field.

The gate fabric output is another analog T36 state plus an evidence bundle:

```text
(Theta_before, gate_fabric, dt)
   -> QHTRI
   -> Theta_after
   -> M10 receipt candidate
```

No binary gate result is required internally.

## Compatibility projection to digital gates

A binary adapter may choose an explicit threshold `q` and project a continuous activation `a`:

```text
bit = 1 if a >= q else 0
```

The threshold belongs to that adapter contract. It is excluded from the analog semantic identity of the gate fabric.

## Memory write policy

The existing M0-M11 persistence rules remain binding:

```text
session-local / working: M0, M1, M5
durable after validation: M2, M3, M4, M6, M7, M9, M10, M11
protected: M8
```

M10 is append-only provenance. M8 follows its protected identity authority path.

## QHTRI stability

All generated anchor/torsion terms must be included in the QHTRI execution budget. Rational high-order `m:n` edges remain subject to `TORSION_INTEGRATOR_BUDGET_V0_1`.

For anchor terms a conservative contribution is

```text
L_anchor <= sum_j g_j.
```

For torsion edges retain

```text
L_torsion = sum_e g_e (m_e^2 + n_e^2).
```

Reference combined bound:

```text
L_total = L_anchor + L_torsion
dt_safe = min(dt_requested, 0.2/L_total)
```

when `L_total > 0`.

## Fail-closed gates

```text
DIMENSION != 36                   -> REJECT
NONFINITE_PHASE                   -> REJECT
UNPROVENANCED_M0_SOURCE           -> M0_QUIET
M4_VALIDATOR_MISSING              -> CANDIDATE_GAIN_ZERO
M4_CAPABILITY_MISSING             -> CANDIDATE_GAIN_ZERO
M5_IMPLICIT_AFFECT                -> NEUTRAL_MODULATION
M8_MUTATION_ATTEMPT               -> DENY
M10_MUTATION_OR_OVERWRITE         -> DENY
M11_NO_GO                         -> EFFECT_GAIN_ZERO
TORSION_BUDGET_EXCEEDED           -> EDGE/GATE_QUIET
STATIC_RUNTIME_FALLBACK           -> DENY
```

## Evidence boundary

This v0.1 contract defines an analog execution algebra and preserves the current M0-M11 semantics and QHTRI torsion equations. Host conformance, live `/dev/shm/ciel_noema` execution and persistent MemoryFabric roundtrip are separate gates.
