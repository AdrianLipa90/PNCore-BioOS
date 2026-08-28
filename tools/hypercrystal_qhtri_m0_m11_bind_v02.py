from __future__ import annotations

from typing import Any, Mapping, Sequence

from tools.hypercrystal_state_v01 import (
    HypercrystalComponent,
    component_from_semantic_state,
    compose_hypercrystal,
    validate_hypercrystal,
)


class HypercrystalQHTRIBindV02Error(ValueError):
    pass


def _state_memory_api():
    try:
        from pnv_state_memory import (
            semantic_commitment,
            semantic_normal_form,
            validate_m0_m11_execution_state_v02,
        )
    except ImportError as exc:
        raise HypercrystalQHTRIBindV02Error(
            "PNV-State-Memory QHTRI analog execution v0.2 API is required"
        ) from exc
    return semantic_commitment, semantic_normal_form, validate_m0_m11_execution_state_v02


def _single_relation(normal: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    matches = [r for r in normal["relations"] if r.get("relation") == name]
    if len(matches) != 1:
        raise HypercrystalQHTRIBindV02Error(f"expected exactly one relation: {name}")
    return matches[0]


def advance_hypercrystal_with_qhtri_v02(
    *,
    hypercrystal_before: Mapping[str, Any],
    identity_state: Mapping[str, Any],
    phase_after_state: Mapping[str, Any],
    qhtri_execution_state: Mapping[str, Any],
    state_memory_object_id: str | None = None,
    evidence_refs: Sequence[str] = (),
) -> dict[str, Any]:
    semantic_commitment, semantic_normal_form, validate_execution = _state_memory_api()

    validate_hypercrystal(hypercrystal_before)
    validate_execution(qhtri_execution_state)

    parent_hyper = str(hypercrystal_before["hypercrystal_semantic_commitment"])
    crystal_id = str(hypercrystal_before["identity_context"]["crystal_id"])

    execution_normal = semantic_normal_form(qhtri_execution_state)
    execution_identity = execution_normal["identity_context"]
    if execution_identity.get("hypercrystal_semantic_commitment") != parent_hyper:
        raise HypercrystalQHTRIBindV02Error("QHTRI execution parent Hypercrystal mismatch")
    if execution_identity.get("crystal_id") != crystal_id:
        raise HypercrystalQHTRIBindV02Error("QHTRI execution CRYSTAL_ID mismatch")

    identity_normal = semantic_normal_form(identity_state)
    if identity_normal.get("identity_context", {}).get("crystal_id") != crystal_id:
        raise HypercrystalQHTRIBindV02Error("identity state CRYSTAL_ID mismatch")

    operator_rel = _single_relation(execution_normal, "EXECUTES_OPERATOR_PROFILE")
    descendant_rel = _single_relation(execution_normal, "OPERATOR_PRODUCES_PHASE_DESCENDANT")
    parent_rel = _single_relation(execution_normal, "OPERATOR_BOUND_TO_HYPERCRYSTAL_PARENT")

    operator_commitment = str(execution_normal["semantic_evidence"]["operator_profile_commitment"])
    if str(operator_rel["target"]) != operator_commitment:
        raise HypercrystalQHTRIBindV02Error("operator-profile relation/evidence mismatch")
    if str(descendant_rel["source"]) != operator_commitment:
        raise HypercrystalQHTRIBindV02Error("operator-profile descendant source mismatch")
    if str(parent_rel["source"]) != operator_commitment or str(parent_rel["target"]) != parent_hyper:
        raise HypercrystalQHTRIBindV02Error("operator-profile parent binding mismatch")

    phase_after_commitment = semantic_commitment(phase_after_state)
    if str(descendant_rel["target"]) != phase_after_commitment:
        raise HypercrystalQHTRIBindV02Error("QHTRI phase descendant commitment mismatch")

    qhtri_component = component_from_semantic_state(
        "QHTRI",
        qhtri_execution_state,
        generation_ref=execution_normal["semantic_evidence"].get("gate_receipt_id"),
        projection_role=f"M0_M11_ANALOG_GATE_IR:{operator_commitment}",
    )

    carried: list[HypercrystalComponent] = []
    for raw in hypercrystal_before.get("components", []):
        role = str(raw.get("role")).upper()
        if role in {"IDENTITY", "PHASE", "QHTRI"}:
            continue
        carried.append(
            HypercrystalComponent(
                role=role,
                semantic_schema=str(raw["semantic_schema"]),
                semantic_commitment=str(raw["semantic_commitment"]),
                generation_ref=raw.get("generation_ref"),
                projection_role=raw.get("projection_role"),
            )
        )
    carried.append(qhtri_component)

    descendant = compose_hypercrystal(
        identity_state=identity_state,
        phase_state=phase_after_state,
        additional_components=carried,
        state_memory_object_id=state_memory_object_id,
        evidence_refs=[
            *hypercrystal_before.get("evidence_refs", []),
            *evidence_refs,
            parent_hyper,
            operator_commitment,
        ],
    )

    if descendant["identity_context"]["crystal_id"] != crystal_id:
        raise HypercrystalQHTRIBindV02Error("Hypercrystal descendant identity drift")
    if descendant["hypercrystal_semantic_commitment"] == parent_hyper:
        raise HypercrystalQHTRIBindV02Error("QHTRI execution must produce descendant Hypercrystal state")
    return descendant
