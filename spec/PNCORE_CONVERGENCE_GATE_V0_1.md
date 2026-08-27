# PNCore Convergence Gate v0.1

Status: BRANCH CANDIDATE / CHYBA / canon_allowed=false
Frontier: `feat/bioos-v0.2.9-convergence`, based on `feat/bioos-v0.2.8-terminal-core`.

## Purpose

Close the evidence gap between the canonical PNCS Genesis program unit and its x86_64 PN Realization without introducing a second text interpreter.

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

## Gate C — emulator execution

`tools/qemu_boot_conformance_v01.py` hashes the ROM against PNR and then requires ordered debugcon evidence:

```text
PNROM
PN32
PN64
PNCORE
PNR.OK
SIGMA0
SCHED
```

with no PNCore `X` failure marker.

## Evidence boundary

Static binding PASS is distinct from emulator execution PASS. Emulator PASS is distinct from physical-machine execution PASS. No canon promotion or `main` mutation is performed by this branch.
