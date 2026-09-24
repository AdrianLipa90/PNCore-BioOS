from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

CAPABILITY_SCHEMA = "BIOOS-NOEMA-QHTRI-SEMANTIC-AUTONOMY-CAPABILITY/0.1"
EXECUTION_SCHEMA = "BIOOS-NOEMA-QHTRI-AUTONOMOUS-INTERNAL-EFFECT/0.1"
FEEDBACK_SCHEMA = "BIOOS-NOEMA-QHTRI-FEEDBACK-CANDIDATE/0.1"

L0 = "L0_OBSERVE_INTERPRET"
L1 = "L1_BOUNDED_INTERNAL_EFFECT"
L2 = "L2_AUTHORITY_EXPANSION_OR_EXTERNAL_EFFECT"


class SemanticAutonomyError(ValueError):
    pass


@dataclass(frozen=True)
class AutonomyDecision:
    level: str
    admitted: bool
    human_per_tick_authorization_required: bool
    reasons: tuple[str, ...]


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _seal(body: Mapping[str, Any], key: str) -> dict[str, Any]:
    if key in body:
        raise SemanticAutonomyError(f"seal key already present: {key}")
    return {**dict(body), key: _sha256(body)}


def _verify_seal(value: Mapping[str, Any], key: str) -> None:
    if key not in value:
        raise SemanticAutonomyError(f"missing seal: {key}")
    body = {k: v for k, v in value.items() if k != key}
    if value[key] != _sha256(body):
        raise SemanticAutonomyError(f"seal mismatch: {key}")


def _text(value: Any, name: str) -> str:
    text = str(value).strip()
    if not text:
        raise SemanticAutonomyError(f"{name} is required")
    return text


def _hex64(value: Any, name: str) -> str:
    text = str(value)
    if len(text) != 64:
        raise SemanticAutonomyError(f"{name} must be 64 hex characters")
    try:
        bytes.fromhex(text)
    except ValueError as exc:
        raise SemanticAutonomyError(f"{name} must be hexadecimal") from exc
    return text.lower()


