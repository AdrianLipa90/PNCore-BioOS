# x86_64 Bootstrap Contract v0.2

Status: PHYSICAL BACKEND CANDIDATE / HOST BUILD PASS
Epistemic operator: CHYBA

This layer is the minimal translation boundary between x86 reset semantics and PNCore native state admission.

Current exact path:

```text
RESET @ 0xFFFF0
 -> PNROM @ 0xF0000
 -> CPUID long-mode admission
 -> PNMap PML4/PDPT/PD substrate
 -> protected mode
 -> long mode
 -> PNVector Handoff copy to 0x5000
 -> PNCore @ 0xF0156
 -> PNR identity admission
 -> Sigma_0 candidate @ 0x5200
 -> evidence
```

Required admitted outputs to PNCore:

```text
CPU_MODE = LONG_MODE
PNMAP_ROOT = CR3 / 0x7000
PNVECTOR_HANDOFF = 0x5000
ARCH_REALIZATION_ID = PNR content identity
SIGMA0_TARGET = 0x5200
TRANSITION_EVIDENCE = 0x5300
PNMAP_EVIDENCE = 0x5400
```

PNFS policy, scheduling, user-space policy and broader device lifecycle remain later explicit gates.

Current host evidence:

```text
ROM size = 65536 bytes
reset vector offset = 0xFFF0
final ELF relocations = 0
runtime emulator execution = pending
physical execution = pending
```
