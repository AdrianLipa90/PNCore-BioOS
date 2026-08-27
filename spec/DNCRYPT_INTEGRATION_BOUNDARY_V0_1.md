# DNCrypt Integration Boundary v0.1

Status: CANDIDATE / CHYBA / canon_allowed=false
Source repository: `AdrianLipa90/DNCrypt`
Pinned source commit: `20f53a9b297b6208d74841aee7c3bb4b8b17ce2a`
Pinned native program blob: `native/programs/DNCRYPT_NATIVE_PNCS_V0_3.pnv` @ `99df240db1db020dea24b51b160de90bce727eb2`

## Purpose

Bind DNCrypt to BioOS as a native PNCS encryption boundary while preserving PNObject/PNV identity and lineage.

DNCrypt v0.3 already exposes native PNCS bindings for SHAKE256, BLAKE2B-256, SHA3-256, HKDF-SHA3-512, ChaCha20-Poly1305, 36D genome/surface state, entropy admission, message receipts and resident adaptation.

## Identity rule

Canonical object identity remains the plaintext-state identity:

```text
PNV_STATE_OBJECT.object_id = canonical logical identity
```

Encryption produces a distinct transport/persistence envelope identity:

```text
DNCrypt ciphertext + authenticated metadata -> ENVELOPE_ID
```

`ENVELOPE_ID` must never replace or mutate `PNV_STATE_OBJECT.object_id`.

## Persistence route

```text
verified PNV_STATE_OBJECT
 -> exact PAUX/plaintext representation
 -> PNCAP EXECUTE_PROGRAM admission for pinned DNCrypt program
 -> DNCrypt AEAD envelope
 -> envelope identity + encryption receipt
 -> normal PNStore CREATE/COMMIT generation admission
 -> durable barrier
 -> HEAD publication
 -> durable barrier
 -> persistence receipt
```

Authenticated associated data SHOULD bind at least:

```text
PNV_STATE_OBJECT.object_id
PNV/PAUX generation
PAUX profile
PNCAP execution receipt identity
parent persistence/evolution receipt identity
destination/domain context
```

DNCrypt already authenticates genome generation, 36D surface commitment, tick, parent receipt and caller AAD. BioOS supplies its object/persistence identities through caller AAD rather than changing the DNCrypt frozen AEAD anchor.

## Recovery route

```text
PNStore envelope bytes
 -> DNCrypt envelope/receipt verification
 -> ChaCha20-Poly1305 authentication + decrypt
 -> PAUX profile verification/decode
 -> PNV_STATE_OBJECT identity + integrity verification
 -> admitted logical state
```

Failure at any layer stops recovery. AEAD PASS does not replace PNV/PAUX integrity, and PNV identity does not replace AEAD authentication.

## Transport route

The same envelope profile is a candidate for Terminal36D/off-box transport. The initial v0.1 binding does not require encrypting the local `/dev/shm/ciel_noema` hot path. Local shared-memory encryption remains a separate threat-model/performance decision.

## Capability rule

No new PNCAP opcode/domain is required for the first binding. DNCrypt runs as an admitted native program under `EXECUTE_PROGRAM`; subsequent PNStore effects still require the existing generation-bound persistence capabilities.

## Key boundary

The DNCrypt frozen anchor uses a 256-bit master key. BioOS integration must pass an opaque admitted key handle/reference; plaintext master-key persistence inside PNStore, PNFS paths, receipts, command envelopes or semantic state is forbidden by this candidate contract. Concrete key provisioning/storage is a separate integration gate.

## Evidence boundary

DNCrypt main reports implementation/conformance prototype status and independent cryptanalytic evaluation remains pending. Therefore DNCrypt integration is optional/candidate in v0.2.9 and is not promoted to mandatory boot/persistence authority by this document.
