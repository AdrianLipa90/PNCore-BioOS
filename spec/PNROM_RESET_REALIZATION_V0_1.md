# PNROM Reset Realization v0.1

Status: IMPLEMENTED CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false

## Purpose

PNROM is the first architecture-specific physical realization boundary for PNCore-BioOS. It maps the x86 reset vector into a deterministic PNROM entry while preserving the PN Transition Spine.

## Contract

```text
ROM identity + reset environment + architecture authority
-> reset-vector coupling
-> admission
-> physical transition
-> PNCore-entry candidate state
-> evidence
```

The first v0.1 gate proves the `RESET -> PNROM entry` byte-layout candidate. PNCore execution remains a later gate.

## Physical layout

```text
ROM size             65536 bytes
ROM physical window  0xF0000..0xFFFFF
entry                 0xF0000
reset vector          0xFFFF0 (ROM offset 0xFFF0)
reset transfer        far jump F000:0000
```

The entry emits the deterministic byte sequence `PNROM\n` to x86 debug I/O port `0xE9` and then halts. No legacy BIOS interrupt or firmware service is invoked.

## Authority separation

`native/PNROM_RESET_REALIZATION_V0_1.pnv` is the PNCS-side witness. `arch/x86_64/pnrom/pnrom_reset.S` is an architecture realization source used to produce machine bytes before a native PN code generator exists. The generated ROM image is evidence of the physical realization and does not self-promote the PNV witness.

## GREMLIN candidate audit

GREMLIN v0.5 compared the PN Transition Spine with PNROM and a classic layered stage0/stage1/loader model. PNROM was structurally isomorphic to the spine; the layered candidate was not. The GREMLIN critic returned PASS. This is candidate-selection evidence only.
