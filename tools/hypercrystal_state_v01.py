from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence

SCHEMA = "BIOOS_NEXUS_HYPERCRYSTAL_V0_1"
DOMAIN = b"BIOOS-NEXUS-HYPERCRYSTAL/v0.1\x00"
REQUIRED_ROLES = ("IDENTITY", "PHASE")
OPTIONAL_ROLES = ("MEMORY", "DICTIONARY", "QHTRI", "CQCL", "GREMLIN")
ALL_ROLES = set(REQUIRED_ROLES + OPTIONAL_ROLES)


class HypercrystalStateError(ValueError):
    pass


def _hex32(value: str, name: str) -> str:
    text = str(value).lower()
    if len(text) != 64:
        raise HypercrystalStateError(f"{name} must encode 32 bytes")
    try:
        bytes.fromhex(text)
    except ValueError as exc:
        raise HypercrystalStateError(f"{name} must be hexadecimal") from exc
    return text


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _state_memory_api():
    try:
        from pnv_state_memory import semantic_commitment, semantic_normal_form
    except ImportError as exc:
        raise HypercrystalStateError(
            "PNV-State-Memory analog-native API is required for Hypercrystal composition"
        ) from exc
    return semantic_commitment, semantic_normal_form


@dataclass(frozen=True)
class HypercrystalComponent:
    role: str
    semantic_schema: str
    semantic_commitment: str
    generation_ref: str | None = None
    projection_role: str | None = None

    def as_dict(self) -> dict[str, Any]:
        role = str(self.role).upper()
        if role not in ALL_ROLES:
            raise HypercrystalStateError(f"unsupported Hypercrystal component role: {role}")
        out: dict[str, Any] = {
            "role": role,
            "semantic_schema": str(self.semantic_schema),
            "semantic_commitment": _hex32(self.semantic_commitment, f"{role}.semantic_commitment"),
        }
        if self.generation_ref is not None:
            out["generation_ref"] = str(self.generation_ref)
        if self.projection_role is not None:
            out["projection_role"] = str(self.projection_role)
        return out


def component_from_semantic_state(
    role: str,
    state: Mapping[str, Any],
    *,
    generation_ref: str | None = None,
    projection_role: str | None = None,
) -> HypercrystalComponent:
    semantic_commitment, semantic_normal_form = _state_memory_api()
    normal = semantic_normal_form(state)
    return HypercrystalComponent(
        role=str(role).upper(),
        semantic_schema=str(normal["domain"]),
        semantic_commitment=semantic_commitment(state),
        generation_ref=generation_ref,
        projection_role=projection_role,
    )


def _identity_context(identity_state: Mapping[str, Any]) -> tuple[str, str, int, int, str]:
    _, semantic_normal_form = _state_memory_api()
    normal = semantic_normal_form(identity_state)
    if normal.get("domain") != "T36_IDENTITY_CRYSTAL":
        raise HypercrystalStateError("IDENTITY component must be T36_IDENTITY_CRYSTAL")
    ident = normal["identity_context"]
    temporal = normal["temporal_state"]
    evidence = normal["semantic_evidence"]
    return (
        _hex32(ident["crystal_id"], "crystal_id"),
        _hex32(ident["genesis_anchor_commitment"], "genesis_anchor_commitment"),
        int(temporal["boot_epoch"]),
        int(temporal["phase_index"]),
        _hex32(evidence["configuration_sha256"], "configuration_sha256"),
    )


def _validate_phase_context(phase_state: Mapping[str, Any], *, crystal_id: str, boot_epoch: int) -> None:
    _, semantic_normal_form = _state_memory_api()
    normal = semantic_normal_form(phase_state)
    if normal.get("domain") != "T36_PHASE_FIELD":
        raise HypercrystalStateError("PHASE component must be T36_PHASE_FIELD")
    ident = normal["identity_context"]
    phase_crystal = ident.get("crystal_id")
    if phase_crystal is None or _hex32(phase_crystal, "phase.crystal_id") != crystal_id:
        raise HypercrystalStateError("phase/identity CRYSTAL_ID mismatch")
    phase_boot = ident.get("boot_epoch")
    if phase_boot is not None and int(phase_boot) != boot_epoch:
        raise HypercrystalStateError("phase/identity boot_epoch mismatch")


