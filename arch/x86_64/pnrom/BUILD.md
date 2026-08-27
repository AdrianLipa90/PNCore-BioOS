# PNROM x86_64 deterministic host build

The build consumes one admitted 416-byte PNVector Handoff at:

```text
build/x86_64/pnvector_handoff_test.bin
```

BioOS v0.3 additionally consumes one exact 256-byte T36 identity record at:

```text
build/x86_64/t36_identity_test.bin
```

The target ROM contains no Python runtime. Host-side builders derive content-addressed inputs before assembly; target code only validates and evolves admitted records.

## PNVector Handoff materialization gate

`arch/x86_64/pncore/pnvh_template.S` includes the handoff byte-for-byte. A clean checkout must materialize the exact admitted PNVH before assembly; a receipt/hash alone is not a substitute for source bytes.

Historical v0.2 witness identities:

```text
handoff_sha256        42877687ea3a86244db5abba64323e16abf3f59fdc32cb2abd1fae8896853bd1
vector_sha256         1696737780aa668ad8ff5d304aa892f696fa0f72a03405f48fb00b076c3d5665
source_context_sha256 1b5b549d9acd31f8343cba88f8d4451b40c83cec775e457e4528a9eb99f320fc
```

Materialization:

```text
python tools/pnvector_handoff_builder_v01.py build \
  --vector <exact-288-byte-vector.bin> \
  --basis-binding-hex <exact-32-byte-basis-binding> \
  --source-context-sha256 1b5b549d9acd31f8343cba88f8d4451b40c83cec775e457e4528a9eb99f320fc \
  --expected-handoff-sha256 42877687ea3a86244db5abba64323e16abf3f59fdc32cb2abd1fae8896853bd1 \
  --out build/x86_64/pnvector_handoff_test.bin \
  --receipt provenance/PNVECTOR_HANDOFF_BUILD_RECEIPT_V0_1.json
```

The exact historical vector and basis-binding inputs are not committed in the current Git tree. Historical clean-checkout reproduction therefore remains `BLOCKED_EXACT_FIXTURE_MISSING` until those exact inputs are recovered. A newly admitted reproducible PNVH generation may be used for v0.3 instead; it must have its own receipt.

## v0.3 T36 identity provisioning

T36 identity derivation is deliberately host/provisioning-side in v0.3. PNCore does not contain a silent substitute for SHA-256.

The raw 32-byte `GENESIS_ANCHOR` is provisioning material. It is read from a file and must not be committed to Git or written into the build receipt. The record stores only its commitment and derived `CRYSTAL_ID`.

The configuration binding avoids final-ROM self-reference. `PNROM_CODE_BINDING` hashes an ordered manifest of code/build inputs while explicitly excluding the PNVH and T36 identity templates. PNVH basis/vector/source are bound separately by the T36 record.

### 1. Assemble code objects that do not depend on binary templates

```text
as --32 -o build/pnrom_reset.o arch/x86_64/pnrom/pnrom_reset.S
as --32 -o build/pnrom_longmode.o arch/x86_64/pnrom/pnrom_longmode.S
as --32 -o build/pncore_entry.o arch/x86_64/pncore/pncore_entry.S
as --32 -o build/t36_identity.o arch/x86_64/pncore/t36_identity.S
as --32 -o build/t36_identity_boot_entry.o arch/x86_64/pncore/t36_identity_boot_entry.S
as --32 -o build/pnscheduler.o arch/x86_64/pncore/pnscheduler.S
as --32 -o build/pnclock.o arch/x86_64/pncore/pnclock.S
as --32 -o build/pnstore_media.o arch/x86_64/pncore/pnstore_media.S
as --32 -o build/pnr_genesis.o arch/x86_64/pncore/pnr_genesis.S
as --32 -o build/pnr_t36_identity_extension.o arch/x86_64/pncore/pnr_t36_identity_extension.S
```

### 2. Derive non-circular code and PNR bindings

