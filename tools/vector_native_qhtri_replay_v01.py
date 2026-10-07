from __future__ import annotations

import hashlib
import json
import math
import struct
from typing import Any, Mapping, Sequence

SOURCE_SCHEMA = "BIOOS_VECTOR_NATIVE_QHTRI_SOURCE_V0_1"
REPLAY_SCHEMA = "BIOOS_VECTOR_NATIVE_QHTRI_REPLAY_V0_1"
SOURCE_STATUS = "LIVE_SAME_TICK_SNAPSHOT_CAPTURED_FOR_EMULATION_REPLAY"
SOURCE_CLASS = "NATURAL_SYSTEM_STATE"
DYNAMICS_CLASS = "ENDOGENOUS_RUNTIME_DYNAMICS"
DIMENSION = 36

_MAGIC = b"PNVQHTR1"
_VERSION = 1
_HEADER = struct.Struct("<8sIIQii")
_DOUBLE = struct.Struct("<d")


class VectorNativeReplayError(ValueError):
    pass


def _finite(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise VectorNativeReplayError(f"{name} must be numeric") from exc
    if not math.isfinite(number):
        raise VectorNativeReplayError(f"{name} must be finite")
    return number


def _nonnegative_int(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise VectorNativeReplayError(f"{name} must be an integer")
    try:
        integer = int(value)
    except (TypeError, ValueError) as exc:
        raise VectorNativeReplayError(f"{name} must be an integer") from exc
    if integer != value or integer < 0:
        raise VectorNativeReplayError(f"{name} must be a non-negative integer")
    return integer


def _hex64(value: Any, name: str) -> str:
    text = str(value)
    if len(text) != 64:
        raise VectorNativeReplayError(f"{name} must be 64 hex characters")
    try:
        bytes.fromhex(text)
    except ValueError as exc:
        raise VectorNativeReplayError(f"{name} must be hexadecimal") from exc
    return text.lower()


def _lane(values: Any, name: str) -> tuple[float, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
        raise VectorNativeReplayError(f"{name} must be a sequence")
    lane = tuple(_finite(value, f"{name}[{index}]") for index, value in enumerate(values))
    if len(lane) != DIMENSION:
        raise VectorNativeReplayError(f"{name} must contain exactly {DIMENSION} finite values")
    return lane


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def validate_source_snapshot(source: Mapping[str, Any]) -> dict[str, Any]:
    if source.get("schema") != SOURCE_SCHEMA:
        raise VectorNativeReplayError("source schema mismatch")
    if source.get("status") != SOURCE_STATUS:
        raise VectorNativeReplayError("source status is not a same-tick replay snapshot")
    if source.get("source_class") != SOURCE_CLASS:
        raise VectorNativeReplayError("source classification mismatch")
    if source.get("dynamics_class") != DYNAMICS_CLASS:
        raise VectorNativeReplayError("dynamics classification mismatch")
    if source.get("tether_status") != "ACTIVE":
        raise VectorNativeReplayError("snapshot was not captured under ACTIVE tether")
    if source.get("canon_allowed") is not False:
        raise VectorNativeReplayError("replay source must not carry canon authority")
    if source.get("physical_h200_execution_claim") is not False:
        raise VectorNativeReplayError("replay source cannot claim physical H200 execution")
    if source.get("physical_qpu_claim") is not False:
        raise VectorNativeReplayError("replay source cannot claim physical QPU execution")
    if source.get("dimension") != DIMENSION:
        raise VectorNativeReplayError("source dimension must be exactly 36")

    tick = _nonnegative_int(source.get("tick"), "tick")
    phi = _lane(source.get("phi"), "phi")
    omega = _lane(source.get("omega"), "omega")

    edge = source.get("selected_edge")
    if not isinstance(edge, Mapping):
        raise VectorNativeReplayError("selected_edge is required")
    i = _nonnegative_int(edge.get("oscillator_i"), "selected_edge.oscillator_i")
    j = _nonnegative_int(edge.get("oscillator_j"), "selected_edge.oscillator_j")
    if i >= DIMENSION or j >= DIMENSION or i == j:
        raise VectorNativeReplayError("selected edge oscillator ids must be distinct 36D lane indices")
    coupling = _finite(edge.get("coupling"), "selected_edge.coupling")
    if coupling == 0.0:
        raise VectorNativeReplayError("selected edge coupling must be non-zero")
    if abs(_finite(edge.get("phi_i"), "selected_edge.phi_i") - phi[i]) > 1e-15:
        raise VectorNativeReplayError("selected_edge.phi_i does not match source phi lane")
    if abs(_finite(edge.get("phi_j"), "selected_edge.phi_j") - phi[j]) > 1e-15:
        raise VectorNativeReplayError("selected_edge.phi_j does not match source phi lane")

    for key in ("poincare_i", "poincare_j"):
        point = edge.get(key)
        if not isinstance(point, Sequence) or isinstance(point, (str, bytes, bytearray)) or len(point) != 2:
            raise VectorNativeReplayError(f"selected_edge.{key} must be a 2-vector")
        re = _finite(point[0], f"selected_edge.{key}[0]")
        im = _finite(point[1], f"selected_edge.{key}[1]")
        if re * re + im * im >= 1.0:
            raise VectorNativeReplayError(f"selected_edge.{key} must lie inside the Poincare unit disk")

    source_receipt = _hex64(source.get("receipt_sha256"), "receipt_sha256")
    working_state = _hex64(source.get("working_state_sha256"), "working_state_sha256")
    phi_hash = _hex64(source.get("phi_raw_sha256"), "phi_raw_sha256")
    omega_hash = _hex64(source.get("omega_raw_sha256"), "omega_raw_sha256")

    return {
        "tick": tick,
        "phi": phi,
        "omega": omega,
        "oscillator_i": i,
        "oscillator_j": j,
        "coupling": coupling,
        "source_receipt_sha256": source_receipt,
        "working_state_sha256": working_state,
        "phi_raw_sha256": phi_hash,
        "omega_raw_sha256": omega_hash,
    }


def build_replay_binary(source: Mapping[str, Any]) -> bytes:
    state = validate_source_snapshot(source)
    payload = bytearray(
        _HEADER.pack(
            _MAGIC,
            _VERSION,
            DIMENSION,
            state["tick"],
            state["oscillator_i"],
            state["oscillator_j"],
        )
    )
    payload.extend(_DOUBLE.pack(state["coupling"]))
    for value in state["phi"]:
        payload.extend(_DOUBLE.pack(value))
    for value in state["omega"]:
        payload.extend(_DOUBLE.pack(value))
    payload.extend(bytes.fromhex(state["source_receipt_sha256"]))
    payload.extend(bytes.fromhex(state["working_state_sha256"]))
    return bytes(payload)


def decode_replay_binary(payload: bytes) -> dict[str, Any]:
    expected_size = _HEADER.size + 8 + (DIMENSION * 8 * 2) + 32 + 32
    if len(payload) != expected_size:
        raise VectorNativeReplayError(f"replay payload must be exactly {expected_size} bytes")

    magic, version, dimension, tick, i, j = _HEADER.unpack_from(payload, 0)
    if magic != _MAGIC or version != _VERSION or dimension != DIMENSION:
        raise VectorNativeReplayError("replay header mismatch")
    if i < 0 or j < 0 or i >= DIMENSION or j >= DIMENSION or i == j:
        raise VectorNativeReplayError("replay header contains invalid selected edge")

    offset = _HEADER.size
    coupling = _DOUBLE.unpack_from(payload, offset)[0]
    offset += 8
    if not math.isfinite(coupling) or coupling == 0.0:
        raise VectorNativeReplayError("replay coupling must be finite and non-zero")

    phi = []
    for _ in range(DIMENSION):
        value = _DOUBLE.unpack_from(payload, offset)[0]
        offset += 8
        if not math.isfinite(value):
            raise VectorNativeReplayError("replay phi lane contains a non-finite value")
        phi.append(value)

    omega = []
    for _ in range(DIMENSION):
        value = _DOUBLE.unpack_from(payload, offset)[0]
        offset += 8
        if not math.isfinite(value):
            raise VectorNativeReplayError("replay omega lane contains a non-finite value")
        omega.append(value)

    source_receipt = payload[offset : offset + 32].hex()
    offset += 32
    working_state = payload[offset : offset + 32].hex()

    return {
        "tick": tick,
        "dimension": dimension,
        "oscillator_i": i,
        "oscillator_j": j,
        "coupling": coupling,
        "phi": tuple(phi),
        "omega": tuple(omega),
        "source_receipt_sha256": source_receipt,
        "working_state_sha256": working_state,
    }


def build_replay_receipt(source: Mapping[str, Any]) -> dict[str, Any]:
    state = validate_source_snapshot(source)
    payload = build_replay_binary(source)
    decoded = decode_replay_binary(payload)
    body = {
        "schema": REPLAY_SCHEMA,
        "source_schema": SOURCE_SCHEMA,
        "source_status": SOURCE_STATUS,
        "source_receipt_sha256": state["source_receipt_sha256"],
        "working_state_sha256": state["working_state_sha256"],
        "tick": decoded["tick"],
        "dimension": decoded["dimension"],
        "selected_edge": {
            "oscillator_i": decoded["oscillator_i"],
            "oscillator_j": decoded["oscillator_j"],
            "coupling": decoded["coupling"],
        },
        "replay_binary_bytes": len(payload),
        "replay_binary_sha256": hashlib.sha256(payload).hexdigest(),
        "transport_semantics": "DETERMINISTIC_QEMU_REPLAY_IMAGE",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "physical_h200_execution_claim": False,
        "physical_qpu_claim": False,
        "epistemic": "CHYBA",
    }
    return {
        **body,
        "replay_receipt_sha256": hashlib.sha256(_canonical_bytes(body)).hexdigest(),
    }


def validate_replay_receipt(receipt: Mapping[str, Any], source: Mapping[str, Any]) -> None:
    expected = build_replay_receipt(source)
    if dict(receipt) != expected:
        raise VectorNativeReplayError("replay receipt does not match deterministic reconstruction")
