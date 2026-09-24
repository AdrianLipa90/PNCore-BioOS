from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import fcntl
import hashlib
import json
import math
import os
import struct
import tempfile
import uuid

RING_SCHEMA = "BIOOS-NOEMA-QHTRI-LIVE-BIFURCATION-RING/0.1"
STATE_SCHEMA = "BIOOS-NOEMA-QHTRI-LIVE-BIFURCATION-RING-STATE/0.1"
CURSOR_SCHEMA = "BIOOS-NOEMA-QHTRI-LIVE-BIFURCATION-RING-CURSOR/0.1"
EVENT_SCHEMA = "BIOOS-NOEMA-QHTRI-LIVE-BIFURCATION-EVENT/0.1"
BIFURCATION_SCHEMA = "BIOOS-NOEMA-QHTRI-BIFURCATION/0.1"
SPINOR_SCHEMA = "BIOOS-QHTRI-SPINOR-LIFT/0.1"

AUTONOMY_LEVEL = "L0_OBSERVE_INTERPRET"
RUNTIME_WRITE_SCOPE = "TRANSPORT_ONLY"
SOURCE_CLASS = "NATURAL_SYSTEM_STATE"
DYNAMICS_CLASS = "ENDOGENOUS_RUNTIME_DYNAMICS"

HEADER_MAGIC = b"BFR1"
FOOTER_MAGIC = b"CMIT"
HEADER = struct.Struct("<4sQQI32s32s")
FOOTER = struct.Struct("<4sQ32s")
DEFAULT_CAPACITY = 64
DEFAULT_SLOT_BYTES = 32768
MIN_SLOT_BYTES = HEADER.size + FOOTER.size + 512


class BifurcationRingError(RuntimeError):
    pass


class RingFullError(BifurcationRingError):
    pass


class RingCorruptionError(BifurcationRingError):
    pass


class RingOrderingError(BifurcationRingError):
    pass


@dataclass(frozen=True)
class RingRecord:
    sequence: int
    qhtri_tick: int
    parent_record_sha256: str
    payload_sha256: str
    record_sha256: str
    event: dict[str, Any]


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256(value: Any) -> str:
    return _sha256_bytes(_canonical_bytes(value))


def _hex64(value: Any, name: str) -> str:
    text = str(value)
    if len(text) != 64:
        raise BifurcationRingError(f"{name} must be 64 hex characters")
    try:
        bytes.fromhex(text)
    except ValueError as exc:
        raise BifurcationRingError(f"{name} must be hexadecimal") from exc
    return text.lower()


