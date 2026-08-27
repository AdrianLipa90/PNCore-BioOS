# PNTERM × Terminal36D V8 Bridge v0.1

Status: IMPLEMENTED CANDIDATE / HASH-PINNED VECTOR ENVIRONMENT
Epistemic operator: CHYBA
Canon promotion: explicit authority only

## Purpose

PNTERM is the bounded terminal/session front-end for BioOS. Terminal36D V8 is the standard 36D vector execution environment used by NOEMA-facing terminal commands.

```text
physical terminal adapter
 -> AUX.TERM.RX
 -> PNTERM line discipline
 -> PNTERM session/envelope
 -> Terminal36D V8 profile admission
 -> Terminal36D action packet
 -> concept gate
 -> PNCAP exact admission for authority-bearing effects
 -> Terminal36D typed primitive
 -> AUX effect boundary when required
 -> execution/evidence receipt
 -> PNTERM result
 -> AUX.TERM.TX
```

The active Terminal36D profile is admitted by exact content hashes, vector dimension 36, capability manifest identity, and current-session tether state. Runtime lookup is hydrated once per TERMINAL_EPOCH and then served from an O(1) operation table.

## Profile pin

The bridge binds Terminal36D V8 by the exact 10-file Library roundtrip hashes recorded in `TERMINAL36D_V8_PROFILE_LOCK_V0_1.json`. The canonical Terminal36D executable source hash is:

```text
terminal36d.py = 78082702c4b7a17a061ca7b9b83f4c21765307c70dfbefd301466224389cce9b
```

The V7 capability manifest is preserved by V8. It exposes 29 typed operations over a 36D vector environment. Missing primitives use `IMPLEMENT_TYPED_VECTORIZED_PRIMITIVE_OR_BLOCK`.

## Command envelope

PNTERM emits a bridge envelope containing:

```text
terminal_epoch
session_id
rx_seq
action_id
operation
payload_ref
intent
principal
capability_ref
profile_lock_sha256
```

`action_id` is content-addressed over the immutable command/session fields. Reuse of an admitted `(session_id, terminal_epoch, rx_seq)` is replay-denied.

## Capability classes

Terminal36D V8 classes operations internally as typed vector/read/write/copy/execute gates. The bridge keeps a separate authority boundary:

```text
READ / VECTORIZE                 -> read-only admission path
EXECUTE_TYPED                    -> exact typed execution admission
WRITE / COPY                     -> exact PNCAP grant + AUX effect admission
```

A high vector similarity, resonance score, relation score, or command spelling match cannot grant authority.

## Standard environment rule

Within NOEMA-facing BioOS terminal execution:

```text
STANDARD_VECTOR_ENVIRONMENT = TERMINAL36D_V8
VECTOR_DIMENSION = 36
VECTORIZE_BY_DEFAULT = TRUE
ACCELERATOR_PROMOTION = EQUIVALENCE_GATED
```

PNTERM does transport, framing, session identity, bounded parsing, deterministic action construction, result framing and evidence transport. Terminal36D owns the typed vector operation registry and execution semantics for this bridge version.

## Runtime continuity

Library is the canonical source for the pinned Terminal36D V8 profile. `/dev/shm/ciel_noema` is the mandatory ephemeral live materialization path for 36D NOEMA execution. A fresh tether guard is required for live execution claims.

## Native BioOS direction

The hash-pinned V8 bridge freezes behavior while BioOS ports typed primitives into PNV/native realization. Native replacement is admitted only by exact operation-level equivalence receipts against this profile.
