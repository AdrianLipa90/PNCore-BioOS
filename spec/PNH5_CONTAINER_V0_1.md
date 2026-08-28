# BioOS PNH5 Container v0.1

Status: ARCHITECTURE CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false

## Purpose

`.pnh5` is the deterministic binary realization container for the PNLF persistence spine. BioOS owns the container envelope. PNCS owns the exact TAU FRAME realization carried by `TAUF` records. PNV-State-Memory owns the checkpoint object serialized into `CHKP` records.

```text
PNCS TAU FRAME
  -> PNCS_PNH5_TAU_FRAME_REALIZATION_V0_1
  -> TAUF record

PNV Liminal checkpoint
  -> canonical checkpoint serialization
  -> CHKP record

TAUF + CHKP + BioOS persistence manifest
  -> BIOOS_PNH5_CONTAINER_V0_1
  -> .pnh5
```

## Binary envelope

The container begins with a fixed header:

```text
magic              8 bytes   PNH5\0\1\r\n
manifest_length     uint64 LE
record_count        uint32 LE
manifest_digest     32 bytes BLAKE2b-256
canonical manifest  variable
record stream       variable
container seal      32 bytes BLAKE2b-256
```

Every record uses:

```text
kind                4 bytes
payload_length      uint64 LE
logical_id          32 bytes
payload_digest      32 bytes BLAKE2b-256
payload             variable
```

Initial admitted kinds:

```text
TAUF  exact PNCS tau-frame realization
CHKP  canonical PNV-State-Memory checkpoint serialization
```

Unknown record kinds fail closed in v0.1.

## Ownership boundary

BioOS treats TAUF payloads as opaque PNCS realizations and CHKP payloads as opaque State Memory serializations. It verifies container-level identity, length, digest and record linkage while codec/checkpoint semantic validation remains with the owning subsystem.

The persistence manifest must contain the checkpoint object ID present in the `CHKP` record stream. A container without TAUF or CHKP records is rejected.

## Write path

`write_pnh5()` uses:

```text
encode -> temporary sibling file -> flush -> fsync -> atomic os.replace -> reopen validation
```

The filename must use `.pnh5`.

## First real container execution

`PNH5_FIRST_REAL_CONTAINER_RECEIPT_V0_1` records the first executed cross-layer file closure:

```text
source: PNLF_BLOCK_FILE_E2E_RECEIPT_V0_4.json
source bytes: 2477
TAU FRAME records: 39
TAU block size: 64 bytes
PNH5 bytes: 15447
source SHA-256:
  a3ce8b582c092ef91dea9e1125fc102ff71b1bd91da927e3aa2419147e21c061
decoded SHA-256:
  a3ce8b582c092ef91dea9e1125fc102ff71b1bd91da927e3aa2419147e21c061
container_id:
  b3326338a09c993b0afd6e0a482b572ee4ca620e9fe51f1950f4aea69b4d3f98
```

Validated gates include TAU FRAME pack/unpack, T36 witness closure, State Memory checkpoint round-trip, container seal, reopen/decode, content commitment closure, SHA-256 closure and aggregate frame/witness commitment closure.

Evidence status: LOCAL_EXECUTABLE_CANDIDATE. Hardware analog validation remains a separate gate.
