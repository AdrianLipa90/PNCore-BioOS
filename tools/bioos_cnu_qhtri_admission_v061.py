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

SCHEMA = "BIOOS_C_NU_QHTRI_ADMISSION_ENVELOPE_V0_6_1"
DOMAIN = b"BIOOS-C-NU-QHTRI-ADMISSION/v0.6.1\x00"


class BioOSCNuQHTRIAdmissionV061Error(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _seal(value: Mapping[str, Any]) -> str:
    return hashlib.blake2b(DOMAIN + _canonical(value), digest_size=32).hexdigest()


def _unit_interval(value: float, name: str) -> float:
    x = float(value)
    if not math.isfinite(x) or not (0.0 <= x <= 1.0):
        raise BioOSCNuQHTRIAdmissionV061Error(f"{name} must be finite in [0,1]")
    return x


def _claim(binding: Mapping[str, Any], claim_id: str) -> Mapping[str, Any]:
    matches = [c for c in binding.get("claims", []) if isinstance(c, Mapping) and c.get("claim_id") == claim_id]
    if len(matches) != 1:
        raise BioOSCNuQHTRIAdmissionV061Error("exactly one bound canonical claim required")
    return matches[0]


def build_cnu_qhtri_admission_v061(
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
    """Build a zero-force M4/M11/M10 admission envelope for one C-Nu claim.

    This function binds canonical knowledge into the existing BioOS v0.5 gate
    fabric without creating a phase target, torsion edge, or execution grant.
    A later operator-binding step must supply its own provenance-bearing
    geometry and runtime authority.
    """

    try:
        validate_neutrino_canon_binding_v06(binding)
        evaluation = evaluate_c_nu_use_v06(
            binding,
            claim_id=claim_id,
            satisfied_preconditions=satisfied_preconditions,
            request_shared_absolute_spectrum=request_shared_absolute_spectrum,
        )
    except BioOSGremlinCanonBindingV06Error as exc:
        raise BioOSCNuQHTRIAdmissionV061Error(str(exc)) from exc

    claim = _claim(binding, claim_id)
    validator = _unit_interval(runtime_validator_confidence, "runtime_validator_confidence")
    capability = _unit_interval(capability_admission, "capability_admission")
    if capability > 0.0 and not str(capability_ref or ""):
        raise BioOSCNuQHTRIAdmissionV061Error(
            "positive capability admission requires provenance-bearing capability_ref"
        )

    precondition_open = bool(evaluation["missing_preconditions"])
    hard_no_go = bool(evaluation["m11_no_go"])
    knowledge_ready = bool(evaluation["m4_candidate_admitted"]) and not precondition_open and not hard_no_go

    effective_validator = validator if knowledge_ready else 0.0
    effective_capability = capability if knowledge_ready else 0.0

    # Deliberately omit every target and every M6 edge. The resulting v0.5
    # fabric carries admission/provenance state but cannot generate Kχ force.
    layer_frames = {
        "M4": {
            "procedure_match": 1.0,
            "validator_confidence": effective_validator,
            "capability_admission": effective_capability,
            "activation": 1.0,
            "claim_ref": claim_id,
            "capability_ref": capability_ref,
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
        raise BioOSCNuQHTRIAdmissionV061Error(
            "canon admission envelope must remain zero-force before operator binding"
        )

    if hard_no_go:
        status = "M11_NO_GO_ZERO_FORCE"
    elif precondition_open:
        status = "PRECONDITION_OPEN_ZERO_FORCE"
    elif effective_capability <= 0.0:
        status = "CAPABILITY_OPEN_ZERO_FORCE"
    else:
        status = "READY_FOR_SEPARATE_OPERATOR_BINDING_ZERO_FORCE"

    core = {
        "schema": SCHEMA,
        "claim_id": claim_id,
        "claim_role": str(claim["role"]),
        "claim_canon_status": str(claim["canon_status"]),
        "canon_binding_commitment": str(binding["canon_binding_commitment"]),
        "use_evaluation": evaluation,
        "runtime_validation": {
            "validator_confidence": validator,
            "capability_admission_requested": capability,
            "capability_ref": capability_ref,
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
        "operator_binding_required": True,
        "authority_grant": False,
        "execution_admitted": False,
        "production_runtime_write": False,
        "evidence_refs": sorted(str(v) for v in evidence_refs),
        "status": status,
    }
    return {**core, "admission_commitment": _seal(core)}


def validate_cnu_qhtri_admission_v061(envelope: Mapping[str, Any]) -> bool:
    if envelope.get("schema") != SCHEMA:
        raise BioOSCNuQHTRIAdmissionV061Error("unsupported C-Nu QHTRI admission envelope schema")
    if envelope.get("operator_binding_required") is not True:
        raise BioOSCNuQHTRIAdmissionV061Error("separate operator binding is required")
    if envelope.get("authority_grant") is not False or envelope.get("execution_admitted") is not False:
        raise BioOSCNuQHTRIAdmissionV061Error("admission envelope may not grant runtime authority")
    if envelope.get("production_runtime_write") is not False:
        raise BioOSCNuQHTRIAdmissionV061Error("admission envelope may not enable production runtime write")

    qhtri = envelope.get("qhtri_admission_ir")
    m = envelope.get("m0_m11_projection")
    if not isinstance(qhtri, Mapping) or not isinstance(m, Mapping):
        raise BioOSCNuQHTRIAdmissionV061Error("admission projection sections missing")
    if int(qhtri.get("character_term_count", -1)) != 0:
        raise BioOSCNuQHTRIAdmissionV061Error("pre-operator canon admission must contain zero character terms")
    if qhtri.get("force_status") != "ZERO_FORCE_ADMISSION_METADATA_ONLY":
        raise BioOSCNuQHTRIAdmissionV061Error("invalid pre-operator force status")
    if m.get("M10", {}).get("append_only") is not True:
        raise BioOSCNuQHTRIAdmissionV061Error("M10 must remain append-only")

    supplied = str(envelope.get("admission_commitment", ""))
    core = dict(envelope)
    core.pop("admission_commitment", None)
    if supplied != _seal(core):
        raise BioOSCNuQHTRIAdmissionV061Error("admission commitment mismatch")
    return True
