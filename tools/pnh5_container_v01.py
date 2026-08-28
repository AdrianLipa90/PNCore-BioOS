from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
from typing import Any, Iterable, Mapping

from .pnlf_persistence_v01 import verify_persistence_manifest

CONTAINER_SCHEMA = "BIOOS_PNH5_CONTAINER_V0_1"
MAGIC = b"PNH5\x00\x01\r\n"
CONTAINER_DOMAIN = b"BIOOS-PNH5-CONTAINER/v0.1\x00"
RECORD_DOMAIN = b"BIOOS-PNH5-RECORD/v0.1\x00"
HEADER = struct.Struct("<8sQI32s")
RECORD_HEADER = struct.Struct("<4sQ32s32s")
KNOWN_RECORD_KINDS = {b"TAUF", b"CHKP"}


class PNH5ContainerError(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _hex32(value: str, name: str) -> str:
    text = str(value).lower()
    if len(text) != 64:
        raise PNH5ContainerError(f"{name} must encode 32 bytes")
    try:
        bytes.fromhex(text)
    except ValueError as exc:
        raise PNH5ContainerError(f"{name} must be hexadecimal") from exc
    return text


@dataclass(frozen=True)
class PNH5Record:
    kind: bytes
    logical_id: str
    payload: bytes

    def __post_init__(self) -> None:
        if self.kind not in KNOWN_RECORD_KINDS:
            raise PNH5ContainerError(f"unknown PNH5 record kind: {self.kind!r}")
        _hex32(self.logical_id, "logical_id")
        object.__setattr__(self, "payload", bytes(self.payload))


@dataclass(frozen=True)
class PNH5Container:
    manifest: Mapping[str, Any]
    records: tuple[PNH5Record, ...]
    container_id: str


def tau_frame_record(*, frame_commitment: str, realization: bytes | bytearray | memoryview) -> PNH5Record:
    return PNH5Record(b"TAUF", _hex32(frame_commitment, "frame_commitment"), bytes(realization))


def checkpoint_record(*, checkpoint_object_id: str, serialization: bytes | bytearray | memoryview) -> PNH5Record:
    return PNH5Record(b"CHKP", _hex32(checkpoint_object_id, "checkpoint_object_id"), bytes(serialization))


def encode_container(manifest: Mapping[str, Any], records: Iterable[PNH5Record]) -> bytes:
    verify_persistence_manifest(manifest)
    record_set = tuple(records)
    if not record_set:
        raise PNH5ContainerError("PNH5 container requires at least one record")
    if not any(record.kind == b"TAUF" for record in record_set):
        raise PNH5ContainerError("PNH5 container requires at least one TAUF record")
    if not any(record.kind == b"CHKP" for record in record_set):
        raise PNH5ContainerError("PNH5 container requires a State Memory CHKP record")

    manifest_raw = _canonical(dict(manifest))
    prefix = HEADER.pack(
        MAGIC,
        len(manifest_raw),
        len(record_set),
        hashlib.blake2b(manifest_raw, digest_size=32).digest(),
    ) + manifest_raw

    parts = [prefix]
    for record in record_set:
        payload_digest = hashlib.blake2b(
            RECORD_DOMAIN + record.kind + record.payload,
            digest_size=32,
        ).digest()
        parts.append(
            RECORD_HEADER.pack(
                record.kind,
                len(record.payload),
                bytes.fromhex(record.logical_id),
                payload_digest,
            )
            + record.payload
        )

    body = b"".join(parts)
    seal = hashlib.blake2b(CONTAINER_DOMAIN + body, digest_size=32).digest()
    return body + seal


def decode_container(raw: bytes | bytearray | memoryview) -> PNH5Container:
    blob = bytes(raw)
    if len(blob) < HEADER.size + 32:
        raise PNH5ContainerError("PNH5 container is too short")

    body, seal = blob[:-32], blob[-32:]
    expected_seal = hashlib.blake2b(CONTAINER_DOMAIN + body, digest_size=32).digest()
    if seal != expected_seal:
        raise PNH5ContainerError("PNH5 container seal mismatch")

    magic, manifest_length, record_count, manifest_digest = HEADER.unpack_from(body, 0)
    if magic != MAGIC:
        raise PNH5ContainerError("PNH5 magic mismatch")

    offset = HEADER.size
    manifest_raw = body[offset : offset + manifest_length]
    if len(manifest_raw) != manifest_length:
        raise PNH5ContainerError("truncated PNH5 manifest")
    offset += manifest_length
    if hashlib.blake2b(manifest_raw, digest_size=32).digest() != manifest_digest:
        raise PNH5ContainerError("PNH5 manifest digest mismatch")
    try:
        manifest = json.loads(manifest_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PNH5ContainerError("invalid PNH5 manifest serialization") from exc
    if not isinstance(manifest, dict):
        raise PNH5ContainerError("PNH5 manifest must decode to an object")
    verify_persistence_manifest(manifest)

    records: list[PNH5Record] = []
    for _ in range(record_count):
        if offset + RECORD_HEADER.size > len(body):
            raise PNH5ContainerError("truncated PNH5 record header")
        kind, payload_length, logical_id, payload_digest = RECORD_HEADER.unpack_from(body, offset)
        offset += RECORD_HEADER.size
        if kind not in KNOWN_RECORD_KINDS:
            raise PNH5ContainerError(f"unknown PNH5 record kind: {kind!r}")
        payload = body[offset : offset + payload_length]
        if len(payload) != payload_length:
            raise PNH5ContainerError("truncated PNH5 record payload")
        offset += payload_length
        expected_digest = hashlib.blake2b(RECORD_DOMAIN + kind + payload, digest_size=32).digest()
        if payload_digest != expected_digest:
            raise PNH5ContainerError("PNH5 record digest mismatch")
        records.append(PNH5Record(kind, logical_id.hex(), payload))

    if offset != len(body):
        raise PNH5ContainerError("unexpected bytes after PNH5 record stream")
    if not any(record.kind == b"TAUF" for record in records):
        raise PNH5ContainerError("PNH5 container has no TAUF records")
    checkpoint_ids = [record.logical_id for record in records if record.kind == b"CHKP"]
    if manifest["checkpoint_object_id"] not in checkpoint_ids:
        raise PNH5ContainerError("manifest checkpoint is absent from PNH5 record stream")

    container_id = hashlib.blake2b(CONTAINER_DOMAIN + body, digest_size=32).hexdigest()
    return PNH5Container(manifest=manifest, records=tuple(records), container_id=container_id)


def write_pnh5(path: Path | str, manifest: Mapping[str, Any], records: Iterable[PNH5Record]) -> PNH5Container:
    target = Path(path)
    if target.suffix.lower() != ".pnh5":
        raise PNH5ContainerError("PNH5 path must use the .pnh5 suffix")
    target.parent.mkdir(parents=True, exist_ok=True)
    blob = encode_container(manifest, records)
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(blob)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()
    return decode_container(target.read_bytes())


def read_pnh5(path: Path | str) -> PNH5Container:
    return decode_container(Path(path).read_bytes())
