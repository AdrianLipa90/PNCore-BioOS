# DN36 <-> DNCrypt auxiliary authenticated binding v0.1

Status: `IMPLEMENTED_AUXILIARY_BINDING_CANDIDATE / CHYBA / canon_allowed=false`

## Purpose

Bind the experimental DN36 fundamental vector commitment to the existing BioOS DNCrypt persistence path without changing cryptographic authority, canonical object identity, or PNStore durability semantics.

DN36 remains an auxiliary structural commitment. DNCrypt remains responsible for authenticated encryption and provenance. Standard hashes remain the authoritative digest/identity layer where already specified.

## Source pins

DN36 construction sources:

- DNCrypt main: `20f53a9b297b6208d74841aee7c3bb4b8b17ce2a`
- TIR main: `45b54c0c8aa60ec92607e6132b69aca9ab766d75`
- Resonant-Chemistry main: `6a9f21678ba4f07e5bdbb1a98a0cafe5c4838697`

BioOS DN36 implementation:

- `tools/dn36_fundamental_vector_commit_v01.py`
- `native/dn36/dn36_v01.c`
- `spec/DN36_FUNDAMENTAL_VECTOR_COMMIT_V0_1.md`

Existing DNCrypt persistence boundary:

- `spec/DNCRYPT_INTEGRATION_BOUNDARY_V0_1.md`
- `spec/DNCRYPT_BINARY_ENVELOPE_BIND_V0_1.md`
- `spec/PNV_STATE_MEMORY_PAUX_DNCRYPT_PNSTORE_V0_2.md`

## Authority firewall

The following identities and gates are unchanged:

```text
PNV_STATE_OBJECT.object_id        -> canonical logical identity
DNCrypt AEAD tag                  -> confidentiality/integrity authority for encrypted envelope
DNCrypt provenance receipt        -> crypto-envelope provenance authority
BioOS expected-user-AAD equality  -> requested-context equality gate
PNStore CRC/seal/HEAD ordering     -> media integrity and durability ordering
standard digest fields             -> authoritative digest fields where already specified
```

DN36 MUST NOT replace any of them.

```text
DN36 identity_authority = false
DN36 aead_authority = false
DN36 security_claim = false
DN36 canon_allowed = false
```

## Non-circular AAD construction

The DNCrypt caller AAD is split into a canonical `core` and a derived DN36 auxiliary extension.

Let:

```text
C = canonical_json(aad_core)
P = PAUX_EXACT plaintext bytes
```

For the current State-Memory convergence profile:

```text
len(P) = 288 bytes = 36 x float64-le
```

The DN36 binding input is:

```text
"BIOOS/DN36/DNCRYPT-AUX/V0.1\0"
|| uint32_be(len(P)) || P
|| uint32_be(len(C)) || C
```

DN36 is evaluated over that byte string. The resulting auxiliary record contains:

- SHA-256 of exact PAUX bytes;
- SHA-256 of canonical AAD core;
- SHA-256 of exact DN36 binding input;
- SHA-256 of the 2304-bit DN36 state;
- experimental DN36 `fold256`;
- independent standard BLAKE2b-256 DN36 anchor;
- explicit authority/firewall flags.

The final authenticated caller AAD is then:

```json
{
  "schema": "BIOOS_DNCRYPT_USER_AAD_WITH_DN36_AUX_V0_1",
  "core": { "...": "..." },
  "dn36_aux": { "...": "derived record" }
}
```

The `core` MUST NOT already contain `dn36_aux`. This prevents recursive/self-referential commitment construction.

## Persistence route

```text
verified PNV_STATE_OBJECT
 -> exact PAUX representation P
 -> canonical reconstruction/context AAD core C
 -> DN36 auxiliary commitment over (P,C)
 -> canonical final user_aad = {core, dn36_aux}
 -> existing BioOS expected-AAD equality policy
 -> DNCrypt AEAD envelope
 -> DNCrypt provenance receipt
 -> PNStore CREATE/COMMIT
 -> durable barrier
 -> HEAD publication
 -> durable barrier
```

No DNCrypt frozen protocol primitive is changed by this binding.

## Recovery route

```text
PNStore payload
 -> DNCrypt binary envelope verification
 -> DNCrypt provenance receipt PASS
 -> existing expected authenticated user_aad exact-match gate
 -> DNCrypt AEAD decrypt PASS
 -> exact PAUX verification
 -> parse canonical DN36-augmented user_aad
 -> recompute DN36 auxiliary record from decrypted PAUX + authenticated AAD core
 -> exact auxiliary-record equality
 -> PNV-State-Memory object/lineage reconstruction gates
```

A DN36 mismatch blocks this candidate recovery path, but a DN36 PASS never substitutes for AEAD, expected-AAD equality, PAUX verification, object identity, lineage, or PNStore integrity.

## Failure semantics

Fail closed on:

- non-canonical authenticated AAD encoding;
- missing or wrong AAD schema;
- PAUX payload not exactly 288 bytes for this profile;
- caller `expected_core` mismatch;
- any mutation of PAUX, AAD core, or DN36 auxiliary record;
- attempt to self-embed `dn36_aux` inside the AAD core.

## Evidence boundary

The initial binding tests establish deterministic construction and fail-closed recomputation behavior only. They do not establish cryptographic strength of DN36, and they do not change DNCrypt's own evidence class.

The DN36 Python/C parity and native timing gates are separate evidence. Independent cryptanalysis remains required before any security role may be considered.

## Promotion boundary

Promotion requires, at minimum:

```text
DN36 auxiliary binding unit/adversarial tests PASS
existing DNCrypt regression PASS
exact final-user-AAD byte identity PASS
actual DNCrypt encrypt/decrypt roundtrip with augmented AAD PASS
PAUX reconstruction/object identity PASS
PNStore capacity recorded after augmented AAD is used
no regression to existing persistence path
canon_allowed remains false unless separately authorized
```
