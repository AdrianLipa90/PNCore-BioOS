# PNCore-BioOS v0.1 — Generation Cell Bootstrap

Status: **ARCHITECTURE CANDIDATE / CANDIDATE_AUTHORITY_ONLY**

PNCore-BioOS starts from one native invariant and constructs the system from admitted vector transitions.

```text
RESET
 -> architecture bootstrap
 -> Triple Pulse: IDENTITY -> DOMAIN -> AUTHORITY
 -> REQUEST -> COUPLING -> ADMISSION
 -> PNCore Transition Spine
 -> PNStore Generation Cell
 -> PNFS relational view
 -> PNCAP capability admission
 -> Genesis.pnv
 -> Sigma_0
```

## Native parts reused

- `.pnv` remains the native program/witness unit.
- `.pnh5` remains a transactional trajectory/memory/dataset object profile.
- Existing PNCS operators are reused; new PNV opcode count in v0.1: **0**.
- Triple Pulse Boot supplies the admission prefix.
- PNH5/QCRUZER generation and commit patterns supply persistence design input.
- PNCS v0.26 Effect Boundary supplies the structural seed for generation-bound capability admission.

## Candidate primitives

- **PN Transition Spine** — common admitted state-transition contract.
- **PNObject / Generation Cell** — typed content-addressed immutable state object.
- **PNStore** — append/commit/head persistence over Generation Cells.
- **PNFS** — relational view over PNObjects; paths are derived views.
- **PNMap** — common relational mapping/resolve contract.
- **PNCAP** — generation-bound explicit capability grants.
- **PNResource** — CPU, RAM, storage and I/O represented as generation-bound PNObjects.
- **Genesis.pnv** — first native system program producing the initial admitted system state.
- **PNROM** — immutable x86 reset/long-mode physical realization candidate.

## Current physical witness path

```text
RESET @ 0xFFFF0
 -> PNROM @ 0xF0000
 -> CPUID long-mode admission
 -> PNMap PML4/PDPT/PD realization
 -> long-mode entry
 -> PNCore / Genesis handoff boundary
```

The first physical backend target is x86_64. The architecture bootstrap stays deliberately small and hands control to PNCore as early as the hardware permits.

## Authority boundary

This branch is a v0.1 candidate. `EPISTEMIC CHYBA`, `canon_allowed=false`. Exact PNCS v0.23 admission + v0.24 `build_native_program_unit` and emulator/physical boot remain separate gates. `main` is not mutated by this candidate branch.
