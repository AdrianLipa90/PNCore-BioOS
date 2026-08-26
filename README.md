# PNCore-BioOS

PNCore BioOS is a candidate vector-native system stack for dynamic AC-flow NOEMA/PhaseNav systems on conventional PC hardware.

Current development line: **v0.2 — Build with GREMLIN**.

```text
RESET @ 0xFFFF0
 -> PNROM @ 0xF0000
 -> x86_64 capability admission
 -> PNMap/MMU substrate
 -> long mode
 -> PNVector Handoff -> RAM 0x5000
 -> PNCore @ 0xF0156
 -> PN Realization admission
 -> Genesis physical predicate
 -> Sigma_0 @ 0x5200
 -> transition evidence @ 0x5300
```

## Core primitives

- **PNV** — native program/witness surface.
- **PNH5** — transactional trajectory/state persistence profile.
- **PNR** — content-addressed architecture-specific physical realization binding.
- **PNObject / Generation Cell** — common generation-bound object model.
- **PNStore** — admitted append/commit persistence.
- **PNFS** — relational object-space view.
- **PNMap** — relational mapping/resolution contract.
- **PNCAP** — generation-bound capability admission.
- **PNResource** — physical resources represented through PNObject semantics.
- **PNVector Handoff** — exact ordered 36D firmware-to-PNCore state carrier.

## GREMLIN-guided reductions

GREMLIN is used only as a bounded candidate generator and structural critic.

Current accepted engineering candidates for this branch:

```text
separate .pnx executable          -> removed as duplicate
layered inode/device ontology      -> replaced by unified PNObject relations
text PNV parser in reset runtime   -> rejected by structural comparison
schedule-only physical table       -> rejected by structural comparison
PN Realization                     -> structural match candidate
x86 page walk <-> PNMap resolve    -> structural match candidate
separate boot-info block           -> folded into PNVector Handoff path
```

## Current evidence

```text
64 KiB PNROM build: PASS
final ELF relocations: 0
reset vector: exact @ 0xFFF0
live PhaseNav registry binding: PASS
PNR program/schedule/composition binding: PASS
PNVector Handoff structural binding: PASS
runtime emulation: pending
physical-machine execution: pending
```

All project-native runtime/program artifacts remain PNV/PNR and assembly bootstrap sources; the target tree contains zero `.py` files.
