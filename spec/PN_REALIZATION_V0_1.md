# PN Realization v0.1

Status: ARCHITECTURE_CANDIDATE / PHYSICAL_BUILD_VALIDATED
Epistemic operator: CHYBA
Canon promotion: explicit authority only

## Purpose

PN Realization (PNR) binds one canonical PNCS program identity to one exact architecture-specific physical image and its deterministic state/evidence targets.

The v0.1 spine is:

```text
SOURCE_PROGRAM
  -> PROGRAM_IDENTITY
  -> ARCHITECTURE_REALIZATION
  -> ADMISSION
  -> PHYSICAL_TRANSITION
  -> STATE
  -> EVIDENCE
```

The source program remains the semantic authority. PNR carries the exact physical realization binding.

## Identity

The realization identity is SHA-256 over canonical UTF-8 PNR semantic lines, excluding the realization ID declaration and terminal marker.

```text
pnr:realization:sha256:<digest>
```

## Current x86_64 binding

The current physical realization binds the Genesis program ID, composition identity, exact operator-schedule SHA-256, 64 KiB reset ROM, PNVector Handoff at `0x5000`, `Sigma_0` at `0x5200`, transition evidence at `0x5300`, and PNMap/MMU evidence at `0x5400`.

Host assembly/link/build and byte/section/symbol conformance are PASS. Runtime emulation and physical-machine execution remain explicit later gates.
