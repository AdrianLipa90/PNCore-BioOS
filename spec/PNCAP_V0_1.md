# PNCAP v0.1 — Generation-Bound Capability Admission

Status: ARCHITECTURE CANDIDATE

PNCAP is the access/admission model for PNObject transitions.

## Structural source

PNCS v0.26 already uses an explicit chain:

```text
EffectRequest
 -> AuthorizationGrant
 -> bounded adapter
 -> effect
 -> EffectReceipt
```

PNCAP lifts the same structural invariant into generic BioOS object admission.

## Capability identity

```text
pncap:sha256:<canonical-grant-payload>
```

A grant binds exactly:

```text
principal_object_id
principal_generation_id
target_object_id
target_generation_id
operation_kind
capability_scope
environment_generation_id
expiry_condition_or_none
delegation_policy
```

## Admission

```text
principal identity
 + target generation
 + operation request
 + exact capability grant
 + current environment generation
 -> coupling
 -> admission gate
 -> PNObject transition
 -> next generation
 -> receipt
```

Default registry state contains zero grants. A state-changing transition requires an explicit matching capability object admitted by the current authority path.

## Initial operation kinds

```text
READ
RELATE
CREATE_GENERATION
COMMIT_GENERATION
RESOLVE_VIEW
EXECUTE_PROGRAM
BIND_DEVICE
```

These are capability-domain operation kinds. They do not extend the PNV opcode registry.

## Exact-target rule

A v0.1 capability is bound to one target object identity and one admitted target generation unless its canonical scope explicitly declares a deterministic relation-set scope.

## Delegation

v0.1 canonical grant policy uses explicit delegation state. Initial system grants use `NO_DELEGATION`.

## Evidence

Every admitted transition records the exact capability ID in its transition evidence so inverse provenance can recover:

```text
state generation
 -> transition
 -> capability
 -> request
 -> principal
 -> environment generation
```
