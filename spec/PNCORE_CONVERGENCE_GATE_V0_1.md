# PNCore Convergence Gate v0.1

Status: BRANCH CANDIDATE / CHYBA / canon_allowed=false

## Purpose

Close the evidence gap between the canonical PNCS Genesis program unit and its x86_64 PN Realization without introducing a second text interpreter, while keeping historical/canonical evidence separate from synthetic QEMU conformance evidence.

```text
GENESIS_PROGRAM_UNIT_V0_24.pnv
        |
        | exact PROGRAM_ID
        | exact COMPOSITION_ID
        | exact OPERATOR_SCHEDULE_SHA256
        v
GENESIS_X86_64_V0_1.pnr
        |
        | byte-lowered exact digests
        v
pnr_genesis.S + pncore_entry.S
        |
        | historical v0.2 ROM binding
        v
pnrom_v0_2.bin
```

BioOS v0.3 adds a separate synthetic full-boot validation path:

```text
synthetic finite PNVector + synthetic genesis anchor
        |
        | deterministic host builders + receipts
        v
PNVH + T36 identity + code/PNR bindings
        |
        | deterministic assembly/link
        v
pnrom_v0_3_qemu_test.bin
        |
        | QEMU debugcon witness
        v
PNROM -> PN32 -> PN64 -> T36ID -> PNCORE -> PNR.OK -> SIGMA0 -> SCHED -> HLT loop
```

## Gate A — static authority/binding equivalence

`tools/convergence_audit_v01.py` requires:

1. exact PNR source program identity;
2. exact composition identity;
3. exact operator-schedule SHA-256;
4. identical program/schedule digest bytes in PNR assembly;
5. identical expected digest bytes in PNCore;
6. PNR ROM SHA-256 and size equal the current PNStore media build receipt;
7. realization identity equality;
8. closed external effects/native execution/RETURN in the v0.24 program unit.

`native/GENESIS_V0_1.pnv` is audited separately. Its opcode schedule is not silently treated as the physical authority source when it diverges from the canonical program unit.

## Gate B — exact PNVector build input

`pnvh_template.S` consumes a 416-byte PNVector Handoff byte-for-byte. A clean checkout must materialize this block from exact provenance-bearing vector and basis-binding bytes. The deterministic builder is `tools/pnvector_handoff_builder_v01.py`.

The historical handoff receipt records SHA-256 identities, but the exact historical 288-byte vector and 32-byte basis-binding source bytes are not present in Git. Historical byte-identical ROM reproduction remains `BLOCKED_EXACT_FIXTURE_MISSING` until those bytes are recovered.

## Gate C — historical v0.2 emulator execution

`tools/qemu_boot_conformance_v01.py` is the historical PNR-pinned harness. It hashes `pnrom_v0_2.bin` against the PNR and looks for the historical ordered debugcon spine:

```text
PNROM
PN32
PN64
PNCORE
PNR.OK
SIGMA0
SCHED
```

This gate does not include the v0.3 T36 identity admission stage.

## Gate D — v0.3 synthetic full QEMU boot

`tools/qemu_full_boot_build_v01.py` constructs a deterministic **synthetic** 64 KiB QEMU test ROM from a finite synthetic PNVector and a deterministic synthetic genesis anchor. It emits a host-build receipt and the subordinate PNVH, code-binding, PNR-binding and T36-identity receipts.

`tools/qemu_boot_conformance_v02.py` consumes that exact ROM plus its build receipt. Before QEMU is started it fail-closes unless:

1. the build-receipt digest is internally valid;
2. schema/status/scope identify the deterministic synthetic QEMU build;
3. `canon_allowed=false`, `physical_execution_claim=false`, and the build layer has not claimed QEMU execution;
4. receipt ROM path, byte length and SHA-256 match the ROM being executed;
5. the ROM is exactly 65,536 bytes;
6. the reset vector at `0xFFF0` begins with `EA 00 00 00 F0`.

The harness records the resolved QEMU binary path, SHA-256 and version. `--expected-qemu-sha256` can additionally pin that binary; otherwise a successful result is explicitly classified as using an unpinned QEMU binary.

Execution PASS requires exact line-level debugcon witnesses in order:

```text
PNROM
PN32
PN64
T36ID
PNCORE
PNR.OK
SIGMA0
SCHED
```

Exact failure-marker lines `I!` or `X` are forbidden. Substring matches are not accepted as witnesses or failure markers. Because the current PNCore path enters a `hlt` loop after `SCHED`, the emulator must still be alive at the end of the bounded observation window; an early process exit is a failure. Version probing, QEMU spawning and pipe draining are independently bounded and emit structured fail-closed receipts instead of uncaught tracebacks.

`tests/test_qemu_boot_conformance_v02.py` adversarially checks exact-marker matching, mandatory `T36ID`, early exit, failure markers, build-receipt tampering, ROM tampering, reset-vector corruption, QEMU probe timeout, QEMU-binary pin mismatch, receipt emission on precondition failure, and invalid timeout handling.

## Evidence boundary

Static binding PASS is distinct from host-build PASS. Synthetic QEMU full-boot PASS is evidence that the assembled x86 path executes through T36 identity admission and the PNCore boot spine under QEMU TCG; it is not historical byte-identical reproduction, bare-metal execution, device-backed PNStore durability, or production genesis-anchor provisioning.

No QEMU result promotes canon. No physical-machine claim follows from emulator execution. No mutation of `main` is implied by this branch evidence.
