# BioOS Vector-Native QHTRI Replay v0.1

Status: `IMPLEMENTED CANDIDATE / HOST-CONFORMANCE PASS / QEMU EXECUTION NOT YET CLAIMED`

## Purpose

This contract turns one hash-bound, same-tick 36D NOEMA/QHTRI runtime snapshot into a deterministic binary replay image suitable for the next bounded QEMU realization gate. It does not grant runtime execution authority, canon authority, physical H200 execution, or physical QPU execution.

The source is:

```text
provenance/BIOOS_VECTOR_NATIVE_QHTRI_SOURCE_V0_1.json
schema  = BIOOS_VECTOR_NATIVE_QHTRI_SOURCE_V0_1
status  = LIVE_SAME_TICK_SNAPSHOT_CAPTURED_FOR_EMULATION_REPLAY
dim     = 36
tick    = 20215
```

The source binds the same-tick phase lane, frequency lane, geometry hashes, selected edge, projective points, source receipt, and working-state commitment.

## Replay image

`tools/vector_native_qhtri_replay_v01.py` validates the source fail-closed and emits one deterministic binary payload:

```text
magic                  8 bytes   PNVQHTR1
version                u32       1
dimension              u32       36
tick                   u64
selected oscillator i  i32
selected oscillator j  i32
coupling               f64
phi[36]                36*f64
omega[36]              36*f64
source receipt          32 bytes
working-state hash      32 bytes
```

Exact payload size for v0.1 is 680 bytes.

The currently bound replay payload has:

```text
replay_binary_sha256 = da6e3499d0a4f9dbad3d173b1cadc36ddcb14cae402aca67b72ba74725a770c4
source_receipt_sha256 = 9680c4b228053db050f2689a9477e4d2b2f8d1c7fb80808adbbc1cc232347492
working_state_sha256  = f05f4048af0058d40fefc5a503519bf66d8a6da600fd7a868340f546a0c1d5db
```

## Fail-closed admission

The replay builder rejects:

- schema/status mismatch;
- non-ACTIVE tether witness in the captured source;
- any canon-authority escalation;
- physical H200 or QPU execution claims;
- dimensions other than exactly 36;
- non-finite phi/omega lanes;
- invalid or zero-coupling selected edge;
- selected-edge phase values that do not equal the bound source lanes;
- projective points on or outside the Poincare unit disk;
- malformed SHA-256 commitments;
- replay receipt tampering.

## Authority boundary

Every replay receipt fixes:

```text
runtime_execution_authority  = false
canon_write_authority         = false
physical_h200_execution_claim = false
physical_qpu_claim            = false
epistemic                     = CHYBA
```

Therefore this stage is a deterministic transport/replay artifact only. A later QEMU execution receipt must separately prove that PNROM/PNCore consumed the exact replay image and reproduced the declared bounded computation. Physical-machine execution remains a separate gate.

## Host conformance

The v0.1 unit surface currently passes:

```text
pytest tests/test_vector_native_qhtri_replay_v01.py
9 passed
```

The exact current source snapshot was additionally loaded through the replay validator and produced the 680-byte payload and hashes recorded above.

## Next gate

The next bounded step is a QEMU-only consumer that:

```text
exact replay image
 -> PNROM/PNCore load
 -> dimension/hash/header validation
 -> bounded vector-native computation
 -> deterministic evidence record
 -> no authority escalation
```

No QEMU execution PASS is claimed by this document until that consumer is implemented and executed against the exact payload commitment above.
