from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

MANIFEST_SCHEMA = "BIOOS-PNLF-PERSISTENCE/0.1"
MANIFEST_DOMAIN = b"BIOOS-PNLF-PERSISTENCE/v0.1\x00"


class PNLFPersistenceError(ValueError):
    pass


def _hex32(value: str, name: str) -> str:
    text = str(value).lower()
    if len(text) != 64:
        raise PNLFPersistenceError(f"{name} must encode 32 bytes")
    try:
        bytes.fromhex(text)
    except ValueError as exc:
        raise PNLFPersistenceError(f"{name} must be hexadecimal") from exc
    return text


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


@dataclass(frozen=True)
class PNLFPersistenceBinding:
    file_id: str
    content_commitment: str
    checkpoint_object_id: str
    tau_frame_commitment: str
    t36_witness_commitment: str
    pncs_codec_contract: str = "PNCS_TAU_LIMINAL_FILE_CODEC_V0_1"
    state_memory_contract: str = "PNV-LIMINAL-CHECKPOINT/0.1"

    def __post_init__(self) -> None:
        for name in (
            "file_id",
            "content_commitment",
            "checkpoint_object_id",
            "tau_frame_commitment",
            "t36_witness_commitment",
        ):
            _hex32(getattr(self, name), name)
        if len({self.file_id, self.content_commitment, self.checkpoint_object_id}) != 3:
            raise PNLFPersistenceError("file, content and checkpoint identities must remain distinct")


def persistence_manifest(
    binding: PNLFPersistenceBinding,
    *,
    generation: int,
    tau_start: Mapping[str, int],
    tau_end: Mapping[str, int],
    active_liminal_layers: tuple[str, ...],
    realization_profile: str = "PNLF",
) -> dict[str, Any]:
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise PNLFPersistenceError("generation must be a non-negative integer")
    layers = tuple(sorted(set(active_liminal_layers)))
    if not layers:
        raise PNLFPersistenceError("active Liminal Memory layers are required")
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "generation": generation,
        "file_id": binding.file_id,
        "content_commitment": binding.content_commitment,
        "checkpoint_object_id": binding.checkpoint_object_id,
        "tau_frame_commitment": binding.tau_frame_commitment,
        "t36_witness_commitment": binding.t36_witness_commitment,
        "tau_start": dict(tau_start),
        "tau_end": dict(tau_end),
        "active_liminal_layers": list(layers),
        "pncs_codec_contract": binding.pncs_codec_contract,
        "state_memory_contract": binding.state_memory_contract,
        "realization_profile": realization_profile,
        "wall_clock_role": "REALIZATION_EVIDENCE",
        "content_parameter": "SCALAR_TAU",
        "integrity_witness": "T36_WHOLE_LANE",
        "consolidation_boundary": "STATE_MEMORY_CHECKPOINT",
    }
    manifest["manifest_id"] = hashlib.blake2b(MANIFEST_DOMAIN + _canonical(manifest), digest_size=32).hexdigest()
    return manifest


def pnh5_view(manifest: Mapping[str, Any], *, dataset_path: str, dataset_schema: str) -> dict[str, Any]:
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise PNLFPersistenceError("PNLF persistence manifest required")
    if not dataset_path or not dataset_schema:
        raise PNLFPersistenceError("dataset_path and dataset_schema are required")
    return {
        "schema": "BIOOS-PNH5-VIEW/0.1",
        "source_manifest_id": manifest["manifest_id"],
        "file_id": manifest["file_id"],
        "content_commitment": manifest["content_commitment"],
        "dataset_path": dataset_path,
        "dataset_schema": dataset_schema,
        "view_class": "HIERARCHICAL_DATASET_COMPATIBILITY",
    }
