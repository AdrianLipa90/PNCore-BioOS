from __future__ import annotations

from typing import Any, Mapping, Sequence

from tools.hypercrystal_state_v01 import (
    HypercrystalComponent,
    HypercrystalStateError,
    component_from_semantic_state,
    compose_hypercrystal,
    validate_hypercrystal,
)


class HypercrystalQHTRIBindError(ValueError):
    pass


def _state_memory_api():
    try:
        from pnv_state_memory import (
            semantic_commitment,
            semantic_normal_form,
            validate_m0_m11_execution_state,
        )
    except ImportError as exc:
        raise HypercrystalQHTRIBindError(
            "PNV-State-Memory QHTRI analog semantic API is required"
        ) from exc
    return semantic_commitment, semantic_normal_form, validate_m0_m11_execution_state


def _component_by_role(hypercrystal: Mapping[str, Any], role: str) -> Mapping[str, Any]:
    for component in hypercrystal.get("components", []):
        if str(component.get("role")).upper() == role:
            return component
    raise HypercrystalQHTRIBindError(f"missing Hypercrystal component: {role}")


def _relation_target(state: Mapping[str, Any], relation_name: str) -> str:
    _, semantic_normal_form, _ = _state_memory_api()
    normal = semantic_normal_form(state)
    matches = [r for r in normal["relations"] if r.get("relation") == relation_name]
    if len(matches) != 1:
        raise HypercrystalQHTRIBindError(f"expected exactly one relation {relation_name}")
    return str(matches[0]["target"])


def advance_hypercrystal_with_qhtri(
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

    pre_commitment = str(hypercrystal_before["hypercrystal_semantic_commitment"])
    execution_normal = semantic_normal_form(qhtri_execution_state)
    execution_identity = execution_normal["identity_context"]
    if execution_identity.get("hypercrystal_semantic_commitment") != pre_commitment:
        raise HypercrystalQHTRIBindError("QHTRI execution is not bound to the supplied Hypercrystal parent")

    crystal_id = str(hypercrystal_before["identity_context"]["crystal_id"])
    if execution_identity.get("crystal_id") != crystal_id:
        raise HypercrystalQHTRIBindError("QHTRI execution CRYSTAL_ID mismatch")

    identity_normal = semantic_normal_form(identity_state)
    if identity_normal.get("identity_context", {}).get("crystal_id") != crystal_id:
        raise HypercrystalQHTRIBindError("identity state CRYSTAL_ID mismatch")

    phase_after_commitment = semantic_commitment(phase_after_state)
    declared_after = _relation_target(qhtri_execution_state, "PRODUCES_PHASE_DESCENDANT")
    if declared_after != phase_after_commitment:
        raise HypercrystalQHTRIBindError("QHTRI phase descendant commitment mismatch")

    qhtri_component = component_from_semantic_state(
        "QHTRI",
        qhtri_execution_state,
        generation_ref=execution_normal["semantic_evidence"].get("gate_receipt_id"),
        projection_role="M0_M11_ANALOG_GATE_FABRIC",
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
        evidence_refs=[*hypercrystal_before.get("evidence_refs", []), *evidence_refs, pre_commitment],
    )

    if descendant["identity_context"]["crystal_id"] != crystal_id:
        raise HypercrystalQHTRIBindError("Hypercrystal descendant identity drift")
    if descendant["hypercrystal_semantic_commitment"] == pre_commitment:
        raise HypercrystalQHTRIBindError("QHTRI descendant must produce a new Hypercrystal state commitment")

    return descendant
