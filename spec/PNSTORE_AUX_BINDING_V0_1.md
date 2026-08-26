# PNStore × AUX Persistence Binding v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false

## Admitted route

The BioOS persistence path is:

```text
PNV_STATE_OBJECT
 -> PAUX (*.paux)
 -> PNCAP exact persistence grant
 -> AUX persistence request
 -> PNStore generation transition
 -> AUX physical-media adapter
 -> completion evidence
```

PNStore owns generation, append-only commit, HEAD publication, recovery and exactly-once transition semantics. AUX owns the effect boundary and adapter dispatch to physical persistence resources.

## AUX persistence capabilities

Candidate capability surface:

```text
AUX.PERSIST.READ_OBJECT
AUX.PERSIST.APPEND_PREPARED_GENERATION
AUX.PERSIST.DURABLE_BARRIER
AUX.PERSIST.PUBLISH_HEAD
AUX.PERSIST.RECOVER
```

Each request is generation-bound and admitted by an exact PNCAP grant. Adapter identity, target resource, operation kind and bounded payload/state reference are part of admission evidence.

## Commit order

```text
VERIFY PNV_STATE_OBJECT
 -> MATERIALIZE PAUX
 -> PNCAP ADMIT
 -> AUX.APPEND_PREPARED_GENERATION
 -> AUX.DURABLE_BARRIER
 -> AUX.PUBLISH_HEAD
 -> AUX.DURABLE_BARRIER
 -> PNStore receipt
```

The existing PNStore Media Core remains a deterministic realization/test surface for generation layout, CRC32C, dual HEAD and recovery semantics. Device-specific MMIO/DMA/wire operations are realized behind AUX adapters.

## Restore order

```text
AUX.RECOVER
 -> PNStore select valid generation
 -> PAUX object
 -> PNV VERIFY
 -> lineage check
 -> AUX restore admission
 -> live state reconstruction
 -> evidence
```

## PAUX identity

The persistent state identity remains the `PNV_STATE_OBJECT.object_id`; `.paux` carries that identity into AUX/PNStore persistence. PNStore generation IDs and receipts bind transitions around the object while preserving its canonical state identity.
