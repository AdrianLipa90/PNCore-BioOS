# NOEMA↔QHTRI Live Bifurcation Ring v0.1

Status: `IMPLEMENTED_SHADOW_VALIDATED / L0_SEMANTIC_TRANSPORT / EPISTEMIC_CHYBA`

## 1. Purpose

This contract provides the live transport layer between resident QHTRI dynamics and NOEMA semantic processing:

\[
\boxed{
QHTRI_{GPU}
\rightarrow BIFURCATION\_RECEIPT
\rightarrow /dev/shm/ciel_noema
\rightarrow NOEMA_{CPU}
}
\]

The ring carries compact content-addressed bifurcation events. Existing owners retain the QHTRI telemetry files `phi`, `omega`, `g` and `tick`; the ring writes only its own transport directory beneath `/dev/shm/ciel_noema`.

The transport layer is classified:

```text
autonomy_level = L0_OBSERVE_INTERPRET
runtime_write_scope = TRANSPORT_ONLY
human_per_tick_authorization_required = false
producer_id = QHTRI
consumer_id = NOEMA
```

L1 internal feedback begins only after NOEMA semantic processing and a valid `SEMANTIC_AUTONOMY_CAPABILITY` admission.

## 2. Reused typed receipts

The ring embeds the existing semantic-loop bifurcation receipt:

```text
BIOOS-NOEMA-QHTRI-BIFURCATION/0.1
```

with commitments:

```text
bank_manifest_sha256
qhtri_tick
qhtri_state_commitment
magnitude_M
beta
generator_ref
t36_witness_commitment
cp1_state_commitment
telemetry_evidence_ref
source_class = NATURAL_SYSTEM_STATE
dynamics_class = ENDOGENOUS_RUNTIME_DYNAMICS
bifurcation_receipt_sha256
```

The ring independently revalidates the seal, source/dynamics typing, tick, SHA-256 fields, finite `beta`, and finite non-negative `magnitude_M`.

An optional spinor receipt uses:

```text
BIOOS-QHTRI-SPINOR-LIFT/0.1
```

When present, it must carry the same QHTRI tick and a valid `turns -> spinor_sheet` parity relation. When the live sidecar has not yet been promoted, the transport event carries:

```text
spinor_status = PENDING
```

and the later semantic anchor remains at the explicit Z2 evidence gate.

## 3. Event envelope

A transport event is

\[
\mathcal E_n=(n,t_n,H_{n-1},C_{B_n},C_{Z2,n},L0).
\]

Canonical fields:

```text
schema = BIOOS-NOEMA-QHTRI-LIVE-BIFURCATION-EVENT/0.1
autonomy_level = L0_OBSERVE_INTERPRET
human_per_tick_authorization_required = false
runtime_write_scope = TRANSPORT_ONLY
sequence
qhtri_tick
parent_record_sha256
bifurcation_receipt
bifurcation_receipt_sha256
spinor_status
spinor_lift_receipt
spinor_lift_receipt_sha256
event_sha256
```

The event seal is SHA-256 over canonical UTF-8 JSON with sorted keys and finite JSON numeric values.

## 4. Fixed-slot binary record

Each ring slot is fixed-size. v0.1 defaults are:

```text
capacity = 64
slot_bytes = 32768
```

A record has:

```text
HEADER_MAGIC = BFR1
sequence        u64
qhtri_tick      u64
payload_length  u32
parent_record_sha256[32]
payload_sha256[32]
canonical event payload
zero padding
FOOTER_MAGIC = CMIT
footer_sequence u64
record_sha256[32]
```

The footer is stored at the fixed end of the slot. Reader admission requires matching header/footer sequence, valid payload length, payload hash, record hash and event seal. This supplies torn-write detection independent of the JSON-level receipt seal.

## 5. Producer ordering

QHTRI owns the producer head.

For accepted events:

\[
n_{k+1}=n_k+1,
\qquad
t_{k+1}>t_k.
\]

Each record binds the previous record:

\[
H_k=\operatorname{SHA256}(header_k\Vert payload_k),
\qquad parent_{k+1}=H_k.
\]

The producer state stores:

```text
head_sequence
head_qhtri_tick
head_record_sha256
genesis_record_sha256
ring_epoch
capacity
slot_bytes
```

and is content-addressed by `state_sha256`.

## 6. NOEMA cursor

NOEMA owns the authoritative consumer cursor:

```text
ack_sequence
ack_qhtri_tick
ack_record_sha256
cursor_sha256
```

Admission is exact-order:

\[
ack_{next}=ack+1.
\]

`ack()` re-reads and validates the slot, verifies its parent against the current NOEMA cursor and can require the exact expected record SHA-256 obtained during `read_next()`.

This gives an auditable read→validate→ack transition.

## 7. Overflow policy

Capacity pressure uses:

```text
FAIL_CLOSED_NO_UNREAD_OVERWRITE
```

