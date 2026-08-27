# PNROM x86_64 deterministic host build

The build consumes one admitted 416-byte PNVector Handoff test binding at:

```text
build/x86_64/pnvector_handoff_test.bin
```

The BioOS target tree contains no Python runtime. Host-side reproducibility and conformance utilities live under `tools/` and are not linked into the target ROM.

## PNVector Handoff materialization gate

`arch/x86_64/pncore/pnvh_template.S` includes the handoff byte-for-byte. Therefore a clean checkout must materialize the exact admitted PNVH before assembly; a receipt/hash alone is not a substitute for the source bytes.

For the historical v0.2 witness the required identities are:

```text
handoff_sha256       42877687ea3a86244db5abba64323e16abf3f59fdc32cb2abd1fae8896853bd1
vector_sha256        1696737780aa668ad8ff5d304aa892f696fa0f72a03405f48fb00b076c3d5665
source_context_sha256 1b5b549d9acd31f8343cba88f8d4451b40c83cec775e457e4528a9eb99f320fc
```

Materialization uses:

```text
python tools/pnvector_handoff_builder_v01.py build \
  --vector <exact-288-byte-vector.bin> \
  --basis-binding-hex <exact-32-byte-basis-binding> \
  --source-context-sha256 1b5b549d9acd31f8343cba88f8d4451b40c83cec775e457e4528a9eb99f320fc \
  --expected-handoff-sha256 42877687ea3a86244db5abba64323e16abf3f59fdc32cb2abd1fae8896853bd1 \
  --out build/x86_64/pnvector_handoff_test.bin \
  --receipt provenance/PNVECTOR_HANDOFF_BUILD_RECEIPT_V0_1.json
```

The exact historical 288-byte vector payload and exact 32-byte basis-binding bytes are not present in the current Git tree. Until those provenance-bearing inputs are recovered, an exact rebuild of the historical ROM from a clean checkout is `BLOCKED_EXACT_FIXTURE_MISSING`. Do not synthesize replacement bytes and do not claim byte-identical reproduction. See `provenance/PNVECTOR_HANDOFF_REPRODUCIBILITY_AUDIT_V0_1.json`.

## ROM build

After the exact PNVH gate passes, run from repository root:

```text
as --32 -o build/pnrom_reset.o arch/x86_64/pnrom/pnrom_reset.S
as --32 -o build/pnrom_longmode.o arch/x86_64/pnrom/pnrom_longmode.S
as --32 -o build/pncore_entry.o arch/x86_64/pncore/pncore_entry.S
as --32 -o build/pnscheduler.o arch/x86_64/pncore/pnscheduler.S
as --32 -o build/pnclock.o arch/x86_64/pncore/pnclock.S
as --32 -o build/pnstore_media.o arch/x86_64/pncore/pnstore_media.S
as --32 -o build/pnr_genesis.o arch/x86_64/pncore/pnr_genesis.S
as --32 -o build/pnvh_template.o arch/x86_64/pncore/pnvh_template.S
ld -m elf_i386 -T arch/x86_64/pnrom/pnrom.ld \
  -o build/pnrom_v0_2.elf \
  build/pnrom_reset.o build/pnrom_longmode.o build/pncore_entry.o \
  build/pnscheduler.o build/pnclock.o build/pnstore_media.o build/pnr_genesis.o build/pnvh_template.o
objcopy -O binary --gap-fill 0xff build/pnrom_v0_2.elf build/pnrom_v0_2.bin
```

Required ROM size: exactly 65536 bytes. Reset vector begins at offset `0xFFF0`.

A historical-reproduction run must additionally require the exact expected ROM SHA-256 from the corresponding PNR/build receipt before reporting PASS.

## Harmonic scheduler object

v0.2+ links `arch/x86_64/pncore/pnscheduler.S` into the same 64 KiB reset ROM. The selector uses one tick counter and `BSF` classification; it does not require seven independent timers.

## PN Clock object

v0.2+ also links `arch/x86_64/pncore/pnclock.S`. It implements an exact rational 7.83 Hz absolute phase-index mapping and a fail-closed CPUID/TSC-deadline probe. Missing exact CPUID.15 frequency data does not fall back to an estimated CPU MHz value.

## PNStore Media Core object

v0.2.3 links `arch/x86_64/pncore/pnstore_media.S`. It defines the byte-exact append-only generation medium, CRC32C validation, dual alternating HEAD recovery, and historical exactly-once transition lookup. The media core separates extent preparation from HEAD publication; a device backend must provide a durable barrier between them and another barrier after HEAD publication.
