from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from typing import Any, Mapping

MANIFEST_SCHEMA = "BIOOS-PNLF-PERSISTENCE/0.1"
MANIFEST_DOMAIN = b"BIOOS-PNLF-PERSISTENCE/v0.1\x00"
STATE_CHECKPOINT_SCHEMA = "PNV-LIMINAL-CHECKPOINT/0.1"


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


def _tau_fraction(value: Mapping[str, int], name: str) -> Fraction:
    try:
        return Fraction(int(value["p"]), int(value["q"]))
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        raise PNLFPersistenceError(f"invalid {name} rational tau coordinate") from exc


@dataclass(frozen=True)
class PNLFPersistenceBinding:
    file_id: str
    content_commitment: str
    checkpoint_object_id: str
    tau_frame_commitment: str
    t36_witness_commitment: str
    pncs_codec_contract: str = "PNCS_TAU_LIMINAL_FILE_CODEC_V0_1"
    state_memory_contract: str = STATE_CHECKPOINT_SCHEMA

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
        if self.tau_frame_commitment == self.t36_witness_commitment:
            raise PNLFPersistenceError("tau-frame and T36 witness commitments must remain distinct")


def binding_from_state_checkpoint(
    checkpoint: Mapping[str, Any],
    *,
    tau_frame_commitment: str,
    t36_witness_commitment: str,
) -> PNLFPersistenceBinding:
    if checkpoint.get("schema") != STATE_CHECKPOINT_SCHEMA:
        raise PNLFPersistenceError("PNV Liminal State Memory checkpoint required")
    required = {
        "file_id",
        "cumulative_content_commitment",
        "object_id",
        "generation",
        "tau_end",
        "segment_commitment",
    }
    missing = required.difference(checkpoint)
    if missing:
        raise PNLFPersistenceError(f"missing State Memory checkpoint fields: {sorted(missing)}")
    if isinstance(checkpoint["generation"], bool) or not isinstance(checkpoint["generation"], int) or checkpoint["generation"] < 0:
        raise PNLFPersistenceError("State Memory generation must be a non-negative integer")
    _tau_fraction(checkpoint["tau_end"], "checkpoint tau_end")
    _hex32(str(checkpoint["segment_commitment"]), "segment_commitment")
    return PNLFPersistenceBinding(
        file_id=str(checkpoint["file_id"]),
        content_commitment=str(checkpoint["cumulative_content_commitment"]),
        checkpoint_object_id=str(checkpoint["object_id"]),
        tau_frame_commitment=tau_frame_commitment,
        t36_witness_commitment=t36_witness_commitment,
    )


def persistence_manifest(
    binding: PNLFPersistenceBinding,
    *,
    generation: int,
    tau_start: Mapping[str, int],
    tau_end: Mapping[str, int],
    active_liminal_layers: tuple[str, ...],
    realization_profile: str = "PNLF",
    state_checkpoint: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise PNLFPersistenceError("generation must be a non-negative integer")
    tau0 = _tau_fraction(tau_start, "tau_start")
    tau1 = _tau_fraction(tau_end, "tau_end")
    if tau1 <= tau0:
        raise PNLFPersistenceError("tau_end must be greater than tau_start")
    layers = tuple(sorted(set(active_liminal_layers)))
    if not layers:
        raise PNLFPersistenceError("active Liminal Memory layers are required")
    if state_checkpoint is not None:
        expected = binding_from_state_checkpoint(
            state_checkpoint,
            tau_frame_commitment=binding.tau_frame_commitment,
            t36_witness_commitment=binding.t36_witness_commitment,
        )
        if expected != binding:
            raise PNLFPersistenceError("State Memory checkpoint does not match persistence binding")
        if state_checkpoint["generation"] != generation:
            raise PNLFPersistenceError("State Memory generation mismatch")
        if _tau_fraction(state_checkpoint["tau_end"], "checkpoint tau_end") != tau1:
            raise PNLFPersistenceError("State Memory tau_end mismatch")
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
        "commitment_holonomy": {
            "PNCS.frame_commitment": "StateMemory.carrier_commitment -> BioOS.tau_frame_commitment",
            "PNCS.witness_commitment": "StateMemory.t36_witness_commitment -> BioOS.t36_witness_commitment",
        },
    }
    manifest["manifest_id"] = hashlib.blake2b(MANIFEST_DOMAIN + _canonical(manifest), digest_size=32).hexdigest()
    return manifest


def verify_persistence_manifest(manifest: Mapping[str, Any]) -> None:
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise PNLFPersistenceError("PNLF persistence manifest required")
    required = {
        "generation",
        "file_id",
        "content_commitment",
        "checkpoint_object_id",
        "tau_frame_commitment",
        "t36_witness_commitment",
        "tau_start",
        "tau_end",
        "active_liminal_layers",
        "pncs_codec_contract",
        "state_memory_contract",
        "realization_profile",
        "wall_clock_role",
        "content_parameter",
        "integrity_witness",
        "consolidation_boundary",
        "commitment_holonomy",
        "manifest_id",
    }
    missing = required.difference(manifest)
    if missing:
        raise PNLFPersistenceError(f"missing persistence manifest fields: {sorted(missing)}")
    for name in (
        "file_id",
        "content_commitment",
        "checkpoint_object_id",
        "tau_frame_commitment",
        "t36_witness_commitment",
        "manifest_id",
    ):
        _hex32(str(manifest[name]), name)
    if isinstance(manifest["generation"], bool) or not isinstance(manifest["generation"], int) or manifest["generation"] < 0:
        raise PNLFPersistenceError("generation must be a non-negative integer")
    if _tau_fraction(manifest["tau_end"], "tau_end") <= _tau_fraction(manifest["tau_start"], "tau_start"):
        raise PNLFPersistenceError("invalid persistence tau interval")
    raw = {k: manifest[k] for k in manifest if k != "manifest_id"}
    expected = hashlib.blake2b(MANIFEST_DOMAIN + _canonical(raw), digest_size=32).hexdigest()
    if expected != manifest["manifest_id"]:
        raise PNLFPersistenceError("persistence manifest identity mismatch")


def pnh5_view(manifest: Mapping[str, Any], *, dataset_path: str, dataset_schema: str) -> dict[str, Any]:
    verify_persistence_manifest(manifest)
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
