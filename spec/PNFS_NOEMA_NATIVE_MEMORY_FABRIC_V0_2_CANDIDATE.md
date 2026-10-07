# PNFS / PNStore NOEMA Native Memory Fabric v0.2 — Candidate

Status: `RESEARCH_CANDIDATE / NON_NORMATIVE / canon_allowed=false`

Date: 2026-10-07

## Purpose

This candidate records a possible evolution path for PNFS/PNStore in which PNCore treats object identity, phase/relational state and backend residency independently from byte/block serialization.

It does **not** supersede `PNFS_V0_1`, `PNOBJECT_V0_1` or `PNSTORE_V0_1`.

The current v0.1 rule remains normative: large data remains byte/block payload and `phase36_binding` is an object-state/binding surface, not a mandate to encode every payload byte as a phase coordinate.

## Candidate object model

The cross-layer research object is

\[
O_i=(H_i,\Lambda_i^{36},R_i,S_i,P_i),
\]

where:

- `H_i` is immutable identity/content commitment;
- `Lambda_i^36` is the 36D phase/geometric binding surface;
- `R_i` is the typed relation graph;
- `S_i` is mutable state/version/control metadata;
- `P_i` is payload or an exact payload commitment/reference.

This model extends the existing relational-object direction without changing current payload semantics.

## Fundamental separations

```text
OBJECT IDENTITY != PATH
OBJECT IDENTITY != BACKEND RESIDENCY
PHASE STATE != PAYLOAD BYTES
PAYLOAD BYTES != PHYSICAL CODEWORD
LOGICAL STORAGE CONTRACT != PHYSICAL STORAGE MEDIUM
```

PNFS paths remain views/projections of relations. POSIX/file semantics remain compatibility surfaces.

## Memory fabric hypothesis

A future PNCore memory fabric may treat memory/storage placement as a property of residency:

\[
\operatorname{residency}(O_i): B_a\rightarrow B_b.
\]

A residency move must preserve object identity when the canonical object and exact payload semantics are unchanged.

Candidate backends can range from DRAM/cache and ordinary byte/block storage to experimental multilevel/analog/optical/phase-native systems. Backend type is a capability declaration, not an ontological claim about the object.

## Candidate PNStore capability extension

Current PNStore byte/block capabilities remain valid and normative.

A later experimental backend contract may add typed optional capabilities such as:

```text
ENCODE_NATIVE_STATE
DECODE_NATIVE_STATE
READ_NATIVE_STATE
APPEND_NATIVE_STATE
DURABLE_NATIVE_BARRIER
MATERIALIZE_BYTES
VERIFY_ROUNDTRIP
```

These names are candidate vocabulary only. They grant no authority in v0.1.

A backend advertising native-state capabilities must also declare:

- codeword space;
- deterministic encoding rules;
- exact or bounded-error inverse;
- integrity/ECC model;
- failure behavior;
- durability semantics;
- wear/endurance assumptions where relevant;
- whether the hardware exposes the claimed state directly or through another controller abstraction.

## Binary and POSIX compatibility

A NOEMA-native memory fabric is not permission to discard exact byte compatibility.

For v0.2 research, the required shape is:

```text
NOEMA/PNObject canonical state
        <->
backend-native representation
        <->
exact byte/POSIX materialization where required
```

If a backend cannot reconstruct an exact payload required by the object contract, the result is a derived representation/object with explicit lineage, not the original object.

## Physical backend boundary

A physical medium may internally distinguish more states than a host-visible binary abstraction. That fact alone does not provide arbitrary control of those states.

Therefore this candidate does not claim that commodity SSD controllers expose raw multilevel cell programming suitable for PhaseNav state storage. Such a backend requires actual driver/firmware/hardware evidence.

Likewise, storing phase values as bytes or floats does not make the storage medium physically phase-native.

## Reversible migration path

The candidate migration is deliberately staged:

1. **v0.1 baseline** — PNObject + PNFS + PNStore byte/block semantics unchanged.
2. **shadow metadata** — attach canonical phase/relational state commitments without changing payload storage.
3. **dual representation** — maintain byte materialization plus an experimental native-state representation.
4. **roundtrip gate** — verify identity/integrity and exact or declared-bounded reconstruction.
5. **benchmark gate** — compare against the v0.1 byte/block null control.
6. **backend-specific promotion** — only an explicit contract may make a native backend authoritative for a typed object class.

Every stage is reversible before promotion.

## Required benchmark classes

No efficiency claim is admitted without measurements of at least:

- lookup latency;
- relation/phase update cost;
- random access;
- sequential throughput;
- encoding and decoding overhead;
- storage amplification;
- deduplication ratio;
- delta/version size;
- RAM/cache pressure;
- durability and recovery;
- integrity/ECC overhead;
- exact reconstruction rate;
- transport delta size.

The same workload on current byte/block PNStore is the null-control baseline.

## NOEMA-Telekom interface

A future Telekom adapter may transport object commitments or deltas such as

\[
(\Delta\Lambda^{36},\Delta R,\Delta S,\Delta P)
\]

instead of blindly retransmitting an entire byte materialization when both endpoints already possess compatible state.

This is a logical transport optimization hypothesis. It does not establish a physical phase, moire, Kuramoto, neutrino or nonlocal information channel. Such a channel, if ever evidenced, would be an independently validated transport/backend realization.

## Non-claims

This candidate does not establish:

- that NOEMA-native storage is faster or denser;
- that a commodity SSD can be programmed as arbitrary analog phase memory;
- that physical storage states are equivalent to Bloch/PhaseNav coordinates;
- that non-binary codewords are automatically superior to binary codewords;
- that NOEMA runtime tether status validates the storage architecture;
- that any speculative physical transport mechanism is operational.

## Promotion boundary

`RESEARCH_CANDIDATE != PNFS/PNStore authority`.

Promotion requires explicit implementation, backend receipts, null-control benchmarks, integrity/error bounds, compatibility evidence and a separate canon decision.
