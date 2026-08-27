from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Mapping

from t36_identity_record_v01 import RECORD_BYTES, T36IdentityRecord

ADAPTER_ID = "T36I_BINARY_V0_1"
FIDELITY_CLASS = "EXACT_SEMANTIC"
REALIZATION_DOMAIN = b"PN-T36I-BINARY/v0.1\x00"


class T36IdentityAnalogAdapterError(ValueError):
    pass


def _state_memory_api():
    try:
        from pnv_state_memory import (
            realization_binding,
            semantic_commitment,
            semantic_normal_form,
            t36_identity_semantic_state,
        )
    except ImportError as exc:
        raise T36IdentityAnalogAdapterError(
            "PNV-State-Memory analog-native API is required for T36I semantic binding"
        ) from exc
    return realization_binding, semantic_commitment, semantic_normal_form, t36_identity_semantic_state


@dataclass(frozen=True)
class T36IdentityRealization:
    semantic_state: Mapping[str, Any]
    semantic_commitment: str
    realization_id: str
    raw_sha256: str
    raw_bytes: bytes
    flags: int
    binding: Mapping[str, Any]


def _realization_identity(raw: bytes) -> str:
    return hashlib.sha256(REALIZATION_DOMAIN + raw).hexdigest()


def decode_t36i(
    raw: bytes | bytearray | memoryview,
    *,
    destination: str = "PNROM_T36_IDENTITY_RECORD",
) -> T36IdentityRealization:
    data = bytes(raw)
    if len(data) != RECORD_BYTES:
        raise T36IdentityAnalogAdapterError("T36I realization requires exactly 256 bytes")
    record = T36IdentityRecord.unpack(data)
    realization_binding, semantic_commitment, _, t36_identity_semantic_state = _state_memory_api()
    state = t36_identity_semantic_state(
        crystal_id=record.crystal_id.hex(),
        genesis_anchor_commitment=record.genesis_anchor_commitment.hex(),
        origin_binding_sha256=record.origin_binding_sha256.hex(),
        pnvector_payload_sha256=record.pnvector_payload_sha256.hex(),
        source_context_sha256=record.source_context_sha256.hex(),
        basis_binding=record.basis_binding.hex(),
        configuration_sha256=record.configuration_sha256.hex(),
        phase_index=record.phase_index,
        boot_epoch=record.boot_epoch,
        semantic_evidence={"physical_identity_profile": "T36_IDENTITY_CRYSTAL_V0_1"},
    )
    commitment = semantic_commitment(state)
    raw_sha = hashlib.sha256(data).hexdigest()
    realization_id = _realization_identity(data)
    binding = realization_binding(
        adapter_id=ADAPTER_ID,
        fidelity_class=FIDELITY_CLASS,
        realization_id=realization_id,
        destination=destination,
        source_semantic_commitment=commitment,
        evidence_ref=f"sha256:{raw_sha}",
    )
    return T36IdentityRealization(
        semantic_state=state,
        semantic_commitment=commitment,
        realization_id=realization_id,
        raw_sha256=raw_sha,
        raw_bytes=data,
        flags=record.flags,
        binding=binding,
    )


def materialize_t36i(state: Mapping[str, Any], *, flags: int = 0x7) -> bytes:
    _, _, semantic_normal_form, _ = _state_memory_api()
    normal = semantic_normal_form(state)
    if normal.get("domain") != "T36_IDENTITY_CRYSTAL":
        raise T36IdentityAnalogAdapterError("T36 identity semantic domain required")
    if not (0 <= flags <= 0xFFFFFFFF):
        raise T36IdentityAnalogAdapterError("flags must fit uint32")
    if flags & 0x7 != 0x7:
        raise T36IdentityAnalogAdapterError("current T36I physical admission requires binding flags 0x7")

    identity = normal["identity_context"]
    evidence = normal["semantic_evidence"]
    temporal = normal["temporal_state"]
    record = T36IdentityRecord(
        flags=flags,
        crystal_id=bytes.fromhex(str(identity["crystal_id"])),
        genesis_anchor_commitment=bytes.fromhex(str(identity["genesis_anchor_commitment"])),
        origin_binding_sha256=bytes.fromhex(str(evidence["origin_binding_sha256"])),
        pnvector_payload_sha256=bytes.fromhex(str(evidence["pnvector_payload_sha256"])),
        source_context_sha256=bytes.fromhex(str(evidence["source_context_sha256"])),
        basis_binding=bytes.fromhex(str(evidence["basis_binding"])),
        configuration_sha256=bytes.fromhex(str(evidence["configuration_sha256"])),
        phase_index=int(temporal["phase_index"]),
        boot_epoch=int(temporal["boot_epoch"]),
    )
    return record.pack()


def verify_t36i(realization: T36IdentityRealization) -> None:
    if len(realization.raw_bytes) != RECORD_BYTES:
        raise T36IdentityAnalogAdapterError("realization byte length mismatch")
    decoded = decode_t36i(realization.raw_bytes, destination=str(realization.binding.get("destination", "PNROM_T36_IDENTITY_RECORD")))
    if decoded.semantic_commitment != realization.semantic_commitment:
        raise T36IdentityAnalogAdapterError("semantic commitment mismatch")
    if decoded.realization_id != realization.realization_id:
        raise T36IdentityAnalogAdapterError("realization identity mismatch")
    if decoded.raw_sha256 != realization.raw_sha256:
        raise T36IdentityAnalogAdapterError("raw realization SHA mismatch")
    if realization.binding.get("source_semantic_commitment") != realization.semantic_commitment:
        raise T36IdentityAnalogAdapterError("binding semantic commitment mismatch")
    if realization.binding.get("realization_id") != realization.realization_id:
        raise T36IdentityAnalogAdapterError("binding realization identity mismatch")