```text
python tools/pnrom_code_binding_v01.py \
  --input RESET=build/pnrom_reset.o \
  --input LONGMODE=build/pnrom_longmode.o \
  --input PNCORE=build/pncore_entry.o \
  --input T36_IDENTITY=build/t36_identity.o \
  --input T36_BOOT=build/t36_identity_boot_entry.o \
  --input SCHEDULER=build/pnscheduler.o \
  --input CLOCK=build/pnclock.o \
  --input PNSTORE=build/pnstore_media.o \
  --input PNR1=build/pnr_genesis.o \
  --input T36X=build/pnr_t36_identity_extension.o \
  --input LINKER=arch/x86_64/pnrom/pnrom.ld \
  --out-binding build/x86_64/pnrom_code_binding.bin \
  --receipt provenance/PNROM_CODE_BINDING_RECEIPT_V0_1.json

python tools/pnr_t36_binding_v01.py \
  --pnr-genesis-object build/pnr_genesis.o \
  --t36-extension-object build/pnr_t36_identity_extension.o \
  --out-binding build/x86_64/pnr_t36_binding.bin \
  --receipt provenance/PNR_T36_BINDING_RECEIPT_V0_1.json
```

Historical PNR1 program and scheduler bindings currently embedded in `pnr_genesis.S` are:

```text
PROGRAM_BINDING   4dd5960aad4ade9029859147c90db5b2f4fc83353407786e66e6476279ca8974
SCHEDULER_BINDING bd6e79f11468a3d5e244b8df4ada6e3b7494187caa971cad0a26ea16cad38c34
```

### 3. Build the exact 256-byte identity record

```text
python tools/t36_identity_builder_v01.py \
  --pnvh build/x86_64/pnvector_handoff_test.bin \
  --genesis-anchor-file <private-or-provisioned-32-byte-anchor.bin> \
  --pnrom-code-binding-file build/x86_64/pnrom_code_binding.bin \
  --pnr-binding-file build/x86_64/pnr_t36_binding.bin \
  --program-binding-hex 4dd5960aad4ade9029859147c90db5b2f4fc83353407786e66e6476279ca8974 \
  --scheduler-binding-hex bd6e79f11468a3d5e244b8df4ada6e3b7494187caa971cad0a26ea16cad38c34 \
  --out build/x86_64/t36_identity_test.bin \
  --receipt provenance/T36_IDENTITY_BUILD_RECEIPT_V0_1.json
```

### 4. Assemble the exact binary templates

```text
as --32 -o build/pnvh_template.o arch/x86_64/pncore/pnvh_template.S
as --32 -o build/t36_identity_template.o arch/x86_64/pncore/t36_identity_template.S
```

### 5. Link v0.3 PNROM

```text
ld -m elf_i386 -T arch/x86_64/pnrom/pnrom.ld \
  -o build/pnrom_v0_3.elf \
  build/pnrom_reset.o build/pnrom_longmode.o build/pncore_entry.o \
  build/t36_identity.o build/t36_identity_boot_entry.o \
  build/pnscheduler.o build/pnclock.o build/pnstore_media.o \
  build/pnr_genesis.o build/pnr_t36_identity_extension.o \
  build/pnvh_template.o build/t36_identity_template.o
objcopy -O binary --gap-fill 0xff build/pnrom_v0_3.elf build/pnrom_v0_3.bin
```

Required ROM size remains exactly 65536 bytes. Reset vector begins at offset `0xFFF0`.

## T36 boot admission

PNROM materializes:

```text
PNVH  -> 0x5000 (416 bytes)
T36I  -> 0x5900 (256 bytes)
```

Before `pncore_entry`, `t36_identity_boot_entry` requires:

- exact T36 record geometry,
- low admission flag bits `0x7`,
- exact equality of T36 record PNVH vector digest with PNVH header,
- exact source-context equality,
- exact basis-binding equality,
- scratch proof `spinor_sheet 0 -> 1 -> 0`,
- exact two-tick `four_pi_closed` under unchanged crystal/configuration/boot epoch.

Failure halts before the existing PNCore transition spine.

## PNR extension

Historical `PNR1` bytes remain unchanged. v0.3 adds a separate 48-byte `T36X` extension containing the T36 working address and physical function bindings. Persistent device continuation and bare-metal State Memory bindings remain zero until their own admission gates are implemented.

## Existing physical components

The harmonic scheduler remains one monotonic tick source plus O(1) trailing-zero band classification. PN Clock retains exact-rational 7.83 Hz TSC-deadline admission. PNStore retains immutable generation preparation, alternating HEAD publication, exactly-once lookup and the explicit durable-barrier contract.

## Evidence boundary

Host derivation/assembly conformance is separate from QEMU, physical boot and device persistence. A successful object assembly or exact binary record build must not be reported as physical boot evidence.
