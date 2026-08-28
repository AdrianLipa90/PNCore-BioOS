from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

RING_SCHEMA = "BIOOS-NOEMA-QHTRI-LIVE-BIFURCATION-RING/0.1"
EVENT_SCHEMA = "BIOOS-NOEMA-QHTRI-LIVE-BIFURCATION-EVENT/0.1"
CURSOR_SCHEMA = "BIOOS-NOEMA-QHTRI-LIVE-BIFURCATION-CURSOR/0.1"
BIFURCATION_SCHEMA = "BIOOS-NOEMA-QHTRI-BIFURCATION/0.1"
SPINOR_SCHEMA = "BIOOS-QHTRI-SPINOR-LIFT/0.1"

class LiveBifurcationRingError(RuntimeError):
    pass

def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")

def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()

def _seal(body: Mapping[str, Any], key: str) -> dict[str, Any]:
    if key in body:
        raise LiveBifurcationRingError(f"seal key already present: {key}")
    return {**dict(body), key: _sha256(body)}

def _verify_seal(value: Mapping[str, Any], key: str) -> None:
    if key not in value:
        raise LiveBifurcationRingError(f"missing seal: {key}")
    body = {k: v for k, v in value.items() if k != key}
    if value[key] != _sha256(body):
        raise LiveBifurcationRingError(f"seal mismatch: {key}")

def _text(value: Any, name: str) -> str:
    text = str(value).strip()
    if not text:
        raise LiveBifurcationRingError(f"{name} is required")
    return text

def _hex64(value: Any, name: str) -> str:
    text = str(value)
    if len(text) != 64:
        raise LiveBifurcationRingError(f"{name} must be 64 hex characters")
    try:
        bytes.fromhex(text)
    except ValueError as exc:
        raise LiveBifurcationRingError(f"{name} must be hexadecimal") from exc
    return text.lower()

