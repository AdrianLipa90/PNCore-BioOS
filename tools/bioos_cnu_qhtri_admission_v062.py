from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from tools.bioos_gremlin_canon_binding_v06 import (
    BioOSGremlinCanonBindingV06Error,
    evaluate_c_nu_use_v06,
    validate_neutrino_canon_binding_v06,
)
from tools.qhtri_m0_m11_gate_fabric_v01 import compile_gate_fabric
from tools.qhtri_m0_m11_gate_ir_v02 import gate_ir_v02, validate_gate_ir_v02

SCHEMA = "BIOOS_C_NU_QHTRI_ADMISSION_ENVELOPE_V0_6_2"
DOMAIN = b"BIOOS-C-NU-QHTRI-ADMISSION/v0.6.2\x00"

OPERATOR_BINDABLE_POLICY = "M4_AND_M11_GATED"
KNOWLEDGE_ONLY_POLICY = "KNOWLEDGE_FIREWALL_NO_DIRECT_EFFECT"
ENFORCEMENT_ONLY_POLICY = "HARD_NO_GO_ON_SHARED_ABSOLUTE_SPECTRUM"
SUPPORTED_EFFECT_POLICIES = {
    OPERATOR_BINDABLE_POLICY,
    KNOWLEDGE_ONLY_POLICY,
    ENFORCEMENT_ONLY_POLICY,
}


