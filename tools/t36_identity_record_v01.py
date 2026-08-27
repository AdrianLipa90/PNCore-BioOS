from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct

MAGIC = b"T36I"
VERSION_MAJOR = 1
VERSION_MINOR = 0
RECORD_BYTES = 256
VECTOR_DIM = 36
ID_DOMAIN = b"T36-ID/v0.1"
GENESIS_COMMIT_DOMAIN = b"T36-GENESIS-COMMIT/v0.1"
ORIGIN_DOMAIN = b"T36-ORIGIN/v0.1"
CONFIG_DOMAIN = b"T36-CONFIG/v0.1"

# magic, major, minor, record_bytes, vector_dim, flags,
# 7 x 32-byte bindings, phase_index, boot_epoch
_HEADER = struct.Struct("<4sHHHHI")
_U64_PAIR = struct.Struct("<QQ")


def _require32(value: bytes, name: str) -> bytes:
    raw = bytes(value)
    if len(raw) != 32:
        raise ValueError(f"{name} must be exactly 32 bytes")
    return raw


def derive_crystal_id(genesis_anchor: bytes) -> bytes:
    anchor = _require32(genesis_anchor, "genesis_anchor")
    return hashlib.sha256(ID_DOMAIN + anchor).digest()


def derive_genesis_anchor_commitment(genesis_anchor: bytes) -> bytes:
    anchor = _require32(genesis_anchor, "genesis_anchor")
    return hashlib.sha256(GENESIS_COMMIT_DOMAIN + anchor).digest()


def derive_origin_binding_sha256(
    crystal_id: bytes,
    pnvector_payload_sha256: bytes,
    source_context_sha256: bytes,
    basis_binding: bytes,
    pnr_binding: bytes,
) -> bytes:
    parts = (
        _require32(crystal_id, "crystal_id"),
        _require32(pnvector_payload_sha256, "pnvector_payload_sha256"),
        _require32(source_context_sha256, "source_context_sha256"),
        _require32(basis_binding, "basis_binding"),
        _require32(pnr_binding, "pnr_binding"),
    )
    return hashlib.sha256(ORIGIN_DOMAIN + b"".join(parts)).digest()


def derive_configuration_sha256(
    pnvector_payload_sha256: bytes,
    basis_binding: bytes,
    source_context_sha256: bytes,
    pnrom_code_binding: bytes,
    pnr_binding: bytes,
    program_binding: bytes,
    scheduler_binding: bytes,
) -> bytes:
    parts = (
        _require32(pnvector_payload_sha256, "pnvector_payload_sha256"),
        _require32(basis_binding, "basis_binding"),
        _require32(source_context_sha256, "source_context_sha256"),
        _require32(pnrom_code_binding, "pnrom_code_binding"),
        _require32(pnr_binding, "pnr_binding"),
        _require32(program_binding, "program_binding"),
        _require32(scheduler_binding, "scheduler_binding"),
    )
    return hashlib.sha256(CONFIG_DOMAIN + b"".join(parts)).digest()


@dataclass(frozen=True, slots=True)
class T36IdentityRecord:
    flags: int
    crystal_id: bytes
    genesis_anchor_commitment: bytes
    origin_binding_sha256: bytes
    pnvector_payload_sha256: bytes
    source_context_sha256: bytes
    basis_binding: bytes
    configuration_sha256: bytes
    phase_index: int
    boot_epoch: int

    @property
    def spinor_sheet(self) -> int:
        return self.phase_index & 1

    def pack(self) -> bytes:
        if not (0 <= self.flags <= 0xFFFFFFFF):
            raise ValueError("flags outside uint32")
        if not (0 <= self.phase_index <= 0xFFFFFFFFFFFFFFFF):
            raise ValueError("phase_index outside uint64")
        if not (0 <= self.boot_epoch <= 0xFFFFFFFFFFFFFFFF):
            raise ValueError("boot_epoch outside uint64")

        bindings = (
            _require32(self.crystal_id, "crystal_id"),
            _require32(self.genesis_anchor_commitment, "genesis_anchor_commitment"),
            _require32(self.origin_binding_sha256, "origin_binding_sha256"),
            _require32(self.pnvector_payload_sha256, "pnvector_payload_sha256"),
            _require32(self.source_context_sha256, "source_context_sha256"),
            _require32(self.basis_binding, "basis_binding"),
            _require32(self.configuration_sha256, "configuration_sha256"),
        )
        raw = b"".join(
            (
                _HEADER.pack(
                    MAGIC,
                    VERSION_MAJOR,
                    VERSION_MINOR,
                    RECORD_BYTES,
                    VECTOR_DIM,
                    self.flags,
                ),
                *bindings,
                _U64_PAIR.pack(self.phase_index, self.boot_epoch),
            )
        )
        if len(raw) != RECORD_BYTES:
            raise AssertionError(f"T36 identity record size drift: {len(raw)}")
        return raw

    @classmethod
    def unpack(cls, raw: bytes) -> "T36IdentityRecord":
        data = bytes(raw)
        if len(data) != RECORD_BYTES:
            raise ValueError("T36 identity record must be exactly 256 bytes")
        magic, major, minor, record_bytes, vector_dim, flags = _HEADER.unpack_from(data, 0)
        if magic != MAGIC:
            raise ValueError("invalid T36 identity magic")
        if (major, minor) != (VERSION_MAJOR, VERSION_MINOR):
            raise ValueError("unsupported T36 identity record version")
        if record_bytes != RECORD_BYTES or vector_dim != VECTOR_DIM:
            raise ValueError("T36 identity geometry mismatch")

        off = _HEADER.size
        fields: list[bytes] = []
        for _ in range(7):
            fields.append(data[off : off + 32])
            off += 32
        phase_index, boot_epoch = _U64_PAIR.unpack_from(data, off)
        return cls(
            flags=flags,
            crystal_id=fields[0],
            genesis_anchor_commitment=fields[1],
            origin_binding_sha256=fields[2],
            pnvector_payload_sha256=fields[3],
            source_context_sha256=fields[4],
            basis_binding=fields[5],
            configuration_sha256=fields[6],
            phase_index=phase_index,
            boot_epoch=boot_epoch,
        )


def record_sha256(record: T36IdentityRecord | bytes) -> str:
    raw = record.pack() if isinstance(record, T36IdentityRecord) else bytes(record)
    if len(raw) != RECORD_BYTES:
        raise ValueError("record_sha256 requires exact 256-byte record")
    return hashlib.sha256(raw).hexdigest()
