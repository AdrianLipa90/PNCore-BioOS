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
seven independent band timers      -> replaced by single-counter dyadic selector
```

## Current evidence

```text
64 KiB PNROM build: PASS
final ELF relocations: 0
reset vector: exact @ 0xFFF0
live PhaseNav registry binding: PASS
PNR program/schedule/composition binding: PASS
PNVector Handoff structural binding: PASS
PN Harmonic Scheduler host selector: 1,048,576/1,048,576 PASS
runtime emulation: pending
physical-machine execution: pending
```

All project-native runtime/program artifacts remain PNV/PNR and assembly bootstrap sources; the target tree contains zero `.py` files.

## PN Harmonic Scheduler candidate

The current development branch adds a single-clock harmonic admission scheduler anchored at `f0 = 7.83 Hz`. `B0` is a bounded service lane on every tick. Mutually-exclusive admission classes are selected for positive tick index `n` by `band(n) = 1 + nu2(n) = 1 + ctz(n)`. Current admitted classes are `B1..B7`; deeper classes remain `RESERVED_QUIET`. Missed windows and re-entry are skipped; catch-up bursts are denied.

The x86_64 physical selector lives in `arch/x86_64/pncore/pnscheduler.S`. Host execution checked 1,048,576 tick values against the mathematical reference with exact agreement.
