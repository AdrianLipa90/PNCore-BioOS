# BioOS <-> DNCrypt Binary Envelope Binding v0.1

Status: IMPLEMENTED BINDING CANDIDATE / CHYBA / canon_allowed=false

## Source pin

Repository: `AdrianLipa90/DNCrypt`
Branch: `feat/dncrypt-v0.4-binary-envelope`
Source head at binding creation: `88439967b97d4d607ab2c7d30211f91e1fe87a72`
Codec: `dncrypt.binary-envelope/v0.1`
Frozen crypto protocol remains `DNCrypt/v0.2` / `dncrypt.frozen-protocol/v0.2`.

GitHub Actions had not reported a workflow run at binding creation; source test promotion is pending.

## Boundary

```text
PNV_STATE_OBJECT
  -> PAUX plaintext representation
  -> PNCAP EXECUTE_PROGRAM
  -> DNCrypt encrypt / authenticated canonical DNCryptEnvelope
  -> DNCrypt binary-envelope codec
  -> PNStore payload bytes
  -> DURABLE_BARRIER
  -> HEAD publication
```

Recovery:

```text
PNStore payload
  -> DNCrypt binary unpack
  -> canonical DNCryptEnvelope byte identity
  -> DNCrypt provenance receipt PASS
  -> BioOS expected authenticated AAD exact-match
  -> DNCrypt AEAD decrypt PASS
  -> PAUX identity/integrity PASS
  -> PNV_STATE_OBJECT identity PASS
```

## Identity separation

`PNV_STATE_OBJECT.object_id` remains canonical system identity.

The encrypted binary representation receives an independent content identity:

```text
dncrypt:binary-envelope:sha256:<digest>
```

Representation identity does not replace, mutate or derive a new PNV object identity.

## PNStore geometry

PNStore v0.1 has:

```text
extent bytes        4096
payload offset        96
commit seal offset  4032
payload max         3936
```

The binary codec is intended to remove canonical-JSON key overhead and base64 expansion at this persistence boundary. Actual capacity limits remain envelope/AAD dependent and must be measured from the committed codec before promotion.

## Ownership

- DNCrypt owns crypto, envelope receipt and binary representation codec.
- PAUX owns state representation and reconstruction validation.
- PNV-State-Memory owns canonical object identity/lineage.
- BioOS/PNStore owns immutable extent persistence and durability ordering.
- PNCAP owns execution permission.

No layer silently substitutes for another.

## Promotion gate

```text
DNCrypt binary codec tests PASS
DNCrypt legacy crypto regression PASS
canonical envelope byte roundtrip PASS
binary tamper rejection PASS
BioOS expected-AAD equality PASS
PAUX/PNV post-decrypt verification PASS
PNStore 3936-byte capacity benchmark recorded
main remains unchanged until explicit merge
```