class BioOSCNuQHTRIAdmissionV062Error(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _seal(value: Mapping[str, Any]) -> str:
    return hashlib.blake2b(DOMAIN + _canonical(value), digest_size=32).hexdigest()


def _unit_interval(value: float, name: str) -> float:
    x = float(value)
    if not math.isfinite(x) or not (0.0 <= x <= 1.0):
        raise BioOSCNuQHTRIAdmissionV062Error(f"{name} must be finite in [0,1]")
    return x


def _claim(binding: Mapping[str, Any], claim_id: str) -> Mapping[str, Any]:
    matches = [c for c in binding.get("claims", []) if isinstance(c, Mapping) and c.get("claim_id") == claim_id]
    if len(matches) != 1:
        raise BioOSCNuQHTRIAdmissionV062Error("exactly one bound canonical claim required")
    return matches[0]


def _binding_mode(effect_policy: str) -> str:
    if effect_policy == OPERATOR_BINDABLE_POLICY:
        return "OPERATOR_BINDABLE"
    if effect_policy == KNOWLEDGE_ONLY_POLICY:
        return "KNOWLEDGE_ONLY"
    if effect_policy == ENFORCEMENT_ONLY_POLICY:
        return "ENFORCEMENT_ONLY"
    raise BioOSCNuQHTRIAdmissionV062Error(f"unsupported claim effect policy: {effect_policy}")


def build_cnu_qhtri_admission_v062(
    binding: Mapping[str, Any],
    *,
    claim_id: str,
    satisfied_preconditions: Sequence[str] = (),
    request_shared_absolute_spectrum: bool = False,
    runtime_validator_confidence: float = 1.0,
    capability_admission: float = 0.0,
    capability_ref: str | None = None,
    evidence_refs: Sequence[str] = (),
) -> dict[str, Any]:
    """Build a zero-force M4/M11/M10 envelope with effect-policy separation.

    Only claims whose canonical effect policy is explicitly operator-bindable may
    carry positive capability metadata toward a later operator-binding step.
    Knowledge-only and enforcement-only claims stay permanently outside that path.
    """

    try:
        validate_neutrino_canon_binding_v06(binding)
    except BioOSGremlinCanonBindingV06Error as exc:
        raise BioOSCNuQHTRIAdmissionV062Error(str(exc)) from exc

    claim = _claim(binding, claim_id)
    effect_policy = str(claim.get("effect_policy", ""))
    if effect_policy not in SUPPORTED_EFFECT_POLICIES:
        raise BioOSCNuQHTRIAdmissionV062Error("canonical claim effect policy is not supported")
    binding_mode = _binding_mode(effect_policy)
    operator_bindable = binding_mode == "OPERATOR_BINDABLE"

    preconditions = sorted({str(v) for v in satisfied_preconditions})
    evidence = sorted(str(v) for v in evidence_refs)
    validator = _unit_interval(runtime_validator_confidence, "runtime_validator_confidence")
    capability = _unit_interval(capability_admission, "capability_admission")
    capability_ref_normalized = str(capability_ref) if capability_ref is not None else None

    if bool(request_shared_absolute_spectrum) and claim_id != "C-Nu-3":
        raise BioOSCNuQHTRIAdmissionV062Error(
            "shared absolute spectrum requests must traverse the C-Nu-3 enforcement firewall"
        )
    if not operator_bindable and capability_ref_normalized is not None:
        raise BioOSCNuQHTRIAdmissionV062Error(
            "non-operator claim may not carry capability_ref"
        )
    if capability > 0.0 and not operator_bindable:
        raise BioOSCNuQHTRIAdmissionV062Error(
            "claim effect policy forbids capability admission and operator binding"
        )
    if capability > 0.0 and not str(capability_ref_normalized or ""):
        raise BioOSCNuQHTRIAdmissionV062Error(
            "positive capability admission requires provenance-bearing capability_ref"
        )

    try:
        evaluation = evaluate_c_nu_use_v06(
            binding,
            claim_id=claim_id,
            satisfied_preconditions=preconditions,
            request_shared_absolute_spectrum=bool(request_shared_absolute_spectrum),
        )
    except BioOSGremlinCanonBindingV06Error as exc:
        raise BioOSCNuQHTRIAdmissionV062Error(str(exc)) from exc

    precondition_open = bool(evaluation["missing_preconditions"])
    hard_no_go = bool(evaluation["m11_no_go"])
    knowledge_ready = bool(evaluation["m4_candidate_admitted"]) and not precondition_open and not hard_no_go

    effective_validator = validator if knowledge_ready else 0.0
    effective_capability = capability if knowledge_ready and operator_bindable else 0.0

    layer_frames = {
        "M4": {
            "procedure_match": 1.0,
            "validator_confidence": effective_validator,
            "capability_admission": effective_capability,
            "activation": 1.0,
            "claim_ref": claim_id,
            "capability_ref": capability_ref_normalized,
        },
        "M10": {
            "append_only": True,
            "claim_ref": claim_id,
            "canon_binding_commitment": binding["canon_binding_commitment"],
        },
        "M11": {
            "validation_confidence": effective_validator,
            "uncertainty": 1.0 if precondition_open else 0.0,
            "no_go": 1.0 if hard_no_go else 0.0,
            "claim_ref": claim_id,
        },
    }

    fabric = compile_gate_fabric(layer_frames)
    ir = gate_ir_v02(fabric)
    validate_gate_ir_v02(ir)

    character_terms = ir["kernel_families"]["KCHI_TORUS_CHARACTER_FIELD"]
    if character_terms:
        raise BioOSCNuQHTRIAdmissionV062Error(
            "canon admission envelope must remain zero-force before operator binding"
        )

    if hard_no_go:
        status = "M11_NO_GO_ZERO_FORCE"
    elif precondition_open:
        status = "PRECONDITION_OPEN_ZERO_FORCE"
    elif binding_mode == "KNOWLEDGE_ONLY":
        status = "KNOWLEDGE_ONLY_ZERO_FORCE"
    elif binding_mode == "ENFORCEMENT_ONLY":
        status = "FIREWALL_CLEAR_ZERO_FORCE"
    elif effective_capability <= 0.0:
        status = "CAPABILITY_OPEN_ZERO_FORCE"
    else:
        status = "READY_FOR_SEPARATE_OPERATOR_BINDING_ZERO_FORCE"

    request = {
        "claim_id": claim_id,
        "satisfied_preconditions": preconditions,
        "request_shared_absolute_spectrum": bool(request_shared_absolute_spectrum),
        "runtime_validator_confidence": validator,
        "capability_admission": capability,
        "capability_ref": capability_ref_normalized,
        "evidence_refs": evidence,
    }

    core = {
        "schema": SCHEMA,
        "request": request,
        "claim_id": claim_id,
        "claim_role": str(claim["role"]),
        "claim_canon_status": str(claim["canon_status"]),
        "claim_effect_policy": effect_policy,
        "binding_mode": binding_mode,
        "canon_binding_commitment": str(binding["canon_binding_commitment"]),
        "use_evaluation": evaluation,
        "runtime_validation": {
            "validator_confidence": validator,
            "capability_admission_requested": capability,
            "capability_ref": capability_ref_normalized,
            "effective_validator_confidence": effective_validator,
            "effective_capability_admission": effective_capability,
        },
        "m0_m11_projection": {
            "M4": {
                "admission": float(fabric.m4_admission),
                "status": str(fabric.layer_status["M4"]),
            },
            "M10": {
                "append_only": bool(fabric.m10_receipt_enabled),
                "status": str(fabric.layer_status["M10"]),
            },
            "M11": {
                "closure": float(fabric.closure),
                "no_go": float(fabric.no_go),
                "status": str(fabric.layer_status["M11"]),
            },
        },
        "qhtri_admission_ir": {
            "schema": str(ir["schema"]),
            "operator_profile_commitment": str(ir["operator_profile_commitment"]),
            "character_field_commitment": str(ir["character_field_commitment"]),
            "character_term_count": len(character_terms),
            "force_status": "ZERO_FORCE_ADMISSION_METADATA_ONLY",
        },
        "operator_binding_required": operator_bindable,
        "authority_grant": False,
        "execution_admitted": False,
        "production_runtime_write": False,
        "evidence_refs": evidence,
        "status": status,
    }
    return {**core, "admission_commitment": _seal(core)}


def validate_cnu_qhtri_admission_v062(
    envelope: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> bool:
    """Validate structurally and by deterministic replay from the canon binding."""

    try:
        validate_neutrino_canon_binding_v06(binding)
    except BioOSGremlinCanonBindingV06Error as exc:
        raise BioOSCNuQHTRIAdmissionV062Error(str(exc)) from exc

    if envelope.get("schema") != SCHEMA:
        raise BioOSCNuQHTRIAdmissionV062Error("unsupported C-Nu QHTRI admission envelope schema")
    if envelope.get("canon_binding_commitment") != binding.get("canon_binding_commitment"):
        raise BioOSCNuQHTRIAdmissionV062Error("canon binding commitment mismatch")
    if envelope.get("authority_grant") is not False or envelope.get("execution_admitted") is not False:
        raise BioOSCNuQHTRIAdmissionV062Error("admission envelope may not grant runtime authority")
    if envelope.get("production_runtime_write") is not False:
        raise BioOSCNuQHTRIAdmissionV062Error("admission envelope may not enable production runtime write")

    qhtri = envelope.get("qhtri_admission_ir")
    m = envelope.get("m0_m11_projection")
    request = envelope.get("request")
    runtime_validation = envelope.get("runtime_validation")
    if not isinstance(qhtri, Mapping) or not isinstance(m, Mapping) or not isinstance(request, Mapping) or not isinstance(runtime_validation, Mapping):
        raise BioOSCNuQHTRIAdmissionV062Error("admission projection/request sections missing")
    if int(qhtri.get("character_term_count", -1)) != 0:
        raise BioOSCNuQHTRIAdmissionV062Error("pre-operator canon admission must contain zero character terms")
    if qhtri.get("force_status") != "ZERO_FORCE_ADMISSION_METADATA_ONLY":
        raise BioOSCNuQHTRIAdmissionV062Error("invalid pre-operator force status")
    if m.get("M10", {}).get("append_only") is not True:
        raise BioOSCNuQHTRIAdmissionV062Error("M10 must remain append-only")

    claim = _claim(binding, str(envelope.get("claim_id", "")))
    expected_policy = str(claim.get("effect_policy", ""))
    expected_mode = _binding_mode(expected_policy)
    if envelope.get("claim_effect_policy") != expected_policy:
        raise BioOSCNuQHTRIAdmissionV062Error("claim effect policy mismatch")
    if envelope.get("binding_mode") != expected_mode:
        raise BioOSCNuQHTRIAdmissionV062Error("claim binding mode mismatch")
    if envelope.get("operator_binding_required") is not (expected_mode == "OPERATOR_BINDABLE"):
        raise BioOSCNuQHTRIAdmissionV062Error("operator-binding eligibility mismatch")
    if expected_mode != "OPERATOR_BINDABLE" and float(runtime_validation.get("effective_capability_admission", -1.0)) != 0.0:
        raise BioOSCNuQHTRIAdmissionV062Error("non-operator claim carries effective capability")

    supplied = str(envelope.get("admission_commitment", ""))
    core = dict(envelope)
    core.pop("admission_commitment", None)
    if supplied != _seal(core):
        raise BioOSCNuQHTRIAdmissionV062Error("admission commitment mismatch")

    try:
        rebuilt = build_cnu_qhtri_admission_v062(
            binding,
            claim_id=str(request["claim_id"]),
            satisfied_preconditions=request.get("satisfied_preconditions", ()),
            request_shared_absolute_spectrum=bool(request.get("request_shared_absolute_spectrum", False)),
            runtime_validator_confidence=float(request.get("runtime_validator_confidence", 1.0)),
            capability_admission=float(request.get("capability_admission", 0.0)),
            capability_ref=request.get("capability_ref"),
            evidence_refs=request.get("evidence_refs", ()),
        )
    except (KeyError, TypeError, ValueError, BioOSCNuQHTRIAdmissionV062Error) as exc:
        raise BioOSCNuQHTRIAdmissionV062Error("admission deterministic replay failed") from exc

    if _canonical(envelope) != _canonical(rebuilt):
        raise BioOSCNuQHTRIAdmissionV062Error("admission deterministic replay mismatch")
    return True
