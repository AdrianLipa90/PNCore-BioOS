# PNObject v0.1

Status: ARCHITECTURE CANDIDATE

PNObject is the common system object identity. It is intended to replace separate primary identity models for files, processes, resident program images, datasets, checkpoints and device handles.

## Object identity

A logical object owns a stable content-addressed identity namespace:

```text
pnobj:<kind>:sha256:<semantic-payload-digest>
```

A mutable history is represented only by immutable generations:

```text
pnobjgen:sha256:<generation-payload-digest>
```

## Generation Cell

```text
PNObjectGeneration {
  object_id
  generation_id
  parent_generation_id
  kind
  environment_id
  authority_id
  phase36_binding
  relation_set_id
  capability_set_id
  payload_ref
  transition_id
  evidence_id
}
```

`parent_generation_id = ROOT` is admitted only for a genesis object class.

## Initial kinds

```text
PROGRAM
DATA
MEMORY
TRAJECTORY_STORE
DEVICE
VIEW
SYSTEM_STATE
PHYSICAL_RESOURCE
RECEIPT
```

`.pnv` maps naturally to `PROGRAM`.
`.pnh5` maps naturally to `TRAJECTORY_STORE`.

## Payload rule

Large data remains byte/block payload. 36D is the object's state/binding surface, not a mandate to encode every payload byte as float64 phase coordinates.

## Relational rule

Names and paths do not define identity. A directory-like hierarchy is a VIEW over explicit relations among PNObjects.