def _nonnegative_int(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise BifurcationRingError(f"{name} must be an integer")
    try:
        integer = int(value)
    except (TypeError, ValueError) as exc:
        raise BifurcationRingError(f"{name} must be an integer") from exc
    if integer != value or integer < 0:
        raise BifurcationRingError(f"{name} must be a non-negative integer")
    return integer


def _positive_int(value: Any, name: str) -> int:
    integer = _nonnegative_int(value, name)
    if integer < 1:
        raise BifurcationRingError(f"{name} must be positive")
    return integer


def _text(value: Any, name: str) -> str:
    text = str(value).strip()
    if not text:
        raise BifurcationRingError(f"{name} is required")
    return text


def _seal(body: Mapping[str, Any], key: str) -> dict[str, Any]:
    if key in body:
        raise BifurcationRingError(f"seal key already present: {key}")
    return {**dict(body), key: _sha256(body)}


def _verify_seal(value: Mapping[str, Any], key: str) -> None:
    if key not in value:
        raise RingCorruptionError(f"missing seal: {key}")
    body = {k: v for k, v in value.items() if k != key}
    if value[key] != _sha256(body):
        raise RingCorruptionError(f"seal mismatch: {key}")


def _validate_bifurcation_receipt(receipt: Mapping[str, Any], expected_tick: int) -> str:
    if receipt.get("schema") != BIFURCATION_SCHEMA:
        raise BifurcationRingError("invalid bifurcation receipt schema")
    tick = _nonnegative_int(receipt.get("qhtri_tick"), "bifurcation qhtri_tick")
    if tick != expected_tick:
        raise RingOrderingError("bifurcation receipt tick does not match event tick")
    if receipt.get("source_class") != SOURCE_CLASS:
        raise BifurcationRingError("bifurcation source class mismatch")
    if receipt.get("dynamics_class") != DYNAMICS_CLASS:
        raise BifurcationRingError("bifurcation dynamics class mismatch")
    for field in (
        "bank_manifest_sha256",
        "qhtri_state_commitment",
        "t36_witness_commitment",
        "cp1_state_commitment",
    ):
        _hex64(receipt.get(field), field)
    try:
        magnitude = float(receipt.get("magnitude_M"))
        beta = float(receipt.get("beta"))
    except (TypeError, ValueError) as exc:
        raise BifurcationRingError("bifurcation magnitude_M and beta must be numeric") from exc
    if not math.isfinite(magnitude) or magnitude < 0.0:
        raise BifurcationRingError("bifurcation magnitude_M must be finite and non-negative")
    if not math.isfinite(beta):
        raise BifurcationRingError("bifurcation beta must be finite")
    _text(receipt.get("generator_ref"), "generator_ref")
    _text(receipt.get("telemetry_evidence_ref"), "telemetry_evidence_ref")
    seal = _hex64(receipt.get("bifurcation_receipt_sha256"), "bifurcation_receipt_sha256")
    body = {k: v for k, v in receipt.items() if k != "bifurcation_receipt_sha256"}
    if seal != _sha256(body):
        raise RingCorruptionError("bifurcation receipt seal mismatch")
    return seal


def _validate_spinor_receipt(receipt: Mapping[str, Any], expected_tick: int) -> str:
    if receipt.get("schema") != SPINOR_SCHEMA:
        raise BifurcationRingError("invalid spinor lift receipt schema")
    tick = _nonnegative_int(receipt.get("qhtri_tick"), "spinor qhtri_tick")
    if tick != expected_tick:
        raise RingOrderingError("spinor receipt tick does not match event tick")
    if receipt.get("source_class") != SOURCE_CLASS:
        raise BifurcationRingError("spinor source class mismatch")
    if receipt.get("dynamics_class") != DYNAMICS_CLASS:
        raise BifurcationRingError("spinor dynamics class mismatch")
    seal = _hex64(receipt.get("spinor_lift_receipt_sha256"), "spinor_lift_receipt_sha256")
    body = {k: v for k, v in receipt.items() if k != "spinor_lift_receipt_sha256"}
    if seal != _sha256(body):
        raise RingCorruptionError("spinor lift receipt seal mismatch")
    if not receipt.get("turns") or not receipt.get("spinor_sheet"):
        raise BifurcationRingError("spinor receipt requires turns and spinor_sheet")
    if len(receipt["turns"]) != len(receipt["spinor_sheet"]):
        raise BifurcationRingError("spinor turns/sheet cardinality mismatch")
    for turns, sheet in zip(receipt["turns"], receipt["spinor_sheet"]):
        expected = 1 if int(turns) % 2 == 0 else -1
        if int(sheet) != expected:
            raise BifurcationRingError("spinor turns/sheet parity mismatch")
    return seal


def build_transport_event(
    *,
    sequence: int,
    parent_record_sha256: str,
    qhtri_tick: int,
    bifurcation_receipt: Mapping[str, Any],
    spinor_lift_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    seq = _positive_int(sequence, "sequence")
    tick = _nonnegative_int(qhtri_tick, "qhtri_tick")
    parent = _hex64(parent_record_sha256, "parent_record_sha256")
    bif_hash = _validate_bifurcation_receipt(bifurcation_receipt, tick)
    if spinor_lift_receipt is None:
        spinor_status = "PENDING"
        spinor_payload = None
        spinor_hash = None
    else:
        spinor_status = "PRESENT"
        spinor_payload = dict(spinor_lift_receipt)
        spinor_hash = _validate_spinor_receipt(spinor_lift_receipt, tick)

    body = {
        "schema": EVENT_SCHEMA,
        "autonomy_level": AUTONOMY_LEVEL,
        "human_per_tick_authorization_required": False,
        "runtime_write_scope": RUNTIME_WRITE_SCOPE,
        "authority_expansion": False,
        "external_effect": False,
        "canon_promotion": False,
        "identity_layer_mutation": False,
        "sequence": seq,
        "qhtri_tick": tick,
        "parent_record_sha256": parent,
        "bifurcation_receipt": dict(bifurcation_receipt),
        "bifurcation_receipt_sha256": bif_hash,
        "spinor_status": spinor_status,
        "spinor_lift_receipt": spinor_payload,
        "spinor_lift_receipt_sha256": spinor_hash,
    }
    return _seal(body, "event_sha256")


def validate_transport_event(event: Mapping[str, Any]) -> None:
    if event.get("schema") != EVENT_SCHEMA:
        raise RingCorruptionError("event schema mismatch")
    if event.get("autonomy_level") != AUTONOMY_LEVEL:
        raise RingCorruptionError("event autonomy level mismatch")
    if event.get("human_per_tick_authorization_required") is not False:
        raise RingCorruptionError("L0 transport cannot require per-tick authorization")
    if event.get("runtime_write_scope") != RUNTIME_WRITE_SCOPE:
        raise RingCorruptionError("event runtime write scope mismatch")
    for forbidden in ("authority_expansion", "external_effect", "canon_promotion", "identity_layer_mutation"):
        if event.get(forbidden) is not False:
            raise RingCorruptionError(f"L0 transport crossed {forbidden} boundary")
    seq = _positive_int(event.get("sequence"), "sequence")
    tick = _nonnegative_int(event.get("qhtri_tick"), "qhtri_tick")
    _hex64(event.get("parent_record_sha256"), "parent_record_sha256")
    bif = event.get("bifurcation_receipt")
    if not isinstance(bif, Mapping):
        raise RingCorruptionError("event bifurcation receipt missing")
    bif_hash = _validate_bifurcation_receipt(bif, tick)
    if event.get("bifurcation_receipt_sha256") != bif_hash:
        raise RingCorruptionError("event bifurcation commitment mismatch")
    status = event.get("spinor_status")
    if status == "PENDING":
        if event.get("spinor_lift_receipt") is not None or event.get("spinor_lift_receipt_sha256") is not None:
            raise RingCorruptionError("PENDING spinor status carries spinor payload")
    elif status == "PRESENT":
        spinor = event.get("spinor_lift_receipt")
        if not isinstance(spinor, Mapping):
            raise RingCorruptionError("PRESENT spinor status missing receipt")
        spinor_hash = _validate_spinor_receipt(spinor, tick)
        if event.get("spinor_lift_receipt_sha256") != spinor_hash:
            raise RingCorruptionError("event spinor commitment mismatch")
    else:
        raise RingCorruptionError("invalid spinor status")
    _verify_seal(event, "event_sha256")


class LiveBifurcationRing:
    def __init__(self, root: str | os.PathLike[str]) -> None:
        self.root = Path(root)
        self.ring_path = self.root / "ring.bin"
        self.state_path = self.root / "state.json"
        self.cursor_path = self.root / "cursor_noema.json"
        self.lock_path = self.root / ".lock"

    @staticmethod
    def _genesis_hash(*, ring_epoch: str, capacity: int, slot_bytes: int) -> str:
        return _sha256(
            {
                "schema": RING_SCHEMA,
                "ring_epoch": ring_epoch,
                "capacity": capacity,
                "slot_bytes": slot_bytes,
                "producer_id": "QHTRI",
                "consumer_id": "NOEMA",
            }
        )

    @classmethod
    def create(
        cls,
        root: str | os.PathLike[str],
        *,
        capacity: int = DEFAULT_CAPACITY,
        slot_bytes: int = DEFAULT_SLOT_BYTES,
        ring_epoch: str | None = None,
    ) -> "LiveBifurcationRing":
        cap = _positive_int(capacity, "capacity")
        slotsz = _positive_int(slot_bytes, "slot_bytes")
        if slotsz < MIN_SLOT_BYTES:
            raise BifurcationRingError(f"slot_bytes must be >= {MIN_SLOT_BYTES}")
        obj = cls(root)
        obj.root.mkdir(parents=True, exist_ok=False)
        os.chmod(obj.root, 0o700)
        epoch = _text(ring_epoch or uuid.uuid4().hex, "ring_epoch")
        genesis = obj._genesis_hash(ring_epoch=epoch, capacity=cap, slot_bytes=slotsz)

        fd = os.open(obj.ring_path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.ftruncate(fd, cap * slotsz)
            os.fsync(fd)
        finally:
            os.close(fd)
        lock_fd = os.open(obj.lock_path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(lock_fd)

        state = _seal(
            {
                "schema": STATE_SCHEMA,
                "ring_schema": RING_SCHEMA,
                "ring_epoch": epoch,
                "capacity": cap,
                "slot_bytes": slotsz,
                "producer_id": "QHTRI",
                "consumer_id": "NOEMA",
                "head_sequence": 0,
                "head_qhtri_tick": None,
                "head_record_sha256": genesis,
                "genesis_record_sha256": genesis,
            },
            "state_sha256",
        )
        cursor = _seal(
            {
                "schema": CURSOR_SCHEMA,
                "ring_epoch": epoch,
                "consumer_id": "NOEMA",
                "ack_sequence": 0,
                "ack_qhtri_tick": None,
                "ack_record_sha256": genesis,
            },
            "cursor_sha256",
        )
        obj._atomic_json(obj.state_path, state)
        obj._atomic_json(obj.cursor_path, cursor)
        obj._fsync_dir()
        obj.validate_metadata()
        return obj

    @classmethod
    def open(cls, root: str | os.PathLike[str], *, verify_pending_chain: bool = True) -> "LiveBifurcationRing":
        obj = cls(root)
        obj.validate_metadata()
        if verify_pending_chain:
            obj.verify_pending_chain()
        return obj

    def _fsync_dir(self) -> None:
        fd = os.open(self.root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def _atomic_json(self, path: Path, payload: Mapping[str, Any]) -> None:
        data = _canonical_bytes(payload) + b"\n"
        fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=self.root)
        try:
            os.fchmod(fd, 0o600)
            view = memoryview(data)
            offset = 0
            while offset < len(view):
                written = os.write(fd, view[offset:])
                if written <= 0:
                    raise BifurcationRingError("short atomic metadata write")
                offset += written
            os.fsync(fd)
        finally:
            os.close(fd)
        try:
            os.replace(tmp_name, path)
            self._fsync_dir()
        except Exception:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass
            raise

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        try:
            raw = path.read_bytes()
            value = json.loads(raw)
        except Exception as exc:
            raise RingCorruptionError(f"cannot parse metadata: {path.name}") from exc
        if not isinstance(value, dict):
            raise RingCorruptionError(f"metadata must be object: {path.name}")
        return value

    def _lock(self, exclusive: bool):
        fd = os.open(self.lock_path, os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        return fd

    @staticmethod
    def _unlock(fd: int) -> None:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

    def _load_state(self) -> dict[str, Any]:
        state = self._load_json(self.state_path)
        if state.get("schema") != STATE_SCHEMA or state.get("ring_schema") != RING_SCHEMA:
            raise RingCorruptionError("ring state schema mismatch")
        _verify_seal(state, "state_sha256")
        return state

    def _load_cursor(self) -> dict[str, Any]:
        cursor = self._load_json(self.cursor_path)
        if cursor.get("schema") != CURSOR_SCHEMA:
            raise RingCorruptionError("ring cursor schema mismatch")
        _verify_seal(cursor, "cursor_sha256")
        return cursor

    def validate_metadata(self) -> None:
        if not self.root.is_dir() or not self.ring_path.is_file() or not self.lock_path.is_file():
            raise RingCorruptionError("ring filesystem layout incomplete")
        state = self._load_state()
        cursor = self._load_cursor()
        if state.get("ring_epoch") != cursor.get("ring_epoch"):
            raise RingCorruptionError("state/cursor epoch mismatch")
        if state.get("producer_id") != "QHTRI" or state.get("consumer_id") != "NOEMA":
            raise RingCorruptionError("ring ownership mismatch")
        if cursor.get("consumer_id") != "NOEMA":
            raise RingCorruptionError("cursor ownership mismatch")
        cap = _positive_int(state.get("capacity"), "capacity")
        slotsz = _positive_int(state.get("slot_bytes"), "slot_bytes")
        if slotsz < MIN_SLOT_BYTES:
            raise RingCorruptionError("slot size below minimum")
        if self.ring_path.stat().st_size != cap * slotsz:
            raise RingCorruptionError("ring file size mismatch")
        head = _nonnegative_int(state.get("head_sequence"), "head_sequence")
        ack = _nonnegative_int(cursor.get("ack_sequence"), "ack_sequence")
        if ack > head:
            raise RingCorruptionError("cursor is ahead of producer head")
        if head - ack > cap:
            raise RingCorruptionError("pending range exceeds ring capacity")
        genesis = self._genesis_hash(ring_epoch=state["ring_epoch"], capacity=cap, slot_bytes=slotsz)
        if state.get("genesis_record_sha256") != genesis:
            raise RingCorruptionError("genesis commitment mismatch")
        if head == 0:
            if state.get("head_qhtri_tick") is not None or state.get("head_record_sha256") != genesis:
                raise RingCorruptionError("empty ring head metadata mismatch")
        else:
            _nonnegative_int(state.get("head_qhtri_tick"), "head_qhtri_tick")
            _hex64(state.get("head_record_sha256"), "head_record_sha256")
        if ack == 0:
            if cursor.get("ack_qhtri_tick") is not None or cursor.get("ack_record_sha256") != genesis:
                raise RingCorruptionError("genesis cursor metadata mismatch")
        else:
            _nonnegative_int(cursor.get("ack_qhtri_tick"), "ack_qhtri_tick")
            _hex64(cursor.get("ack_record_sha256"), "ack_record_sha256")

    def _slot_offset(self, sequence: int, capacity: int, slot_bytes: int) -> int:
        return ((sequence - 1) % capacity) * slot_bytes

    @staticmethod
    def _pwrite_all(fd: int, data: bytes, offset: int) -> None:
        view = memoryview(data)
        total = 0
        while total < len(view):
            written = os.pwrite(fd, view[total:], offset + total)
            if written <= 0:
                raise BifurcationRingError("short ring write")
            total += written

    @staticmethod
    def _pread_exact(fd: int, size: int, offset: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < size:
            part = os.pread(fd, size - len(chunks), offset + len(chunks))
            if not part:
                break
            chunks.extend(part)
        if len(chunks) != size:
            raise RingCorruptionError("short ring read")
        return bytes(chunks)

    def publish(
        self,
        *,
        qhtri_tick: int,
        bifurcation_receipt: Mapping[str, Any],
        spinor_lift_receipt: Mapping[str, Any] | None = None,
    ) -> RingRecord:
        lock_fd = self._lock(True)
        try:
            state = self._load_state()
            cursor = self._load_cursor()
            cap = int(state["capacity"])
            slotsz = int(state["slot_bytes"])
            head = int(state["head_sequence"])
            ack = int(cursor["ack_sequence"])
            if head - ack >= cap:
                raise RingFullError("ring is full; unread events are never overwritten")
            tick = _nonnegative_int(qhtri_tick, "qhtri_tick")
            if head > 0 and tick <= int(state["head_qhtri_tick"]):
                raise RingOrderingError("qhtri_tick must be strictly increasing")
            sequence = head + 1
            parent = _hex64(state["head_record_sha256"], "head_record_sha256")
            event = build_transport_event(
                sequence=sequence,
                parent_record_sha256=parent,
                qhtri_tick=tick,
                bifurcation_receipt=bifurcation_receipt,
                spinor_lift_receipt=spinor_lift_receipt,
            )
            payload = _canonical_bytes(event)
            payload_hash = _sha256_bytes(payload)
            max_payload = slotsz - HEADER.size - FOOTER.size
            if len(payload) > max_payload:
                raise BifurcationRingError(
                    f"event payload {len(payload)} exceeds slot capacity {max_payload}"
                )
            header = HEADER.pack(
                HEADER_MAGIC,
                sequence,
                tick,
                len(payload),
                bytes.fromhex(parent),
                bytes.fromhex(payload_hash),
            )
            record_hash = _sha256_bytes(header + payload)
            footer = FOOTER.pack(FOOTER_MAGIC, sequence, bytes.fromhex(record_hash))
            slot = header + payload + bytes(max_payload - len(payload)) + footer
            if len(slot) != slotsz:
                raise BifurcationRingError("internal slot size mismatch")
            fd = os.open(self.ring_path, os.O_RDWR)
            try:
                offset = self._slot_offset(sequence, cap, slotsz)
                self._pwrite_all(fd, slot, offset)
                os.fsync(fd)
            finally:
                os.close(fd)
            new_state = _seal(
                {
                    **{k: v for k, v in state.items() if k != "state_sha256"},
                    "head_sequence": sequence,
                    "head_qhtri_tick": tick,
                    "head_record_sha256": record_hash,
                },
                "state_sha256",
            )
            self._atomic_json(self.state_path, new_state)
            return RingRecord(sequence, tick, parent, payload_hash, record_hash, event)
        finally:
            self._unlock(lock_fd)

    def _read_record_locked(self, sequence: int, state: Mapping[str, Any]) -> RingRecord:
        cap = int(state["capacity"])
        slotsz = int(state["slot_bytes"])
        seq = _positive_int(sequence, "sequence")
        fd = os.open(self.ring_path, os.O_RDONLY)
        try:
            slot = self._pread_exact(fd, slotsz, self._slot_offset(seq, cap, slotsz))
        finally:
            os.close(fd)
        header = slot[: HEADER.size]
        footer = slot[-FOOTER.size :]
        try:
            magic, stored_seq, tick, payload_len, parent_raw, payload_hash_raw = HEADER.unpack(header)
            foot_magic, foot_seq, record_hash_raw = FOOTER.unpack(footer)
        except struct.error as exc:
            raise RingCorruptionError("cannot unpack ring record") from exc
        if magic != HEADER_MAGIC or foot_magic != FOOTER_MAGIC:
            raise RingCorruptionError("torn/uncommitted ring record magic")
        if stored_seq != seq or foot_seq != seq:
            raise RingCorruptionError("ring sequence/footer mismatch")
        max_payload = slotsz - HEADER.size - FOOTER.size
        if payload_len < 1 or payload_len > max_payload:
            raise RingCorruptionError("ring payload length invalid")
        payload = slot[HEADER.size : HEADER.size + payload_len]
        payload_hash = _sha256_bytes(payload)
        if payload_hash != payload_hash_raw.hex():
            raise RingCorruptionError("ring payload hash mismatch")
        record_hash = _sha256_bytes(header + payload)
        if record_hash != record_hash_raw.hex():
            raise RingCorruptionError("ring record hash mismatch")
        try:
            event = json.loads(payload)
        except Exception as exc:
            raise RingCorruptionError("ring event JSON invalid") from exc
        if not isinstance(event, dict):
            raise RingCorruptionError("ring event payload must be object")
        if _canonical_bytes(event) != payload:
            raise RingCorruptionError("ring event payload is not canonical JSON")
        validate_transport_event(event)
        parent = parent_raw.hex()
        if event.get("sequence") != seq or event.get("qhtri_tick") != tick:
            raise RingCorruptionError("event/header sequence or tick mismatch")
        if event.get("parent_record_sha256") != parent:
            raise RingCorruptionError("event/header parent commitment mismatch")
        return RingRecord(seq, int(tick), parent, payload_hash, record_hash, event)

    def read_next(self) -> RingRecord | None:
        lock_fd = self._lock(False)
        try:
            state = self._load_state()
            cursor = self._load_cursor()
            head = int(state["head_sequence"])
            ack = int(cursor["ack_sequence"])
            if ack == head:
                return None
            sequence = ack + 1
            record = self._read_record_locked(sequence, state)
            if record.parent_record_sha256 != cursor["ack_record_sha256"]:
                raise RingCorruptionError("next event parent does not match NOEMA cursor")
            if ack > 0 and record.qhtri_tick <= int(cursor["ack_qhtri_tick"]):
                raise RingCorruptionError("next event tick is not strictly increasing")
            return record
        finally:
            self._unlock(lock_fd)

    def ack(self, sequence: int, *, expected_record_sha256: str | None = None) -> dict[str, Any]:
        lock_fd = self._lock(True)
        try:
            state = self._load_state()
            cursor = self._load_cursor()
            expected_sequence = int(cursor["ack_sequence"]) + 1
            seq = _positive_int(sequence, "sequence")
            if seq != expected_sequence:
                raise RingOrderingError(f"ack must be exact next sequence {expected_sequence}")
            if seq > int(state["head_sequence"]):
                raise RingOrderingError("cannot acknowledge beyond producer head")
            record = self._read_record_locked(seq, state)
            if record.parent_record_sha256 != cursor["ack_record_sha256"]:
                raise RingCorruptionError("ack record parent does not match cursor")
            if expected_record_sha256 is not None:
                expected_hash = _hex64(expected_record_sha256, "expected_record_sha256")
                if record.record_sha256 != expected_hash:
                    raise RingCorruptionError("ack record SHA does not match expected SHA")
            if int(cursor["ack_sequence"]) > 0 and record.qhtri_tick <= int(cursor["ack_qhtri_tick"]):
                raise RingCorruptionError("ack tick is not strictly increasing")
            new_cursor = _seal(
                {
                    "schema": CURSOR_SCHEMA,
                    "ring_epoch": cursor["ring_epoch"],
                    "consumer_id": "NOEMA",
                    "ack_sequence": record.sequence,
                    "ack_qhtri_tick": record.qhtri_tick,
                    "ack_record_sha256": record.record_sha256,
                },
                "cursor_sha256",
            )
            self._atomic_json(self.cursor_path, new_cursor)
            return new_cursor
        finally:
            self._unlock(lock_fd)

    def verify_pending_chain(self) -> dict[str, Any]:
        lock_fd = self._lock(False)
        try:
            state = self._load_state()
            cursor = self._load_cursor()
            head = int(state["head_sequence"])
            ack = int(cursor["ack_sequence"])
            parent = cursor["ack_record_sha256"]
            previous_tick = cursor["ack_qhtri_tick"]
            last_record: RingRecord | None = None
            count = 0
            for sequence in range(ack + 1, head + 1):
                record = self._read_record_locked(sequence, state)
                if record.parent_record_sha256 != parent:
                    raise RingCorruptionError("pending chain parent mismatch")
                if previous_tick is not None and record.qhtri_tick <= int(previous_tick):
                    raise RingCorruptionError("pending chain qhtri_tick regression")
                parent = record.record_sha256
                previous_tick = record.qhtri_tick
                last_record = record
                count += 1
            if last_record is not None and last_record.record_sha256 != state["head_record_sha256"]:
                raise RingCorruptionError("producer head commitment does not match pending chain")
            if last_record is None and ack == head and cursor["ack_record_sha256"] != state["head_record_sha256"]:
                raise RingCorruptionError("empty pending range cursor/head commitment mismatch")
            return {
                "schema": RING_SCHEMA,
                "status": "PASS",
                "pending_count": count,
                "ack_sequence": ack,
                "head_sequence": head,
                "head_record_sha256": state["head_record_sha256"],
            }
        finally:
            self._unlock(lock_fd)

    def status(self) -> dict[str, Any]:
        lock_fd = self._lock(False)
        try:
            state = self._load_state()
            cursor = self._load_cursor()
            return {
                "schema": RING_SCHEMA,
                "ring_epoch": state["ring_epoch"],
                "capacity": state["capacity"],
                "slot_bytes": state["slot_bytes"],
                "head_sequence": state["head_sequence"],
                "head_qhtri_tick": state["head_qhtri_tick"],
                "ack_sequence": cursor["ack_sequence"],
                "ack_qhtri_tick": cursor["ack_qhtri_tick"],
                "pending_count": int(state["head_sequence"]) - int(cursor["ack_sequence"]),
                "autonomy_level": AUTONOMY_LEVEL,
                "human_per_tick_authorization_required": False,
                "overflow_policy": "FAIL_CLOSED_NO_UNREAD_OVERWRITE",
            }
        finally:
            self._unlock(lock_fd)
