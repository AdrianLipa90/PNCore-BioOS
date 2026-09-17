# DN36 -> DNCrypt AEAD / binary-envelope capacity gate v0.1

Status: `PENDING_CROSS_REPO_EXECUTION / CHYBA / canon_allowed=false`

The next promotion gate for the DN36 auxiliary binding is an actual execution against the pinned DNCrypt binary-envelope branch.

Required source:

```text
AdrianLipa90/DNCrypt
branch feat/dncrypt-v0.4-binary-envelope
commit 88439967b97d4d607ab2c7d30211f91e1fe87a72
```

Required deterministic sequence:

```text
288-byte PAUX plaintext
 -> BioOS canonical DN36-augmented user_aad
 -> DNCrypt v0.2 encrypt
 -> verify DNCrypt provenance receipt
 -> pack dncrypt.binary-envelope/v0.1
 -> require packed size <= 3936 bytes
 -> unpack
 -> require reconstructed canonical DNCrypt envelope byte identity
 -> decode authenticated DNCrypt outer AAD
 -> require exact embedded BioOS user_aad equality
 -> DNCrypt v0.2 decrypt
 -> require exact 288-byte plaintext equality
```

The capacity gate must record at least:

```text
PAUX bytes
BioOS user_aad bytes
DNCrypt authenticated outer-AAD bytes
ciphertext bytes
packed binary-envelope bytes
remaining PNStore payload margin = 3936 - packed bytes
binary envelope content ID
receipt validity
plaintext roundtrip equality
```

Fail closed if the packed envelope exceeds 3936 bytes. The PNStore extent geometry must not be relaxed to make the candidate pass.

A PASS proves only compatibility of this deterministic candidate with the current DNCrypt binary-envelope and PNStore payload geometry. It does not promote DN36 to cryptographic authority and does not establish cryptographic strength.
