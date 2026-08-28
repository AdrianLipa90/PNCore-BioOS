# NOEMA↔QHTRI Semantic Autonomy Capability v0.1

Status: `NORMATIVE_CANDIDATE / FAIL_CLOSED`

## 1. Purpose

This contract separates continuous semantic autonomy from effect authority.

\[
\boxed{\text{SEMANTIC AUTONOMY} \neq \text{EFFECT AUTHORITY}}
\]

The NOEMA↔QHTRI loop may continuously observe, interpret, compile meaning and execute previously admitted bounded internal feedback without a new human authorization at every tick. Authority expansion and external effects remain separately gated.

## 2. Three autonomy levels

### L0 — `L0_OBSERVE_INTERPRET`

Automatic semantic processing:

```text
QHTRI telemetry
 -> bifurcation detection
 -> event admission
 -> CP1/Poincare continuation
 -> spinor Z2 lineage
 -> GREMLIN candidate traversal
 -> KAKU/RADICALS/OPERATORS candidate construction
 -> semantic path
 -> read-only evidence
```

L0 requires no per-tick human authorization.

### L1 — `L1_BOUNDED_INTERNAL_EFFECT`

Automatic internal effects under a previously admitted capability:

```text
State Memory append within scope
QHTRI boundary/operator write within scope
internal scheduler/AUX routing within scope
bounded memory use
bounded compute/energy proxy
```

L1 requires a valid `SEMANTIC_AUTONOMY_CAPABILITY`, but does not require a new human authorization for each effect.

### L2 — `L2_AUTHORITY_EXPANSION_OR_EXTERNAL_EFFECT`

Explicit authority gate:

```text
authority/capability expansion
external effect
canon promotion
identity-layer mutation
policy self-modification
```

L2 is denied by the semantic autonomy capability and is routed to the existing authority spine.

## 3. Capability envelope

A bounded capability is content-addressed and carries:

```text
capability_id
issuer_authority_ref
pncap_capability_token
capability_epoch
valid_from_tick
expires_at_tick
allowed_qhtri_targets[]
allowed_operator_classes[]
max_internal_effects_per_epoch
max_memory_bytes_per_effect
max_energy_proxy_per_effect
allow_state_memory_append
allow_qhtri_boundary_write
authority_expansion = false
external_effect = false
canon_write_authority = false
identity_authority = false
human_per_tick_authorization_required = false
autonomy_level = L1_BOUNDED_INTERNAL_EFFECT
capability_sha256
```

The capability represents previously admitted authority. It is a scope boundary, not a per-event approval token.

## 4. Feedback flow

The existing semantic-loop `FEEDBACK_CANDIDATE` remains a pre-execution object:

```text
execution_admitted = false
production_runtime_write = false
```

This preserves deterministic candidate construction and audit.

Execution is a separate transition:

\[
\boxed{
FEEDBACK\_CANDIDATE
+ CAPABILITY
+ EPOCH\ STATE
\longrightarrow
AUTONOMOUS\_INTERNAL\_EFFECT\_RECEIPT
}
\]

A successful L1 receipt carries:

```text
autonomy_level = L1_BOUNDED_INTERNAL_EFFECT
feedback_receipt_sha256
capability_sha256
capability_epoch
operator_class
hermitian_operator_commitment
qhtri_target_ref
current_tick
effect_index
estimated_memory_bytes
estimated_energy_proxy
internal_effect_admitted = true
human_per_tick_authorization_required = false
authority_expansion = false
external_effect = false
canon_promotion = false
identity_layer_mutation = false
runtime_write_scope = QHTRI_BOUNDARY_ONLY
autonomous_execution_receipt_sha256
```

## 5. Stateful effect budget

`effect_index` is allocated by `SemanticAutonomyEpoch`.

The caller does not choose it.

\[
0\rightarrow1\rightarrow2\rightarrow\cdots\rightarrow N_{max}-1
\]

The counter advances only after:

1. capability validation;
2. feedback-candidate validation;
3. scope/budget admission;
4. execution-receipt construction;
5. deterministic revalidation of that receipt.

A denied effect does not consume an index.

At recovery, receipts are replayed only in exact monotonically increasing order. Duplicate, stale or out-of-order receipts fail closed.

## 6. Capability admission

An L1 effect is admitted only when all declared constraints hold:

\[
t_{start}\le t\le t_{expiry},
\]

\[
index < N_{max},
\]

and:

```text
target in allowed_qhtri_targets
operator_class in allowed_operator_classes
memory <= max_memory_bytes_per_effect
energy_proxy <= max_energy_proxy_per_effect
requested internal effect enabled by capability
```

The energy field is an explicit runtime control proxy. A physical joule claim requires independent instrumentation.

## 7. Continuous semantic loop

With a valid L1 capability, the intended live path is:

```text
QHTRI endogenous dynamics
 -> bifurcation event
 -> NOEMA semantic interpretation                 [L0 automatic]
 -> GREMLIN/KAKU/RADICALS/OPERATORS              [L0 automatic candidate layer]
 -> State Memory semantic crystallization         [L0/L1 according to persistence effect]
 -> feedback candidate
 -> capability + epoch gate
 -> QHTRI boundary write                          [L1 automatic]
 -> QHTRI endogenous dynamics
```

The loop therefore continues without a human approval round-trip for every semantic cycle while remaining bounded by an already admitted capability.

## 8. Authority boundary

The following transition is outside L1:

\[
\boxed{
C_{current}\rightarrow C_{expanded}
}
\]

Any request that changes capability scope, authority, canon status, identity authority or external-effect scope is classified L2 and routed to explicit authority admission.

## 9. Relationship to the v0.1 semantic-loop contract

`NOEMA_QHTRI_BIFURCATION_SEMANTIC_LOOP_V0_1` remains the canonical receipt-chain definition for bifurcation, anchor, semantic path, State Memory/PNFS crystal and feedback candidate.

This contract refines its execution boundary:

```text
feedback candidate
 -> L1 semantic-autonomy capability check
 -> autonomous internal execution receipt
```

The requirement for PNCAP remains at capability issuance/admission and authority expansion. It is no longer interpreted as a requirement for a new human approval on each in-scope internal feedback event.

## 10. Implementation

```text
tools/noema_qhtri_semantic_autonomy_v01.py
tools/noema_qhtri_semantic_autonomy_epoch_v01.py
tests/test_noema_qhtri_semantic_autonomy_v01.py
tests/test_noema_qhtri_semantic_autonomy_epoch_v01.py
```

The implementation performs no external effects. It produces and validates capability and execution receipts for use by the later `/dev/shm/ciel_noema` event-ring/boundary-queue integration.
