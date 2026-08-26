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
as --32 -o build/pnr_genesis.o arch/x86_64/pncore/pnr_genesis.S
as --32 -o build/pnvh_template.o arch/x86_64/pncore/pnvh_template.S
ld -m elf_i386 -T arch/x86_64/pnrom/pnrom.ld \
  -o build/pnrom_v0_2.elf \
  build/pnrom_reset.o build/pnrom_longmode.o build/pncore_entry.o \
  build/pnr_genesis.o build/pnvh_template.o
objcopy -O binary --gap-fill 0xff build/pnrom_v0_2.elf build/pnrom_v0_2.bin
```

Required ROM size: exactly 65536 bytes. Reset vector begins at offset `0xFFF0`.
