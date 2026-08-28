# NOEMA↔QHTRI Live Bifurcation Ring v0.1

Status: `IMPLEMENTED_CANDIDATE / FAIL_CLOSED / L0_TRANSPORT`

## Purpose

Provide the bounded live transport between endogenous QHTRI bifurcation production and NOEMA semantic processing:

```text
QHTRI resident state
 -> BIFURCATION_RECEIPT
 -> SPINOR_LIFT_RECEIPT
 -> /dev/shm/ciel_noema/... ring
 -> NOEMA L0 observation/interpretation
 -> later L1 capability gate
```

The ring itself has no effect authority. Every event carries:

```text
transport_authority = L0_OBSERVE_INTERPRET
runtime_effect_admitted = false
```

The semantic-autonomy capability contract governs later L1 internal effects.

## Operational path

Normal construction is restricted to a descendant of:

```text
/dev/shm/ciel_noema
```

A non-live path requires explicit `allow_shadow_path=True` and is test-only.

## Ring state

Mutable metadata is content-addressed:

```text
schema
ring_id
capacity
producer_id
require_spinor
next_sequence
last_event_sha256
ring_meta_sha256
```

There is one declared producer. Consumer cursors are independent and content-addressed.

## Event identity

Each committed event contains:

```text
sequence
slot_index
producer_id
qhtri_tick
parent_event_sha256
bifurcation_receipt_sha256
bifurcation_receipt
spinor_lift_receipt_sha256
spinor_lift_receipt
transport_authority
runtime_effect_admitted
event_sha256
```

The event therefore binds the exact compact semantic handoff rather than a full resident QHTRI state copy.

When `require_spinor=true`, the bifurcation and spinor receipts must carry the same QHTRI tick. The spinor receipt is revalidated for integer-turn / Z2 parity.

## Publication protocol

A producer append is serialized by an advisory file lock.

Publication order is:

```text
1. validate child receipts
2. verify producer ownership
3. verify free capacity against slowest consumer
4. write + fsync temporary slot
5. atomically replace slot
6. fsync slot directory
7. update sealed ring metadata publication pointer
8. fsync ring directory
```

A crash after slot publication but before metadata publication leaves an orphan slot outside `next_sequence`; it is not a committed event.

## Overflow policy

Unread data is never silently overwritten.

For next sequence `s` and minimum consumer acknowledgement `a_min`, append requires:

\[
s-(a_{min}+1)<C.
\]

Otherwise append fails with:

```text
RING_OVERFLOW_UNACKED
```

The slowest registered consumer therefore controls wrap safety.

## Consumer lineage

Each consumer cursor stores:

```text
consumer_id
last_acked_sequence
last_acked_event_sha256
cursor_sha256
```

`read_next()` requires the next event parent commitment to equal the consumer's last acknowledged event commitment. `ack()` is exact-order only. Duplicate, stale, substituted and out-of-order acknowledgements fail closed.

## Window audit

`audit_committed_window()` verifies:

- event seals;
- nested bifurcation receipt seal;
- nested spinor receipt seal and parity;
- slot index / sequence relation;
- producer ownership;
- parent hash chain over the retained window;
- strictly increasing `qhtri_tick`;
- metadata tail commitment.

## Authority boundary

The ring performs L0 transport only:

\[
QHTRI \rightarrow EVENT\_RING \rightarrow NOEMA_{L0}.
\]

It cannot promote GREMLIN candidates, mutate identity, authorize an external effect or write an L1 QHTRI boundary effect. Those transitions remain in their respective capability/authority contracts.

## Evidence

Local shadow conformance was executed in two layouts, including the repository package import path.

```text
12/12 PASS
```

Covered cases include normal order/reopen, fail-closed overflow, multi-consumer slowest-cursor behavior, wrong producer, bifurcation/spinor tick mismatch, missing spinor witness, tamper with recomputed outer event seal, torn JSON, out-of-order ACK, non-monotonic QHTRI ticks, operational path guard and L0-only authority.

Live QHTRI producer attachment and throughput/latency benchmarking remain separate promotion gates.