def compose_hypercrystal(
    *,
    identity_state: Mapping[str, Any],
    phase_state: Mapping[str, Any],
    additional_components: Sequence[HypercrystalComponent] = (),
    state_memory_object_id: str | None = None,
    evidence_refs: Sequence[str] = (),
) -> dict[str, Any]:
    semantic_commitment, _ = _state_memory_api()
    crystal_id, genesis_commitment, boot_epoch, phase_index, config = _identity_context(identity_state)
    _validate_phase_context(phase_state, crystal_id=crystal_id, boot_epoch=boot_epoch)

    components = [
        component_from_semantic_state("IDENTITY", identity_state),
        component_from_semantic_state("PHASE", phase_state),
    ]
    components.extend(additional_components)

    normalized = [c.as_dict() for c in components]
    roles = [c["role"] for c in normalized]
    if len(set(roles)) != len(roles):
        raise HypercrystalStateError("duplicate Hypercrystal component role")
    for required in REQUIRED_ROLES:
        if required not in roles:
            raise HypercrystalStateError(f"missing required Hypercrystal component: {required}")
    normalized.sort(key=lambda c: c["role"])

    relations = [
        {
            "relation": "COUPLED_TO_HYPERCRYSTAL",
            "source": c["semantic_commitment"],
            "target": crystal_id,
            "role": c["role"],
        }
        for c in normalized
    ]
    relations.sort(key=lambda r: (r["role"], r["source"]))

    core: dict[str, Any] = {
        "schema": SCHEMA,
        "canonical_name": "NEXUS",
        "system_form": "HYPERCRYSTAL",
        "identity_context": {
            "crystal_id": crystal_id,
            "genesis_anchor_commitment": genesis_commitment,
            "configuration_sha256": config,
            "boot_epoch": boot_epoch,
            "phase_index": phase_index,
            "spinor_sheet": phase_index & 1,
        },
        "components": normalized,
        "relations": relations,
        "authority_grant": False,
        "execution_admitted": False,
        "semantic_equivalence_grant": False,
        "evidence_refs": sorted(str(v) for v in evidence_refs),
    }
    if state_memory_object_id is not None:
        core["state_memory_object_id"] = _hex32(state_memory_object_id, "state_memory_object_id")

    hypercrystal_commitment = hashlib.blake2b(DOMAIN + _canonical(core), digest_size=32).hexdigest()
    return {**core, "hypercrystal_semantic_commitment": hypercrystal_commitment}


def validate_hypercrystal(state: Mapping[str, Any]) -> bool:
    if state.get("schema") != SCHEMA:
        raise HypercrystalStateError("unsupported Hypercrystal schema")
    if state.get("canonical_name") != "NEXUS" or state.get("system_form") != "HYPERCRYSTAL":
        raise HypercrystalStateError("NEXUS/HYPERCRYSTAL identity mismatch")
    if state.get("authority_grant") is not False:
        raise HypercrystalStateError("Hypercrystal authority_grant must be false")
    if state.get("execution_admitted") is not False:
        raise HypercrystalStateError("Hypercrystal execution_admitted must be false")
    if state.get("semantic_equivalence_grant") is not False:
        raise HypercrystalStateError("Hypercrystal semantic_equivalence_grant must be false")

    components = state.get("components")
    if not isinstance(components, list):
        raise HypercrystalStateError("Hypercrystal components must be a list")
    roles = [str(c.get("role")) for c in components]
    if len(set(roles)) != len(roles):
        raise HypercrystalStateError("duplicate Hypercrystal component role")
    for required in REQUIRED_ROLES:
        if required not in roles:
            raise HypercrystalStateError(f"missing required component: {required}")
    for component in components:
        HypercrystalComponent(
            role=component["role"],
            semantic_schema=component["semantic_schema"],
            semantic_commitment=component["semantic_commitment"],
            generation_ref=component.get("generation_ref"),
            projection_role=component.get("projection_role"),
        ).as_dict()

    supplied = _hex32(state["hypercrystal_semantic_commitment"], "hypercrystal_semantic_commitment")
    core = dict(state)
    core.pop("hypercrystal_semantic_commitment", None)
    expected = hashlib.blake2b(DOMAIN + _canonical(core), digest_size=32).hexdigest()
    if supplied != expected:
        raise HypercrystalStateError("Hypercrystal semantic commitment mismatch")
    return True
