# PNCore Convergence Gate v0.1

Status: LOCAL CANDIDATE / CHYBA / canon_allowed=false

## Purpose

Close the first evidence gap between the canonical PNCS Genesis program unit and its x86_64 PN Realization without introducing a second text interpreter.

The gate is:

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
        | exact current ROM build
        v
pnrom_v0_2.bin
        |
        | QEMU debugcon witness
        v
PNROM -> PN32 -> PN64 -> PNCORE -> PNR.OK -> ... -> SIGMA0 -> SCHED
```

## Gate A — static authority/binding equivalence

`tools/convergence_audit_v01.py` requires all of the following:

1. PNR `SOURCE_PROGRAM_ID` equals the canonical v0.24 program ID.
2. PNR composition identity equals the program unit composition identity.
3. PNR operator-schedule SHA-256 equals the program unit schedule SHA-256.
4. The PNR assembly carries the same 32-byte program and schedule digests.
5. PNCore's expected program and schedule digests carry the same bytes.
6. PNR ROM SHA-256 and ROM size equal the current PNStore media build receipt.
7. PNR realization identity equals the realization identity in the current ROM build receipt.
8. Effects, native execution and terminal RETURN remain closed in the v0.24 program unit.

The older `native/GENESIS_V0_1.pnv` is compared to the canonical program-unit opcode sequence. A mismatch is surfaced as a separate provenance classification and is not silently treated as the physical authority source.

## Gate B — emulator execution

`tools/qemu_boot_conformance_v01.py` first hashes the ROM and requires exact equality with the PNR `ROM_SHA256`.

Then it runs the 64 KiB ROM as the x86 BIOS and captures port `0xE9`.

PASS requires this ordered witness:

```text
PNROM
PN32
PN64
PNCORE
PNR.OK
SIGMA0
SCHED
```

and forbids the PNCore failure marker:

```text
X
```

The current PNCore code emits `SIGMA0` and `SCHED` only after its scheduler, exact-rational clock and PNStore media self-tests have passed, so reaching this suffix is a meaningful integrated boot witness.

## Evidence boundary

A static binding PASS is not an emulator-execution PASS.
A QEMU PASS is not a physical-machine execution PASS.

No canon promotion, main mutation or external effect is performed by this package.
