# BioOS Vector-Native QHTRI Replay v0.1

Status: `IMPLEMENTED CANDIDATE / HOST-CONFORMANCE PASS / QEMU-TCG REPLAY PASS`

## Purpose

This contract turns one hash-bound, same-tick 36D NOEMA/QHTRI runtime snapshot into a deterministic binary replay image and executes that exact image through a bounded PNROM -> T36 identity -> PNCore QEMU-TCG gate. It does not grant canon authority, physical H200 execution, physical QPU execution, or physical-machine execution.

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
replay_receipt_sha256 = 8b6b5e803d29b41b75b96343a4662ba9c645a5106b6faa08670b70098e617d90
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

The QEMU entry independently validates the fixed binary ABI, exact 36D width, selected-edge indices, finite/non-zero coupling, all 72 float64 phase/frequency lanes, and non-zero source-lineage commitments. It then computes a deterministic 64-bit fold across the exact IEEE-754 lane bits and emits the fold through debugcon for independent host comparison.

## Authority boundary

Every replay receipt fixes:

```text
runtime_execution_authority  = false
canon_write_authority         = false
physical_h200_execution_claim = false
physical_qpu_claim            = false
epistemic                     = CHYBA
```

The QEMU conformance receipt additionally fixes `physical_machine_claim = false`. QEMU-TCG execution is emulator evidence only; it is not a physical-machine, H200, QPU, or canon claim.

## Host conformance

The v0.1 unit surface passes:

```text
pytest tests/test_vector_native_qhtri_replay_v01.py
9 passed
```

The exact source snapshot reconstructs a 680-byte payload with deterministic fold:

```text
vector_fold64 = 687aac2ca5b6feb3
```

## QEMU-TCG execution evidence

GitHub Actions run `35230173714`, head `fa2fa572e308c175bb57491023de3b6f2dbc46ef`, completed successfully. The build step, exact-replay QEMU execution step, and evidence upload all concluded `success`.

The source-bound ROM evidence is:

```text
rom_bytes        = 65536
rom_sha256       = 5cb4942a62edf7706e2cdf7356b3d6e9eff81edc8a32343aa6a2c09dc725d113
replay_rom_offset = 3240
build_receipt_sha256 = 13fc875ade0649ac110c6ec196ffbf614b8936b8cef1f48b98cf101214084f4e
qemu_receipt_sha256  = 27161f5fbb92760f46416b0a59e8daee83c40a1935530b194697163a3e9ea914
```

The observed guest trace was exactly:

```text
PNROM
PN32
PN64
T36ID
PNVQ
PNVQ.FOLD=687aac2ca5b6feb3
PNVQ.OK
```

The host independently reconstructed the same fold, verified the exact replay bytes inside the 64 KiB ROM, and found no failure marker. The QEMU process then remained in the intended success halt loop until the bounded observation timeout. The conformance status was `PASS_QEMU_VECTOR_NATIVE_REPLAY`.

The uploaded evidence artifact is `bioos-vector-native-qhtri-replay-v01-evidence`, artifact id `10500323143`, with archive digest:

```text
sha256:777256948045c444ab0847a60a1468e5359349aa5ac359c8d440d21014f180f9
```

## Next gate

The emulator gate is now closed for this exact snapshot. The next distinct evidence frontier is physical-machine execution with an independently bound device/runtime receipt. That future gate must remain separate from this QEMU evidence and must not inherit physical authority from emulator success.