def _nonnegative_int(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise LiveBifurcationRingError(f"{name} must be integer")
    try:
        n = int(value)
    except (TypeError, ValueError) as exc:
        raise LiveBifurcationRingError(f"{name} must be integer") from exc
    if n != value or n < 0:
        raise LiveBifurcationRingError(f"{name} must be non-negative integer")
    return n

def _positive_int(value: Any, name: str) -> int:
    n = _nonnegative_int(value, name)
    if n < 1:
        raise LiveBifurcationRingError(f"{name} must be positive")
    return n

def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            payload = _canonical_bytes(value)
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        dir_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        if tmp.exists():
            tmp.unlink()

def _read_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise LiveBifurcationRingError(f"invalid/torn JSON: {path.name}") from exc
    if not isinstance(value, dict):
        raise LiveBifurcationRingError(f"JSON object required: {path.name}")
    return value

def _validate_bifurcation(receipt: Mapping[str, Any]) -> None:
    if receipt.get("schema") != BIFURCATION_SCHEMA:
        raise LiveBifurcationRingError("invalid bifurcation receipt schema")
    _nonnegative_int(receipt.get("qhtri_tick"), "qhtri_tick")
    _hex64(receipt.get("bifurcation_receipt_sha256"), "bifurcation_receipt_sha256")
    _verify_seal(receipt, "bifurcation_receipt_sha256")

def _validate_spinor(receipt: Mapping[str, Any]) -> None:
    if receipt.get("schema") != SPINOR_SCHEMA:
        raise LiveBifurcationRingError("invalid spinor receipt schema")
    _nonnegative_int(receipt.get("qhtri_tick"), "spinor qhtri_tick")
    turns = tuple(int(x) for x in receipt.get("turns", ()))
    sheet = tuple(int(x) for x in receipt.get("spinor_sheet", ()))
    if not turns or len(turns) != len(sheet):
        raise LiveBifurcationRingError("spinor turns/sheet cardinality mismatch")
    expected = tuple(1 if (x % 2 == 0) else -1 for x in turns)
    if sheet != expected:
        raise LiveBifurcationRingError("spinor sheet parity mismatch")
    _hex64(receipt.get("spinor_lift_receipt_sha256"), "spinor_lift_receipt_sha256")
    _verify_seal(receipt, "spinor_lift_receipt_sha256")

class LiveBifurcationRing:
    def __init__(
        self,
        root: str | Path,
        *,
        capacity: int | None = None,
        producer_id: str | None = None,
        ring_id: str = "NOEMA_QHTRI_BIFURCATION_RING_V0_1",
        require_spinor: bool = True,
        allow_shadow_path: bool = False,
    ) -> None:
        self.root = Path(root)
        if not allow_shadow_path:
            live_root = Path("/dev/shm/ciel_noema").resolve()
            try:
                resolved = self.root.resolve()
            except FileNotFoundError:
                resolved = self.root.absolute()
            if resolved != live_root and live_root not in resolved.parents:
                raise LiveBifurcationRingError("operational ring must live under /dev/shm/ciel_noema")
        self.ring_id = _text(ring_id, "ring_id")
        self.meta_path = self.root / "ring.meta.json"
        self.lock_path = self.root / ".ring.lock"
        self.slots_dir = self.root / "slots"
        self.cursors_dir = self.root / "consumers"
        self.root.mkdir(parents=True, exist_ok=True)
        self.slots_dir.mkdir(exist_ok=True)
        self.cursors_dir.mkdir(exist_ok=True)
        self.lock_path.touch(exist_ok=True)

        if self.meta_path.exists():
            meta = self._read_meta()
            if capacity is not None and _positive_int(capacity, "capacity") != meta["capacity"]:
                raise LiveBifurcationRingError("capacity mismatch with existing ring")
            if producer_id is not None and _text(producer_id, "producer_id") != meta["producer_id"]:
                raise LiveBifurcationRingError("producer ownership mismatch")
            if bool(require_spinor) != bool(meta["require_spinor"]):
                raise LiveBifurcationRingError("require_spinor mismatch with existing ring")
            self.capacity = meta["capacity"]
            self.producer_id = meta["producer_id"]
            self.require_spinor = bool(meta["require_spinor"])
        else:
            if capacity is None or producer_id is None:
                raise LiveBifurcationRingError("new ring requires capacity and producer_id")
            self.capacity = _positive_int(capacity, "capacity")
            self.producer_id = _text(producer_id, "producer_id")
            self.require_spinor = bool(require_spinor)
            body = {
                "schema": RING_SCHEMA,
                "ring_id": self.ring_id,
                "capacity": self.capacity,
                "producer_id": self.producer_id,
                "require_spinor": self.require_spinor,
                "next_sequence": 0,
                "last_event_sha256": "0" * 64,
            }
            _atomic_write_json(self.meta_path, _seal(body, "ring_meta_sha256"))

    def _locked(self):
        class _Lock:
            def __init__(self, path: Path): self.path=path; self.fh=None
            def __enter__(self):
                self.fh=open(self.path, "a+b")
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX)
                return self
            def __exit__(self, *exc):
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
                self.fh.close()
        return _Lock(self.lock_path)

    def _read_meta(self) -> dict[str, Any]:
        meta = _read_json(self.meta_path)
        if meta.get("schema") != RING_SCHEMA or meta.get("ring_id") != self.ring_id:
            raise LiveBifurcationRingError("ring metadata schema/id mismatch")
        _positive_int(meta.get("capacity"), "capacity")
        _text(meta.get("producer_id"), "producer_id")
        _nonnegative_int(meta.get("next_sequence"), "next_sequence")
        _hex64(meta.get("last_event_sha256"), "last_event_sha256")
        if meta.get("require_spinor") not in (True, False):
            raise LiveBifurcationRingError("require_spinor must be boolean")
        _verify_seal(meta, "ring_meta_sha256")
        return meta

    def _slot_path(self, sequence: int) -> Path:
        return self.slots_dir / f"{sequence % self.capacity:08d}.json"

    def _cursor_path(self, consumer_id: str) -> Path:
        safe = _text(consumer_id, "consumer_id")
        if "/" in safe or safe in (".", ".."):
            raise LiveBifurcationRingError("invalid consumer_id")
        return self.cursors_dir / f"{safe}.json"

    def register_consumer(self, consumer_id: str) -> dict[str, Any]:
        with self._locked():
            meta = self._read_meta()
            path = self._cursor_path(consumer_id)
            if path.exists():
                return self._read_cursor(consumer_id)
            oldest = max(0, meta["next_sequence"] - self.capacity)
            last_acked = oldest - 1
            anchor_hash = "0" * 64
            if oldest > 0:
                first = _read_json(self._slot_path(oldest))
                self._validate_event(first, expected_sequence=oldest)
                anchor_hash = first["parent_event_sha256"]
            body = {
                "schema": CURSOR_SCHEMA,
                "ring_id": self.ring_id,
                "consumer_id": _text(consumer_id, "consumer_id"),
                "last_acked_sequence": last_acked,
                "last_acked_event_sha256": anchor_hash,
            }
            cur = _seal(body, "cursor_sha256")
            _atomic_write_json(path, cur)
            return cur

    def _read_cursor(self, consumer_id: str) -> dict[str, Any]:
        path = self._cursor_path(consumer_id)
        if not path.exists():
            raise LiveBifurcationRingError("consumer is not registered")
        cur = _read_json(path)
        if cur.get("schema") != CURSOR_SCHEMA or cur.get("ring_id") != self.ring_id:
            raise LiveBifurcationRingError("cursor schema/id mismatch")
        if cur.get("consumer_id") != consumer_id:
            raise LiveBifurcationRingError("cursor consumer mismatch")
        seq = cur.get("last_acked_sequence")
        if isinstance(seq, bool) or not isinstance(seq, int) or seq < -1:
            raise LiveBifurcationRingError("invalid cursor sequence")
        _hex64(cur.get("last_acked_event_sha256"), "last_acked_event_sha256")
        _verify_seal(cur, "cursor_sha256")
        return cur

    def _minimum_acked(self) -> int:
        cursors = list(self.cursors_dir.glob("*.json"))
        if not cursors:
            return -1
        return min(self._read_cursor(path.stem)["last_acked_sequence"] for path in cursors)

    def append(
        self,
        bifurcation_receipt: Mapping[str, Any],
        *,
        spinor_lift_receipt: Mapping[str, Any] | None = None,
        producer_id: str | None = None,
    ) -> dict[str, Any]:
        _validate_bifurcation(bifurcation_receipt)
        if self.require_spinor and spinor_lift_receipt is None:
            raise LiveBifurcationRingError("spinor lift receipt required")
        if spinor_lift_receipt is not None:
            _validate_spinor(spinor_lift_receipt)
            if spinor_lift_receipt["qhtri_tick"] != bifurcation_receipt["qhtri_tick"]:
                raise LiveBifurcationRingError("bifurcation/spinor tick mismatch")
        owner = self.producer_id if producer_id is None else _text(producer_id, "producer_id")
        if owner != self.producer_id:
            raise LiveBifurcationRingError("producer ownership mismatch")

        with self._locked():
            meta = self._read_meta()
            if meta["producer_id"] != owner:
                raise LiveBifurcationRingError("producer ownership mismatch")
            sequence = meta["next_sequence"]
            occupied = sequence - (self._minimum_acked() + 1)
            if occupied >= self.capacity:
                raise LiveBifurcationRingError("RING_OVERFLOW_UNACKED")
            body = {
                "schema": EVENT_SCHEMA,
                "ring_id": self.ring_id,
                "sequence": sequence,
                "slot_index": sequence % self.capacity,
                "producer_id": owner,
                "qhtri_tick": bifurcation_receipt["qhtri_tick"],
                "parent_event_sha256": meta["last_event_sha256"],
                "bifurcation_receipt_sha256": bifurcation_receipt["bifurcation_receipt_sha256"],
                "bifurcation_receipt": dict(bifurcation_receipt),
                "spinor_lift_receipt_sha256": spinor_lift_receipt["spinor_lift_receipt_sha256"] if spinor_lift_receipt is not None else "",
                "spinor_lift_receipt": dict(spinor_lift_receipt) if spinor_lift_receipt is not None else None,
                "transport_authority": "L0_OBSERVE_INTERPRET",
                "runtime_effect_admitted": False,
            }
            event = _seal(body, "event_sha256")
            _atomic_write_json(self._slot_path(sequence), event)
            new_meta_body = {
                "schema": RING_SCHEMA,
                "ring_id": self.ring_id,
                "capacity": self.capacity,
                "producer_id": self.producer_id,
                "require_spinor": self.require_spinor,
                "next_sequence": sequence + 1,
                "last_event_sha256": event["event_sha256"],
            }
            _atomic_write_json(self.meta_path, _seal(new_meta_body, "ring_meta_sha256"))
            return event

    def _validate_event(self, event: Mapping[str, Any], *, expected_sequence: int | None = None) -> None:
        if event.get("schema") != EVENT_SCHEMA or event.get("ring_id") != self.ring_id:
            raise LiveBifurcationRingError("event schema/id mismatch")
        seq = _nonnegative_int(event.get("sequence"), "sequence")
        if expected_sequence is not None and seq != expected_sequence:
            raise LiveBifurcationRingError("event sequence mismatch")
        if event.get("slot_index") != seq % self.capacity:
            raise LiveBifurcationRingError("slot index mismatch")
        if event.get("producer_id") != self.producer_id:
            raise LiveBifurcationRingError("event producer mismatch")
        _hex64(event.get("parent_event_sha256"), "parent_event_sha256")
        _validate_bifurcation(event.get("bifurcation_receipt", {}))
        if event.get("bifurcation_receipt_sha256") != event["bifurcation_receipt"]["bifurcation_receipt_sha256"]:
            raise LiveBifurcationRingError("bifurcation child commitment mismatch")
        if event.get("qhtri_tick") != event["bifurcation_receipt"]["qhtri_tick"]:
            raise LiveBifurcationRingError("event/bifurcation tick mismatch")
        spinor = event.get("spinor_lift_receipt")
        if spinor is None:
            if self.require_spinor or event.get("spinor_lift_receipt_sha256") != "":
                raise LiveBifurcationRingError("spinor requirement/commitment mismatch")
        else:
            _validate_spinor(spinor)
            if spinor["qhtri_tick"] != event["qhtri_tick"]:
                raise LiveBifurcationRingError("event/spinor tick mismatch")
            if event.get("spinor_lift_receipt_sha256") != spinor["spinor_lift_receipt_sha256"]:
                raise LiveBifurcationRingError("spinor child commitment mismatch")
        if event.get("transport_authority") != "L0_OBSERVE_INTERPRET":
            raise LiveBifurcationRingError("event crossed transport authority boundary")
        if event.get("runtime_effect_admitted") is not False:
            raise LiveBifurcationRingError("event crossed runtime effect boundary")
        _verify_seal(event, "event_sha256")

    def read_next(self, consumer_id: str) -> dict[str, Any] | None:
        with self._locked():
            meta = self._read_meta()
            cur = self._read_cursor(consumer_id)
            sequence = cur["last_acked_sequence"] + 1
            if sequence >= meta["next_sequence"]:
                return None
            if meta["next_sequence"] - sequence > self.capacity:
                raise LiveBifurcationRingError("CONSUMER_FELL_BEHIND")
            path = self._slot_path(sequence)
            if not path.exists():
                raise LiveBifurcationRingError("MISSING_COMMITTED_SLOT")
            event = _read_json(path)
            self._validate_event(event, expected_sequence=sequence)
            if event["parent_event_sha256"] != cur["last_acked_event_sha256"]:
                raise LiveBifurcationRingError("event parent chain mismatch")
            return event

    def ack(self, consumer_id: str, event: Mapping[str, Any]) -> dict[str, Any]:
        with self._locked():
            cur = self._read_cursor(consumer_id)
            self._validate_event(event)
            expected = cur["last_acked_sequence"] + 1
            if event["sequence"] != expected:
                raise LiveBifurcationRingError("ACK_OUT_OF_ORDER")
            current = _read_json(self._slot_path(expected))
            self._validate_event(current, expected_sequence=expected)
            if current["event_sha256"] != event["event_sha256"]:
                raise LiveBifurcationRingError("ACK_EVENT_SUBSTITUTION")
            body = {
                "schema": CURSOR_SCHEMA,
                "ring_id": self.ring_id,
                "consumer_id": consumer_id,
                "last_acked_sequence": expected,
                "last_acked_event_sha256": event["event_sha256"],
            }
            sealed = _seal(body, "cursor_sha256")
            _atomic_write_json(self._cursor_path(consumer_id), sealed)
            return sealed

    def audit_committed_window(self) -> dict[str, Any]:
        with self._locked():
            meta = self._read_meta()
            next_seq = meta["next_sequence"]
            start = max(0, next_seq - self.capacity)
            parent = "0" * 64 if start == 0 else None
            if start > 0:
                first = _read_json(self._slot_path(start))
                self._validate_event(first, expected_sequence=start)
                parent = first["parent_event_sha256"]
            last = parent
            count = 0
            last_tick = None
            for seq in range(start, next_seq):
                event = _read_json(self._slot_path(seq))
                self._validate_event(event, expected_sequence=seq)
                if event["parent_event_sha256"] != last:
                    raise LiveBifurcationRingError("committed window parent mismatch")
                if last_tick is not None and event["qhtri_tick"] <= last_tick:
                    raise LiveBifurcationRingError("QHTRI_TICK_NOT_STRICTLY_INCREASING")
                last_tick = event["qhtri_tick"]
                last = event["event_sha256"]
                count += 1
            if count and last != meta["last_event_sha256"]:
                raise LiveBifurcationRingError("metadata tail commitment mismatch")
            if not count and meta["last_event_sha256"] != "0" * 64:
                raise LiveBifurcationRingError("empty ring has non-genesis tail")
            return {
                "schema": "BIOOS-NOEMA-QHTRI-LIVE-BIFURCATION-RING-AUDIT/0.1",
                "ring_id": self.ring_id,
                "retained_start_sequence": start,
                "next_sequence": next_seq,
                "retained_event_count": count,
                "last_event_sha256": meta["last_event_sha256"],
                "status": "PASS",
            }