def _nonnegative_int(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise SemanticAutonomyError(f"{name} must be an integer")
    try:
        integer = int(value)
    except (TypeError, ValueError) as exc:
        raise SemanticAutonomyError(f"{name} must be an integer") from exc
    if integer != value or integer < 0:
        raise SemanticAutonomyError(f"{name} must be a non-negative integer")
    return integer


def _positive_int(value: Any, name: str) -> int:
    integer = _nonnegative_int(value, name)
    if integer < 1:
        raise SemanticAutonomyError(f"{name} must be positive")
    return integer


def _nonnegative_finite(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise SemanticAutonomyError(f"{name} must be numeric") from exc
    if not math.isfinite(number) or number < 0.0:
        raise SemanticAutonomyError(f"{name} must be finite and non-negative")
    return number


def _unique_texts(values: Sequence[str], name: str) -> tuple[str, ...]:
    result = tuple(_text(v, name) for v in values)
    if not result:
        raise SemanticAutonomyError(f"{name} must contain at least one value")
    if len(result) != len(set(result)):
        raise SemanticAutonomyError(f"{name} contains duplicates")
    return result


def _strict_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise SemanticAutonomyError(f"{name} must be boolean")
    return value


def build_semantic_autonomy_capability(
    *,
    capability_id: str,
    issuer_authority_ref: str,
    pncap_capability_token: str,
    capability_epoch: int,
    valid_from_tick: int,
    expires_at_tick: int,
    allowed_qhtri_targets: Sequence[str],
    allowed_operator_classes: Sequence[str],
    max_internal_effects_per_epoch: int,
    max_memory_bytes_per_effect: int,
    max_energy_proxy_per_effect: float,
    allow_state_memory_append: bool = True,
    allow_qhtri_boundary_write: bool = True,
) -> dict[str, Any]:
    start = _nonnegative_int(valid_from_tick, "valid_from_tick")
    end = _nonnegative_int(expires_at_tick, "expires_at_tick")
    if end < start:
        raise SemanticAutonomyError("expires_at_tick must be >= valid_from_tick")

    body = {
        "schema": CAPABILITY_SCHEMA,
        "capability_id": _text(capability_id, "capability_id"),
        "issuer_authority_ref": _text(issuer_authority_ref, "issuer_authority_ref"),
        "pncap_capability_token": _text(pncap_capability_token, "pncap_capability_token"),
        "capability_epoch": _nonnegative_int(capability_epoch, "capability_epoch"),
        "valid_from_tick": start,
        "expires_at_tick": end,
        "allowed_qhtri_targets": list(_unique_texts(allowed_qhtri_targets, "allowed_qhtri_targets")),
        "allowed_operator_classes": list(_unique_texts(allowed_operator_classes, "allowed_operator_classes")),
        "max_internal_effects_per_epoch": _positive_int(
            max_internal_effects_per_epoch, "max_internal_effects_per_epoch"
        ),
        "max_memory_bytes_per_effect": _nonnegative_int(
            max_memory_bytes_per_effect, "max_memory_bytes_per_effect"
        ),
        "max_energy_proxy_per_effect": _nonnegative_finite(
            max_energy_proxy_per_effect, "max_energy_proxy_per_effect"
        ),
        "allow_state_memory_append": _strict_bool(allow_state_memory_append, "allow_state_memory_append"),
        "allow_qhtri_boundary_write": _strict_bool(allow_qhtri_boundary_write, "allow_qhtri_boundary_write"),
        "authority_expansion": False,
        "external_effect": False,
        "canon_write_authority": False,
        "identity_authority": False,
        "human_per_tick_authorization_required": False,
        "autonomy_level": L1,
    }
    return _seal(body, "capability_sha256")


def validate_semantic_autonomy_capability(capability: Mapping[str, Any]) -> None:
    if capability.get("schema") != CAPABILITY_SCHEMA:
        raise SemanticAutonomyError("invalid semantic autonomy capability schema")
    _text(capability.get("capability_id"), "capability_id")
    _text(capability.get("issuer_authority_ref"), "issuer_authority_ref")
    _text(capability.get("pncap_capability_token"), "pncap_capability_token")
    _nonnegative_int(capability.get("capability_epoch"), "capability_epoch")
    start = _nonnegative_int(capability.get("valid_from_tick"), "valid_from_tick")
    end = _nonnegative_int(capability.get("expires_at_tick"), "expires_at_tick")
    if end < start:
        raise SemanticAutonomyError("capability tick window is inverted")
    _unique_texts(tuple(capability.get("allowed_qhtri_targets", ())), "allowed_qhtri_targets")
    _unique_texts(tuple(capability.get("allowed_operator_classes", ())), "allowed_operator_classes")
    _positive_int(capability.get("max_internal_effects_per_epoch"), "max_internal_effects_per_epoch")
    _nonnegative_int(capability.get("max_memory_bytes_per_effect"), "max_memory_bytes_per_effect")
    _nonnegative_finite(capability.get("max_energy_proxy_per_effect"), "max_energy_proxy_per_effect")
    _strict_bool(capability.get("allow_state_memory_append"), "allow_state_memory_append")
    _strict_bool(capability.get("allow_qhtri_boundary_write"), "allow_qhtri_boundary_write")
    for forbidden in ("authority_expansion", "external_effect", "canon_write_authority", "identity_authority"):
        if capability.get(forbidden) is not False:
            raise SemanticAutonomyError(f"bounded capability crossed {forbidden} boundary")
    if capability.get("human_per_tick_authorization_required") is not False:
        raise SemanticAutonomyError("bounded capability must not require per-tick human authorization")
    if capability.get("autonomy_level") != L1:
        raise SemanticAutonomyError("bounded capability autonomy level mismatch")
    _verify_seal(capability, "capability_sha256")


def classify_semantic_action(
    *,
    observe_or_interpret_only: bool = False,
    qhtri_boundary_write: bool = False,
    state_memory_append: bool = False,
    external_effect: bool = False,
    authority_expansion: bool = False,
    canon_promotion: bool = False,
    identity_layer_mutation: bool = False,
) -> str:
    flags = (
        observe_or_interpret_only,
        qhtri_boundary_write,
        state_memory_append,
        external_effect,
        authority_expansion,
        canon_promotion,
        identity_layer_mutation,
    )
    if not all(isinstance(v, bool) for v in flags):
        raise SemanticAutonomyError("semantic action flags must be boolean")
    if external_effect or authority_expansion or canon_promotion or identity_layer_mutation:
        return L2
    if qhtri_boundary_write or state_memory_append:
        return L1
    return L0


def decide_semantic_action(
    *,
    level: str,
    capability: Mapping[str, Any] | None = None,
    current_tick: int | None = None,
    effect_index: int | None = None,
    qhtri_target_ref: str | None = None,
    operator_class: str | None = None,
    estimated_memory_bytes: int = 0,
    estimated_energy_proxy: float = 0.0,
    state_memory_append: bool = False,
    qhtri_boundary_write: bool = False,
) -> AutonomyDecision:
    if level == L0:
        return AutonomyDecision(L0, True, False, ("SEMANTIC_AUTONOMY",))
    if level == L2:
        return AutonomyDecision(L2, False, True, ("EXPLICIT_AUTHORITY_REQUIRED",))
    if level != L1:
        raise SemanticAutonomyError(f"unknown autonomy level: {level}")
    if capability is None:
        return AutonomyDecision(L1, False, False, ("CAPABILITY_REQUIRED",))

    validate_semantic_autonomy_capability(capability)
    tick = _nonnegative_int(current_tick, "current_tick")
    index = _nonnegative_int(effect_index, "effect_index")
    target = _text(qhtri_target_ref, "qhtri_target_ref")
    op_class = _text(operator_class, "operator_class")
    memory = _nonnegative_int(estimated_memory_bytes, "estimated_memory_bytes")
    energy = _nonnegative_finite(estimated_energy_proxy, "estimated_energy_proxy")
    append_requested = _strict_bool(state_memory_append, "state_memory_append")
    boundary_requested = _strict_bool(qhtri_boundary_write, "qhtri_boundary_write")

    failures: list[str] = []
    if tick < capability["valid_from_tick"] or tick > capability["expires_at_tick"]:
        failures.append("CAPABILITY_TICK_WINDOW")
    if index >= capability["max_internal_effects_per_epoch"]:
        failures.append("EFFECT_BUDGET")
    if target not in capability["allowed_qhtri_targets"]:
        failures.append("TARGET_SCOPE")
    if op_class not in capability["allowed_operator_classes"]:
        failures.append("OPERATOR_SCOPE")
    if memory > capability["max_memory_bytes_per_effect"]:
        failures.append("MEMORY_BUDGET")
    if energy > capability["max_energy_proxy_per_effect"]:
        failures.append("ENERGY_BUDGET")
    if append_requested and capability["allow_state_memory_append"] is not True:
        failures.append("STATE_MEMORY_SCOPE")
    if boundary_requested and capability["allow_qhtri_boundary_write"] is not True:
        failures.append("QHTRI_BOUNDARY_SCOPE")

    if failures:
        return AutonomyDecision(L1, False, False, tuple(failures))
    return AutonomyDecision(L1, True, False, ("BOUNDED_CAPABILITY_ADMITTED",))


def _validate_feedback_candidate(feedback: Mapping[str, Any]) -> None:
    if feedback.get("schema") != FEEDBACK_SCHEMA:
        raise SemanticAutonomyError("invalid feedback candidate schema")
    _hex64(feedback.get("bank_manifest_sha256"), "bank_manifest_sha256")
    _hex64(feedback.get("state_crystal_receipt_sha256"), "state_crystal_receipt_sha256")
    _hex64(feedback.get("hermitian_operator_commitment"), "hermitian_operator_commitment")
    _text(feedback.get("pncap_admission_token"), "pncap_admission_token")
    _text(feedback.get("qhtri_target_ref"), "qhtri_target_ref")
    if feedback.get("effect_policy") != "OPERATOR_BINDABLE":
        raise SemanticAutonomyError("feedback candidate effect policy mismatch")
    if feedback.get("execution_admitted") is not False:
        raise SemanticAutonomyError("feedback candidate must remain pre-execution")
    if feedback.get("production_runtime_write") is not False:
        raise SemanticAutonomyError("feedback candidate must remain pre-write")
    _verify_seal(feedback, "feedback_receipt_sha256")


def build_autonomous_feedback_execution_receipt(
    feedback_receipt: Mapping[str, Any],
    capability: Mapping[str, Any],
    *,
    operator_class: str,
    current_tick: int,
    effect_index: int,
    estimated_memory_bytes: int = 0,
    estimated_energy_proxy: float = 0.0,
    state_memory_append: bool = False,
) -> dict[str, Any]:
    _validate_feedback_candidate(feedback_receipt)
    validate_semantic_autonomy_capability(capability)
    append_requested = _strict_bool(state_memory_append, "state_memory_append")

    decision = decide_semantic_action(
        level=L1,
        capability=capability,
        current_tick=current_tick,
        effect_index=effect_index,
        qhtri_target_ref=feedback_receipt["qhtri_target_ref"],
        operator_class=operator_class,
        estimated_memory_bytes=estimated_memory_bytes,
        estimated_energy_proxy=estimated_energy_proxy,
        state_memory_append=append_requested,
        qhtri_boundary_write=True,
    )
    if not decision.admitted:
        raise SemanticAutonomyError("bounded internal feedback denied: " + ",".join(decision.reasons))

    body = {
        "schema": EXECUTION_SCHEMA,
        "autonomy_level": L1,
        "feedback_receipt_sha256": feedback_receipt["feedback_receipt_sha256"],
        "feedback_pncap_admission_token": feedback_receipt["pncap_admission_token"],
        "capability_sha256": capability["capability_sha256"],
        "capability_id": capability["capability_id"],
        "capability_epoch": capability["capability_epoch"],
        "pncap_capability_token": capability["pncap_capability_token"],
        "operator_class": _text(operator_class, "operator_class"),
        "hermitian_operator_commitment": feedback_receipt["hermitian_operator_commitment"],
        "qhtri_target_ref": feedback_receipt["qhtri_target_ref"],
        "current_tick": _nonnegative_int(current_tick, "current_tick"),
        "effect_index": _nonnegative_int(effect_index, "effect_index"),
        "estimated_memory_bytes": _nonnegative_int(estimated_memory_bytes, "estimated_memory_bytes"),
        "estimated_energy_proxy": _nonnegative_finite(estimated_energy_proxy, "estimated_energy_proxy"),
        "state_memory_append": append_requested,
        "qhtri_boundary_write": True,
        "internal_effect_admitted": True,
        "human_per_tick_authorization_required": False,
        "authority_expansion": False,
        "external_effect": False,
        "canon_promotion": False,
        "identity_layer_mutation": False,
        "runtime_write_scope": "QHTRI_BOUNDARY_ONLY",
        "decision_reasons": list(decision.reasons),
    }
    return _seal(body, "autonomous_execution_receipt_sha256")


def validate_autonomous_feedback_execution_receipt(
    receipt: Mapping[str, Any],
    *,
    feedback_receipt: Mapping[str, Any],
    capability: Mapping[str, Any],
) -> None:
    _validate_feedback_candidate(feedback_receipt)
    validate_semantic_autonomy_capability(capability)
    if receipt.get("schema") != EXECUTION_SCHEMA or receipt.get("autonomy_level") != L1:
        raise SemanticAutonomyError("autonomous execution schema/level mismatch")
    if receipt.get("feedback_receipt_sha256") != feedback_receipt["feedback_receipt_sha256"]:
        raise SemanticAutonomyError("autonomous execution feedback parent mismatch")
    if receipt.get("feedback_pncap_admission_token") != feedback_receipt["pncap_admission_token"]:
        raise SemanticAutonomyError("feedback PNCAP token mismatch")
    if receipt.get("capability_sha256") != capability["capability_sha256"]:
        raise SemanticAutonomyError("autonomous execution capability parent mismatch")
    if receipt.get("capability_id") != capability["capability_id"]:
        raise SemanticAutonomyError("capability id mismatch")
    if receipt.get("capability_epoch") != capability["capability_epoch"]:
        raise SemanticAutonomyError("capability epoch mismatch")
    if receipt.get("pncap_capability_token") != capability["pncap_capability_token"]:
        raise SemanticAutonomyError("capability PNCAP token mismatch")
    if receipt.get("hermitian_operator_commitment") != feedback_receipt["hermitian_operator_commitment"]:
        raise SemanticAutonomyError("operator commitment mismatch")
    if receipt.get("qhtri_target_ref") != feedback_receipt["qhtri_target_ref"]:
        raise SemanticAutonomyError("QHTRI target mismatch")
    if receipt.get("internal_effect_admitted") is not True:
        raise SemanticAutonomyError("internal effect admission missing")
    if receipt.get("human_per_tick_authorization_required") is not False:
        raise SemanticAutonomyError("per-tick human authorization unexpectedly required")
    for forbidden in ("authority_expansion", "external_effect", "canon_promotion", "identity_layer_mutation"):
        if receipt.get(forbidden) is not False:
            raise SemanticAutonomyError(f"autonomous execution crossed {forbidden} boundary")
    if receipt.get("runtime_write_scope") != "QHTRI_BOUNDARY_ONLY":
        raise SemanticAutonomyError("autonomous runtime write scope mismatch")
    if receipt.get("qhtri_boundary_write") is not True:
        raise SemanticAutonomyError("autonomous QHTRI boundary write marker missing")
    append_requested = _strict_bool(receipt.get("state_memory_append"), "state_memory_append")

    decision = decide_semantic_action(
        level=L1,
        capability=capability,
        current_tick=receipt.get("current_tick"),
        effect_index=receipt.get("effect_index"),
        qhtri_target_ref=receipt.get("qhtri_target_ref"),
        operator_class=receipt.get("operator_class"),
        estimated_memory_bytes=receipt.get("estimated_memory_bytes"),
        estimated_energy_proxy=receipt.get("estimated_energy_proxy"),
        state_memory_append=append_requested,
        qhtri_boundary_write=True,
    )
    if not decision.admitted:
        raise SemanticAutonomyError("execution receipt is outside capability: " + ",".join(decision.reasons))
    if receipt.get("decision_reasons") != list(decision.reasons):
        raise SemanticAutonomyError("autonomy decision reasons mismatch")
    _verify_seal(receipt, "autonomous_execution_receipt_sha256")