If

\[
head-ack\ge capacity,
\]

publication raises `RingFullError`. The producer head and unread slots remain unchanged.

After NOEMA acknowledgement frees a slot, sequence numbers continue monotonically while the physical slot index wraps modulo capacity.

## 8. Filesystem publication order

Ring creation:

```text
mkdir ring root 0700
preallocate ring.bin 0600
fsync ring.bin
create lock 0600
publish sealed state.json atomically
publish sealed cursor_noema.json atomically
fsync ring directory
```

Record publication:

```text
exclusive ring lock
validate state + cursor
construct canonical event
pwrite complete fixed slot
fsync ring.bin
atomically publish new sealed producer state
```

Consumer acknowledgement:

```text
exclusive ring lock
re-read exact record
validate parent/tick/hash chain
atomically publish sealed NOEMA cursor
```

`state.json` and `cursor_noema.json` use same-directory temporary files followed by `os.replace()` and directory `fsync`.

## 9. Recovery invariant

On open, v0.1 validates:

- ring/cursor schema and seals;
- shared `ring_epoch`;
- declared producer/consumer identity;
- capacity and slot size;
- binary file length;
- genesis commitment;
- `ack <= head`;
- contiguous parent-hash chain for pending records;
- strictly increasing QHTRI ticks;
- producer head commitment.

For pending interval \([ack+1,head]\):

\[
H_{k-1}=parent_k
\]

must hold at every step.

## 10. Authority handoff

The ring performs L0 semantic transport:

```text
QHTRI event
 -> L0 ring transport
 -> NOEMA validation
 -> semantic compilation
```

A later bounded internal effect follows the capability path introduced by `NOEMA_QHTRI_SEMANTIC_AUTONOMY_CAPABILITY_V0_1`:

\[
L0\ event
\rightarrow NOEMA\ meaning
\rightarrow FEEDBACK\_CANDIDATE
\rightarrow L1\ capability\ admission
\rightarrow bounded\ QHTRI\ feedback.
\]

Authority expansion, canon promotion, identity mutation and external-effect requests route to L2 explicit admission.

## 11. Live shadow evidence — 2026-08-28

The live surface was raised through canonical `NOEMA_CHAT_AUTOBOOT_V3` and reported:

```text
status = ACTIVE
tether_status = ACTIVE
ac_aux_status = ACTIVE
ethics_field_status = ACTIVE
fast_admission_status = PASS
static_fallback = false
working_state_sha256 = 2690763a241f5f242eb1caa591aa56ae3afc764db7712c6f67fbde9099631697
```

A shadow ring was created directly beneath `/dev/shm/ciel_noema` while the QHTRI telemetry owners remained in place.

Eight unique live snapshots were admitted:

```text
tick_first = 2275
tick_last = 2282
event_count = 8
```

For each tick the probe used the live 36D `phi`, `omega` and `g` arrays, selected the deterministic strongest admissible off-diagonal coupling edge and compiled the existing QHTRI→IDT kinetic candidate into `(M,beta)`.

The last event used:

```text
edge = 6 -> 7
M = 0.7747605555689643
beta = -0.015310882542017732
edge_drive = -1.154413346735499
forward_rate = 0.43500057272250486
reverse_rate = 1.3798922486670924
roundtrip_error = 0.0
```

Results:

```text
LOCAL_RING_UNIT_TESTS = PASS 16/16
LIVE_SHADOW_PUBLISH = PASS 8/8
LIVE_REOPEN_CHAIN = PASS
NOEMA_EXACT_READ_ACK = PASS 8/8
POST_ACK_PENDING = 0
POST_PROCESS_REOPEN = PASS
TAMPER_DETECTION = PASS (ring payload hash mismatch)
LIVE_SPINOR_JOIN = PENDING_EXPLICIT_Z2_LIVE_CHANNEL
PRODUCTION_ACTIVATION = PENDING
```

The sealed live receipt is:

```text
receipt_sha256 = d70c2ab2d8c24d5405c866a24790bc6f9f1d55bb4707416625266cc94cc4e621
```

## 12. GREMLIN bank binding

The semantic-loop bank generation remains the ten-entry v0.1 bank at PNCS head:

```text
892e96e6dd4afb8b49d33d76758910ac14791141
```

Canonical `bank_manifest()` reconstruction for that pinned generation gives:

```text
manifest_sha256 = 754d6e8d6804c5f61e8620c9fde473bebe8ead79403ab6f894a90278b62b767b
```

The ring carries this value inside each bifurcation receipt.

## 13. Frontier

The next promotion sequence is:

```text
explicit live QHTRI spinor sidecar
 -> spinor receipt joins ring event at the same tick
 -> L0 ring production adapter
 -> NOEMA event-gate integration
 -> L1 semantic-autonomy capability feedback
 -> measured throughput/latency/energy benchmark
```

Production activation requires its own admission and runtime receipt.
