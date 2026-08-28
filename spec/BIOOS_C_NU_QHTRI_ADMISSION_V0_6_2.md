# BioOS C-Nu QHTRI Admission v0.6.2

Status: `IMPLEMENTED CANDIDATE / EFFECT-POLICY FIREWALL`

Parent: `BIOOS_C_NU_QHTRI_ADMISSION_V0_6_1`

## Purpose

v0.6.2 closes a semantic escalation path found during BELZEBUB audit of v0.6.1.

v0.6.1 correctly kept all pre-operator envelopes at zero QHTRI force and retained

```text
authority_grant = false
execution_admitted = false
production_runtime_write = false
```

but the capability field was not restricted by the canonical claim `effect_policy`. A caller could therefore provide positive capability metadata for a knowledge-only or enforcement-only claim and obtain a `READY_FOR_SEPARATE_OPERATOR_BINDING_ZERO_FORCE` status. No physical execution was admitted, but the semantic route toward a later operator binder was too permissive.

## v0.6.2 separation

The canonical GREMLIN policies are now typed into three disjoint BioOS binding modes:

```text
C-Nu-1 / M4_AND_M11_GATED
    -> OPERATOR_BINDABLE

C-Nu-2 / KNOWLEDGE_FIREWALL_NO_DIRECT_EFFECT
    -> KNOWLEDGE_ONLY

C-Nu-3 / HARD_NO_GO_ON_SHARED_ABSOLUTE_SPECTRUM
    -> ENFORCEMENT_ONLY
```

Only `OPERATOR_BINDABLE` may carry positive `capability_admission` and a provenance-bearing `capability_ref`.

Positive capability on `KNOWLEDGE_ONLY` or `ENFORCEMENT_ONLY` fails closed.

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
- zero character terms;
- M10 append-only behavior;
- the existing non-authority boundary.

## Adversarial controls

The regression suite includes:

1. re-sealed `KNOWLEDGE_ONLY -> OPERATOR_BINDABLE` tamper;
2. re-sealed positive effective capability on `ENFORCEMENT_ONLY`;
3. direct positive capability request for C-Nu-2;
4. direct positive capability request for C-Nu-3;
5. C-Nu-3 shared-spectrum M11 NO-GO;
6. C-Nu-1 operator-bindable path remaining zero-force and non-executing.

## Supersession rule

v0.6.1 remains a provenance-bearing historical candidate and regression target.

For new C-Nu admission envelopes, v0.6.2 supersedes v0.6.1 because it preserves the canonical GREMLIN `effect_policy` boundary through BioOS admission semantics.

No merge to `main`, BioOS canon promotion, runtime execution admission, or production write is implied by this artifact.
