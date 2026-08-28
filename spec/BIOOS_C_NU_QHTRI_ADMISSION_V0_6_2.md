# BioOS C-Nu QHTRI Admission v0.6.2

Status: `IMPLEMENTED CANDIDATE / EFFECT-POLICY + ROUTING FIREWALL`

Parent: `BIOOS_C_NU_QHTRI_ADMISSION_V0_6_1`

## Purpose

v0.6.2 closes two semantic escalation paths found during BELZEBUB audit of v0.6.1.

v0.6.1 correctly kept all pre-operator envelopes at zero QHTRI force and retained

```text
authority_grant = false
execution_admitted = false
production_runtime_write = false
```

but:

1. the capability field was not restricted by the canonical claim `effect_policy`; and
2. `request_shared_absolute_spectrum=true` was only blocked when the caller explicitly selected `C-Nu-3`, so a single-claim request could otherwise bypass the spectrum firewall route.

No physical execution was admitted by v0.6.1, but both semantic routes were too permissive.

## v0.6.2 effect-policy separation

The canonical GREMLIN policies are typed into three disjoint BioOS binding modes:

```text
C-Nu-1 / M4_AND_M11_GATED
    -> OPERATOR_BINDABLE

C-Nu-2 / KNOWLEDGE_FIREWALL_NO_DIRECT_EFFECT
    -> KNOWLEDGE_ONLY

C-Nu-3 / HARD_NO_GO_ON_SHARED_ABSOLUTE_SPECTRUM
    -> ENFORCEMENT_ONLY
```

Only `OPERATOR_BINDABLE` may carry `capability_ref` or positive `capability_admission` toward a later operator-binding step.

Capability metadata on `KNOWLEDGE_ONLY` or `ENFORCEMENT_ONLY` fails closed.

## Cross-claim routing firewall

Any request with

```text
request_shared_absolute_spectrum = true
```

must traverse

```text
claim_id = C-Nu-3
```

Requests that attach the shared-spectrum flag to C-Nu-1 or C-Nu-2 are rejected fail-closed rather than silently evaluated without the canonical spectrum-holonomy firewall.

This makes C-Nu-3 a mandatory semantic choke point for shared absolute-spectrum use.

## Status semantics

For C-Nu-1:

```text
PRECONDITION_OPEN_ZERO_FORCE
CAPABILITY_OPEN_ZERO_FORCE
READY_FOR_SEPARATE_OPERATOR_BINDING_ZERO_FORCE
```

For C-Nu-2:

```text
KNOWLEDGE_ONLY_ZERO_FORCE
operator_binding_required = false
```

For C-Nu-3:

```text
FIREWALL_CLEAR_ZERO_FORCE
M11_NO_GO_ZERO_FORCE
operator_binding_required = false
```

## Zero-force invariant

All v0.6.2 envelopes remain pre-operator metadata:

```text
character_term_count = 0
force_status = ZERO_FORCE_ADMISSION_METADATA_ONLY
authority_grant = false
execution_admitted = false
production_runtime_write = false
```

C-Nu-1 becoming `READY_FOR_SEPARATE_OPERATOR_BINDING_ZERO_FORCE` still does not create a phase target, torsion edge, character term, authority grant, or runtime write.

## Deterministic replay

Validation reconstructs the complete envelope from the pinned canon binding plus the sealed request. Re-sealing a modified projection is insufficient to pass validation.

v0.6.2 additionally checks:

- claim `effect_policy` against the canonical binding;
- derived `binding_mode`;
- exact `operator_binding_required` eligibility;
- zero effective capability on non-operator claims;
- mandatory C-Nu-3 routing for shared absolute-spectrum requests;
- zero character terms;
- M10 append-only behavior;
- the existing non-authority boundary.

## Adversarial controls

The regression suite includes:

1. re-sealed `KNOWLEDGE_ONLY -> OPERATOR_BINDABLE` tamper;
2. re-sealed positive effective capability on `ENFORCEMENT_ONLY`;
3. direct positive capability request for C-Nu-2;
4. capability-reference injection into C-Nu-2;
5. direct positive capability request for C-Nu-3;
6. shared-spectrum request routed through C-Nu-1 or C-Nu-2;
7. C-Nu-3 shared-spectrum M11 NO-GO;
8. C-Nu-1 operator-bindable path remaining zero-force and non-executing.

## Supersession rule

v0.6.1 remains a provenance-bearing historical candidate and regression target.

For new C-Nu admission envelopes, v0.6.2 supersedes v0.6.1 because it preserves both the canonical GREMLIN `effect_policy` boundary and the mandatory C-Nu-3 spectrum-firewall route through BioOS admission semantics.

No merge to `main`, BioOS canon promotion, runtime execution admission, or production write is implied by this artifact.
