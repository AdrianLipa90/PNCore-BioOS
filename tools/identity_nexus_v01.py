from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping, Sequence

KAPPA = math.log(2.0) / (24.0 * math.pi)
VECTOR_DIM = 36
DEFAULT_ACTIVE_LIMIT = 16
SCHEMA = "BIOOS_IDENTITY_NEXUS_V0_1"


class IdentityNexusError(ValueError):
    pass


def _hex32(value: str, name: str) -> str:
    v = str(value).lower()
    if len(v) != 64:
        raise IdentityNexusError(f"{name} must encode 32 bytes")
    try:
        bytes.fromhex(v)
    except ValueError as exc:
        raise IdentityNexusError(f"{name} must be hex") from exc
    return v


def _finite_float(value: Any, name: str) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise IdentityNexusError(f"{name} must be finite")
    return x


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _validate_crystal_context(context: Mapping[str, Any]) -> dict[str, Any]:
    phase_index = int(context["phase_index"])
    boot_epoch = int(context["boot_epoch"])
    if phase_index < 0 or boot_epoch < 0:
        raise IdentityNexusError("phase_index and boot_epoch must be non-negative")
    spinor_sheet = int(context.get("spinor_sheet", phase_index & 1))
    if spinor_sheet != (phase_index & 1):
        raise IdentityNexusError("spinor_sheet mismatch")
    out = {
        "crystal_id": _hex32(context["crystal_id"], "crystal_id"),
        "configuration_sha256": _hex32(context["configuration_sha256"], "configuration_sha256"),
        "boot_epoch": boot_epoch,
        "phase_index": phase_index,
        "spinor_sheet": spinor_sheet,
    }
    source_object_id = context.get("source_object_id")
    if source_object_id is not None:
        out["source_object_id"] = _hex32(source_object_id, "source_object_id")
    return out


def _validate_dictionary_binding(binding: Mapping[str, Any]) -> dict[str, Any]:
    states = int(binding["states"])
    relations = int(binding["relations"])
    if states <= 0 or relations < 0:
        raise IdentityNexusError("invalid Dictionary counts")
    return {
        "repository": str(binding.get("repository", "AdrianLipa90/The-Consciousness-Dictionary")),
        "branch": str(binding["branch"]),
        "commit": str(binding["commit"]),
        "states": states,
        "relations": relations,
        "state_sha256": _hex32(binding["state_sha256"], "state_sha256"),
        "relation_sha256": _hex32(binding["relation_sha256"], "relation_sha256"),
    }


def _validate_projection_rows(rows: Sequence[Mapping[str, Any]], expected_count: int) -> list[dict[str, Any]]:
    if len(rows) != expected_count:
        raise IdentityNexusError(f"term count mismatch: expected {expected_count}, got {len(rows)}")
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for raw in rows:
        term_id = str(raw["term_id"])
        if not term_id:
            raise IdentityNexusError("empty term_id")
        if term_id in seen:
            raise IdentityNexusError(f"duplicate term_id: {term_id}")
        seen.add(term_id)
        coherence = _finite_float(raw["coherence"], f"{term_id}.coherence")
        if coherence < -1e-12 or coherence > 1.0 + 1e-12:
            raise IdentityNexusError(f"{term_id}.coherence outside [0,1]")
        coherence = min(1.0, max(0.0, coherence))
        phase = _finite_float(raw["phase"], f"{term_id}.phase")
        action = _finite_float(raw["informational_action"], f"{term_id}.informational_action")
        distance = _finite_float(raw["angular_distance"], f"{term_id}.angular_distance")
        if distance < 0.0:
            raise IdentityNexusError(f"{term_id}.angular_distance must be non-negative")
        if bool(raw.get("authority_grant", False)):
            raise IdentityNexusError("projection row attempted authority grant")
        if bool(raw.get("semantic_equivalence", False)):
            raise IdentityNexusError("projection row attempted semantic equivalence")
        out.append({
            "term_id": term_id,
            "name": str(raw.get("name", term_id)),
            "phase_index": int(raw.get("phase_index", 0)),
            "coherence": coherence,
            "phase": phase,
            "informational_action": action,
            "angular_distance": distance,
            "semantic_equivalence": False,
            "authority_grant": False,
        })
    return out


