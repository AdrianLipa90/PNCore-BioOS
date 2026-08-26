# PNROM x86_64 deterministic host build

The build consumes one admitted 416-byte PNVector Handoff test binding at:

```text
build/x86_64/pnvector_handoff_test.bin
```

The BioOS target tree contains no Python runtime.

Run from repository root:

```text
as --32 -o build/pnrom_reset.o arch/x86_64/pnrom/pnrom_reset.S
as --32 -o build/pnrom_longmode.o arch/x86_64/pnrom/pnrom_longmode.S
as --32 -o build/pncore_entry.o arch/x86_64/pncore/pncore_entry.S
as --32 -o build/pnscheduler.o arch/x86_64/pncore/pnscheduler.S
as --32 -o build/pnclock.o arch/x86_64/pncore/pnclock.S
as --32 -o build/pnr_genesis.o arch/x86_64/pncore/pnr_genesis.S
as --32 -o build/pnvh_template.o arch/x86_64/pncore/pnvh_template.S
ld -m elf_i386 -T arch/x86_64/pnrom/pnrom.ld \
  -o build/pnrom_v0_2.elf \
  build/pnrom_reset.o build/pnrom_longmode.o build/pncore_entry.o \
  build/pnscheduler.o build/pnclock.o build/pnr_genesis.o build/pnvh_template.o
objcopy -O binary --gap-fill 0xff build/pnrom_v0_2.elf build/pnrom_v0_2.bin
```

Required ROM size: exactly 65536 bytes. Reset vector begins at offset `0xFFF0`.

## Harmonic scheduler object

v0.2+ links `arch/x86_64/pncore/pnscheduler.S` into the same 64 KiB reset ROM. The selector uses one tick counter and `BSF` classification; it does not require seven independent timers.

## PN Clock object

v0.2+ also links `arch/x86_64/pncore/pnclock.S`. It implements an exact rational 7.83 Hz absolute phase-index mapping and a fail-closed CPUID/TSC-deadline probe. Missing exact CPUID.15 frequency data does not fall back to an estimated CPU MHz value.
