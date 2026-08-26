# PNStore Media Realization v0.1

Status: IMPLEMENTED CANDIDATE / BYTE-EXACT MEDIA CORE

PNStore Media Realization binds the logical PNStore commit contract to an exact bounded block-image format while leaving hardware I/O behind an explicit backend capability boundary.

## Geometry

```text
media bytes      65536
sector bytes       512
superblock       0x0000..0x01ff
HEAD_A           0x0200..0x03ff
HEAD_B           0x0400..0x05ff
reserved         0x0600..0x0fff
generation log   0x1000..0xffff
extent bytes       4096
max generations      15
```

Generation `g` uses extent offset `g * 4096`, for `1 <= g <= 15`.

## Superblock

The superblock contains magic/version, exact geometry, alternating-HEAD flag and a CRC32C over bytes `[0,508)`. CRC32C uses the Castagnoli polynomial.

## Generation extent

Each immutable generation extent contains:

```text
magic/version
generation
parent_generation
transition_id[32]
object_digest[32]
payload_length
flags
payload
...
commit seal at byte 4032
```

The commit seal binds the generation and stores CRC32C over bytes `[0,4032)`, plus a second CRC32C over the first 60 bytes of the seal.

A prepared extent without a published valid HEAD is not current state.

## Alternating HEAD

Odd generations publish to `HEAD_A`; even generations publish to `HEAD_B`.

A HEAD contains sequence/generation, referenced extent offset, extent data CRC, transition identity, object digest and its own CRC32C. Recovery validates both HEAD slots and referenced extents, then selects the newest valid generation. A torn newer HEAD or corrupt newer extent therefore falls back to the previous valid HEAD.

## Exactly-once transition identity

Exactly-once lookup scans the bounded committed immutable history, not only the current HEAD. A replay of any already committed `transition_id` returns the original generation/extent and performs no mutation.

## Durability ordering

The media core deliberately separates extent preparation from HEAD publication:

```text
prepare immutable extent
 -> DURABLE_BARRIER
 -> publish alternating HEAD
 -> DURABLE_BARRIER
```

`DURABLE_BARRIER` is a backend capability. RAM writes do not satisfy this requirement.

## Backend boundary

A device realization must provide:

```text
READ_EXTENT
APPEND_EXTENT
DURABLE_BARRIER
HEAD_SLOT_WRITE
```

The first implementation validates byte semantics against an fsync-backed host block image. Device binding status: **PENDING**; the next realization gate is a bounded NVMe/AHCI backend capability.

## Failure policy

```text
invalid superblock             -> fail closed
invalid/torn current HEAD      -> recover previous valid HEAD
invalid referenced extent      -> reject that HEAD
prepared unreferenced tail     -> not current
log capacity exhausted         -> fail closed
replayed committed transition  -> return existing generation
```
