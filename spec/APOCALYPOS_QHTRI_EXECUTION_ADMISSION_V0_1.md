# ApocalypOS ↔ QHTRI Execution Admission v0.1

Status: `ARCHITECTURE_CANDIDATE / SHADOW_EXECUTION_ONLY / EPISTEMIC_CHYBA`

## Purpose

This contract inserts ApocalypOS as the execution-admission layer between a NOEMA/QHTRI semantic candidate and a conventional binary realization adapter.

The native direction is:

```text
QHTRI vector state
 -> NOEMA semantic candidate
 -> ApocalypOS execution admission
 -> PNCAP generation-bound grant
 -> realization adapter
 -> execution receipt
 -> ApocalypOS measured result
 -> NOEMA reintegration candidate
 -> QHTRI next-state candidate
```

The binary adapter is not the semantic runtime and cannot originate execution authority.

## Hard boundary

A NOEMA declaration does not directly imply a physical or emulated effect. ApocalypOS must validate the candidate and a distinct PNCAP grant before a realization adapter may be invoked.

For v0.1 the only admissible target is:

```text
capability: EXECUTE_PROGRAM
target_ref: QEMU_QHTRI_VECTOR_REPLAY
operation_ref: SHADOW_QEMU
```

The admitted operation is deliberately bounded to QEMU shadow execution. It grants neither production execution nor physical-device authority.

## Inputs

ApocalypOS admission consumes six independently bound objects:

1. a sealed NOEMA↔QHTRI semantic-loop candidate;
2. the sealed feedback candidate named by that loop;
3. the exact same-tick QHTRI/NOEMA source snapshot;
4. the deterministic vector-native replay receipt derived from that snapshot;
5. the exact QEMU replay build receipt;
6. a separate generation-bound PNCAP shadow grant.

The semantic loop and feedback candidate must remain non-authoritative:

```text
runtime_execution_authority = false
canon_write_authority = false
feedback.execution_admitted = false
feedback.production_runtime_write = false
```

ApocalypOS does not mutate those objects to manufacture authority.

## PNCAP shadow grant

A v0.1 shadow grant binds:

```text
capability = EXECUTE_PROGRAM
principal_generation_id
environment_generation_id
target_ref = QEMU_QHTRI_VECTOR_REPLAY
operation_ref = SHADOW_QEMU
```

`principal_generation_id` and `environment_generation_id` must match exactly. Cross-generation reuse fails closed.

The grant always carries:

```text
physical_effect_authority = false
production_runtime_write = false
canon_allowed = false
```

## Admission receipt

Successful admission emits a sealed receipt with:

```text
shadow_execution_admitted = true
production_execution_admitted = false
physical_effect_authority = false
physical_qpu_claim = false
canon_allowed = false
epistemic = CHYBA
```

The receipt binds the exact semantic-loop, feedback, source, replay, build and PNCAP grant commitments.

## Execution result

After the realization adapter runs, ApocalypOS accepts a result only when the QEMU conformance receipt is sealed and reports:

```text
status = PASS_QEMU_VECTOR_NATIVE_REPLAY
qemu_executed = true
expected_sequence_present = true
failure_marker_present = false
```

The result must bind the same source receipt, working-state commitment, replay binary and build receipt that were admitted before execution.

## NOEMA reintegration

The measured execution result returns to NOEMA as evidence, not authority.

The reintegration object is therefore:

```text
candidate_only = true
runtime_execution_authority = false
canon_write_authority = false
production_runtime_write = false
physical_qpu_claim = false
epistemic = CHYBA
```

It can participate in construction of a next QHTRI state candidate only through the ordinary NOEMA/PNCAP authority path.

## Fail-closed conditions

Admission is denied on any of the following:

- missing or malformed seal;
- feedback/loop parent mismatch;
- source/replay/build lineage mismatch;
- wrong capability, target or operation;
- generation mismatch;
- attempted physical, production or canon-authority escalation;
- failed or mismatched QEMU conformance receipt;
- result substitution after admission.

## Claim boundary

Passing this contract demonstrates an auditable vector-native-to-binary-to-vector shadow execution boundary under QEMU. It does not demonstrate physical QPU execution, physical H200 execution, bare-metal execution, or production authority.