def compute_identity_nexus(
    *,
    crystal_context: Mapping[str, Any],
    dictionary_binding: Mapping[str, Any],
    projection_rows: Sequence[Mapping[str, Any]],
    active_limit: int = DEFAULT_ACTIVE_LIMIT,
) -> dict[str, Any]:
    crystal = _validate_crystal_context(crystal_context)
    dictionary = _validate_dictionary_binding(dictionary_binding)
    rows = _validate_projection_rows(projection_rows, dictionary["states"])
    if active_limit <= 0:
        raise IdentityNexusError("active_limit must be positive")

    # Dictionary's current informational_action uses -kappa*ln(R+epsilon), so
    # exact self-coherence can generate a tiny negative floating-point action.
    # Global coherence is clamped to its declared [0,1] statistic range.
    mean_action = math.fsum(row["informational_action"] for row in rows) / len(rows)
    global_coherence = math.exp(-mean_action / KAPPA)
    global_coherence = min(1.0, max(0.0, global_coherence))

    ordered = sorted(
        rows,
        key=lambda r: (
            -r["coherence"],
            r["informational_action"],
            r["angular_distance"],
            r["term_id"],
        ),
    )
    active = ordered[: min(active_limit, len(ordered))]

    core: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "ACTIVE_DERIVED_WORKING_STATE",
        "authority_class": "DERIVED_WORKING_STATE",
        "authority_grant": False,
        "semantic_equivalence_grant": False,
        "crystal": crystal,
        "dictionary": dictionary,
        "term_count": len(rows),
        "active_limit": min(active_limit, len(rows)),
        "mean_informational_action": mean_action,
        "nexus_coherence": global_coherence,
        "active_terms": active,
        "aggregation": {
            "policy": "EQUAL_WEIGHT_INFORMATIONAL_ACTION_V0_1",
            "kappa": KAPPA,
            "formula": "C_NEXUS=clamp(exp(-mean(S_k)/kappa),0,1)",
            "full_term_set": True,
        },
    }
    generation_id = hashlib.sha256(b"BIOOS-IDENTITY-NEXUS/v0.1\x00" + canonical_json_bytes(core)).hexdigest()
    return {**core, "nexus_generation_id": generation_id}


def validate_nexus_generation(generation: Mapping[str, Any]) -> bool:
    if generation.get("schema") != SCHEMA:
        raise IdentityNexusError("unsupported NEXUS schema")
    if generation.get("authority_class") != "DERIVED_WORKING_STATE":
        raise IdentityNexusError("invalid NEXUS authority class")
    if generation.get("authority_grant") is not False:
        raise IdentityNexusError("NEXUS authority grant must be false")
    if generation.get("semantic_equivalence_grant") is not False:
        raise IdentityNexusError("NEXUS semantic equivalence grant must be false")
    supplied = _hex32(generation["nexus_generation_id"], "nexus_generation_id")
    core = dict(generation)
    core.pop("nexus_generation_id", None)
    expected = hashlib.sha256(b"BIOOS-IDENTITY-NEXUS/v0.1\x00" + canonical_json_bytes(core)).hexdigest()
    if supplied != expected:
        raise IdentityNexusError("NEXUS generation hash mismatch")
    _validate_crystal_context(generation["crystal"])
    _validate_dictionary_binding(generation["dictionary"])
    coherence = _finite_float(generation["nexus_coherence"], "nexus_coherence")
    if not (0.0 <= coherence <= 1.0):
        raise IdentityNexusError("nexus_coherence outside [0,1]")
    return True
