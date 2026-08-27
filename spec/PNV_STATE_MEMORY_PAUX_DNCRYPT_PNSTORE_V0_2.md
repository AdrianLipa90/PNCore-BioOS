# PNV State Memory -> PAUX -> DNCrypt -> PNStore v0.2

Status: IMPLEMENTED CROSS-REPO CONVERGENCE CANDIDATE / CHYBA / canon_allowed=false

## Source authorities

- PNV-State-Memory: `feat/pnv-state-memory-paux-exact-bridge`
  - `paux_exact.py` Git blob `73296bbced19d269dbb9309ecda47b12af07692f`
  - State Memory owns checkpoint identity, lineage, receipt and reconstruction validation.
- DNCrypt: `feat/dncrypt-v0.4-binary-envelope`
  - source head at binding creation `88439967b97d4d607ab2c7d30211f91e1fe87a72`
  - DNCrypt owns authenticated encryption, provenance receipt and binary envelope representation.
- PNStore media core:
  - `arch/x86_64/pncore/pnstore_media.S`
  - Git blob `e1df76a6adcda3e98234d23da76cec93ebff9f9c`
  - PNStore owns extent commit, alternating HEAD publication, exactly-once transition identity and recovery.

## Canonical persistence path

```text
live AUX phi[36]
  -> PNV-State-Memory checkpoint
  -> State Memory AUX binding + receipt
  -> PAUX-EXACT: 36 x float64-le = 288 bytes
  -> authenticated reconstruction descriptor in DNCrypt AAD
  -> DNCrypt authenticated envelope
  -> DNCrypt binary-envelope/v0.1
  -> PNStore generation extent
  -> DURABLE_BARRIER
  -> alternating HEAD
```

Recovery:

```text
PNStore recover
  -> exact encrypted payload bytes
  -> DNCrypt binary unpack
  -> DNCrypt provenance receipt verify
  -> BioOS expected AAD exact-match
  -> AEAD decrypt
  -> exact 288-byte PAUX-EXACT
  -> PNV-State-Memory reconstruction
  -> exact object_id + integrity_hash + state_id
  -> State Memory binding/receipt validation
```

## Reconstruction descriptor

The authenticated AAD carries the information required to reproduce and validate the logical State Memory identity from the compact physical phase payload:

- profile, dimension and dtype
- `object_id`
- `integrity_hash`
- `state_id`
- `parent_id`
- relation
- geometry
- metadata
- state label used by canonical checkpoint serialization
- State Memory AUX binding
- State Memory receipt
- SHA-256 of exact PAUX bytes
- persistence context / PNCAP binding where applicable

The PNStore object digest binds the canonical PNV object identity; the DNCrypt binary envelope receives its independent representation identity.

## Extent result

A direct live-source witness on `/dev/shm/ciel_noema/aux_phi` produced:

```text
PAUX plaintext              288 bytes
authenticated AAD          1374 bytes
DNCrypt binary envelope    2672 bytes
PNStore payload limit      3936 bytes
extent utilization        67.886 %
```

The earlier whole-checkpoint serialization experiment exceeded one PNStore extent. The v0.2 convergence profile therefore carries the exact PAUX payload physically and carries logical reconstruction/lineage context as authenticated metadata.

## Native PNStore witness

The exact GitHub assembly blob was compiled as an x86_64 host-linked shared object and executed directly. It passed:

- media format and superblock verification
- immutable generation preparation
- alternating dual HEAD publication/recovery
- exactly-once transition replay
- unpublished prepared-tail safety
- extent-tamper fallback
- HEAD-tamper fallback
- byte identity against the independent host model for generation 1 and 2

This witness validates the media-core assembly semantics on the host CPU. PNROM/bare-metal execution remains a separate convergence gate.

## Live witness

Receipt: `provenance/BIOOS_LIVE_AUX_STATE_MEMORY_PAUX_DNCRYPT_NATIVE_PNSTORE_V0_2.json`.

The live source was read with fresh ACTIVE AUX/tether heartbeats. The test used an isolated session-local State Memory root. Canonical live source bytes and persistent authority roots remained unchanged.

## Current runtime gate

The persistence/recovery chain is admitted at the component/conformance level. Full PNCS resident live admission additionally requires the canonical working-state artifacts `session/fast_admission.json` and `ac_aux_status.json`. Their producer must be an admitted runtime component with explicit provenance.
