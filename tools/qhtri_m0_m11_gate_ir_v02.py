from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from tools.qhtri_m0_m11_gate_fabric_v01 import (
    CompiledFabric,
    DIM,
    SCHEMA as FABRIC_SCHEMA,
    phase_vector,
    wrap_phase,
)

IR_SCHEMA = "BIOOS_QHTRI_M0_M11_GATE_IR_V0_2"
IR_DOMAIN = b"BIOOS-QHTRI-M0-M11-GATE-IR/v0.2\x00"
FIELD_DOMAIN = b"BIOOS-QHTRI-TORUS-CHARACTER-FIELD/v0.2\x00"
RECEIPT_SCHEMA = "BIOOS_QHTRI_M0_M11_ANALOG_GATE_RECEIPT_V0_3"
RECEIPT_DOMAIN = b"BIOOS-QHTRI-M0-M11-RECEIPT/v0.3\x00"


class QHTRIGateIRV02Error(ValueError):
    pass


def _f(value: float) -> str:
    x = float(value)
    if not math.isfinite(x):
        raise QHTRIGateIRV02Error("non-finite floating parameter")
    return x.hex()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _canonical_mode(ell: Sequence[int], tau: float) -> tuple[tuple[int, ...], float]:
    if len(ell) != DIM:
        raise QHTRIGateIRV02Error("lattice mode must contain exactly 36 integers")
    mode = tuple(int(v) for v in ell)
    if all(v == 0 for v in mode):
        raise QHTRIGateIRV02Error("zero lattice mode has zero phase force")
    first = next(v for v in mode if v != 0)
    phase = float(tau)
    if not math.isfinite(phase):
        raise QHTRIGateIRV02Error("character tau must be finite")
    if first < 0:
        mode = tuple(-v for v in mode)
        phase = -phase
    return mode, wrap_phase(phase)


def _math_term(term: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "ell": [int(v) for v in term["ell"]],
        "tau_f64_hex": str(term["tau_f64_hex"]),
        "gain_f64_hex": str(term["gain_f64_hex"]),
    }


def _field_core(profile_terms: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out = [_math_term(term) for term in profile_terms]
    out.sort(key=lambda x: (tuple(x["ell"]), x["tau_f64_hex"], x["gain_f64_hex"]))
    return out


def _character_terms(fabric: CompiledFabric) -> list[dict[str, Any]]:
    terms: list[dict[str, Any]] = []

    # Every anchor lane is one character with ell=e_j and phase offset target_j+tau.
    for anchor in fabric.anchors:
        for j, (target, gain) in enumerate(zip(anchor.target, anchor.gain)):
            ell = [0] * DIM
            ell[j] = 1
            mode, tau = _canonical_mode(ell, target + anchor.tau)
            terms.append({
                "layer": anchor.layer,
                "origin": "ANCHOR",
                "ell": list(mode),
                "tau_f64_hex": _f(tau),
                "gain_f64_hex": _f(gain),
                "effect_carrying": bool(anchor.effect_carrying),
                "source_ref": anchor.source_ref,
            })

    # Every m:n edge is one character with ell=n e_i-m e_j.
    for edge in fabric.torsion_edges:
        ell = [0] * DIM
        ell[edge.i] = edge.n
        ell[edge.j] = -edge.m
        mode, tau = _canonical_mode(ell, edge.tau)
        terms.append({
            "layer": "M6",
            "origin": "TORSION",
            "ell": list(mode),
            "tau_f64_hex": _f(tau),
            "gain_f64_hex": _f(edge.gain),
            "effect_carrying": bool(edge.effect_carrying),
            "source_ref": edge.source_ref,
        })

    terms.sort(
        key=lambda x: (
            x["layer"],
            x["origin"],
            tuple(x["ell"]),
            x["tau_f64_hex"],
            x["gain_f64_hex"],
            str(x["source_ref"]),
        )
    )
    return terms


def gate_ir_v02(fabric: CompiledFabric) -> dict[str, Any]:
    kchi = _character_terms(fabric)
    field_core = _field_core(kchi)
    field_commitment = hashlib.blake2b(FIELD_DOMAIN + _canonical(field_core), digest_size=32).hexdigest()

    k2 = {
        "m4_admission_f64_hex": _f(fabric.m4_admission),
        "m5_affect_multiplier_f64_hex": _f(fabric.affect_multiplier),
        "m11_closure_f64_hex": _f(fabric.closure),
        "m11_no_go_f64_hex": _f(fabric.no_go),
    }
    k3 = {
        "m10_receipt_enabled": bool(fabric.m10_receipt_enabled),
        "force": "ZERO",
        "mode": "APPEND_ONLY_OBSERVER",
    }

    active_reducers = []
    if str(fabric.layer_status.get("M3")) == "SEMANTIC_ATTRACTOR":
        active_reducers.append("M3")
    if str(fabric.layer_status.get("M7")) == "BRAID_ACTIVE":
        active_reducers.append("M7")

    core = {
        "schema": IR_SCHEMA,
        "source_fabric_schema": FABRIC_SCHEMA,
        "geometry": {
            "space": "T^36",
            "dual_lattice": "Z^36",
            "dimension": DIM,
            "whole_semantic_lanes": True,
            "coordinate_position_mapping": False,
            "force_kernel_families": 3,
        },
        "reducers": {
            "PHASE_CENTROID": {
                "role": "PARAMETER_REDUCER",
                "active_layers": active_reducers,
                "independent_force_law": False,
            }
        },
        "kernel_families": {
            "KCHI_TORUS_CHARACTER_FIELD": kchi,
            "K2_GAIN_MODULATION": k2,
            "K3_RECEIPT_OBSERVER": k3,
        },
        "character_field_commitment": field_commitment,
        "layer_status": {k: str(v) for k, v in sorted(fabric.layer_status.items())},
        "normalization": {
            "gain_nonnegative": True,
            "tau_principal_wrap": True,
            "first_nonzero_ell_positive": True,
            "gcd_reduction": False,
        },
        "authority_grant": False,
        "execution_admitted": False,
    }
    commitment = hashlib.blake2b(IR_DOMAIN + _canonical(core), digest_size=32).hexdigest()
    return {**core, "operator_profile_commitment": commitment}


def validate_gate_ir_v02(ir: Mapping[str, Any]) -> bool:
    if ir.get("schema") != IR_SCHEMA:
        raise QHTRIGateIRV02Error("unsupported QHTRI gate IR v0.2 schema")
    geometry = ir.get("geometry")
    if not isinstance(geometry, Mapping):
        raise QHTRIGateIRV02Error("missing gate IR geometry")
    if geometry.get("space") != "T^36" or geometry.get("dual_lattice") != "Z^36":
        raise QHTRIGateIRV02Error("invalid character geometry")
    if int(geometry.get("dimension")) != DIM or int(geometry.get("force_kernel_families")) != 3:
        raise QHTRIGateIRV02Error("invalid force-kernel factorization")
    if geometry.get("whole_semantic_lanes") is not True:
        raise QHTRIGateIRV02Error("whole semantic lanes required")
    if geometry.get("coordinate_position_mapping") is not False:
        raise QHTRIGateIRV02Error("coordinate-position mapping forbidden")

    families = ir.get("kernel_families")
    required = {
        "KCHI_TORUS_CHARACTER_FIELD",
        "K2_GAIN_MODULATION",
        "K3_RECEIPT_OBSERVER",
    }
    if not isinstance(families, Mapping) or set(families) != required:
        raise QHTRIGateIRV02Error("exact three-kernel family set required")

    terms = families["KCHI_TORUS_CHARACTER_FIELD"]
    if not isinstance(terms, list):
        raise QHTRIGateIRV02Error("character term list required")
    for term in terms:
        if not isinstance(term, Mapping):
            raise QHTRIGateIRV02Error("character term must be a mapping")
        mode, tau = _canonical_mode(term["ell"], float.fromhex(str(term["tau_f64_hex"])))
        if list(mode) != [int(v) for v in term["ell"]]:
            raise QHTRIGateIRV02Error("non-canonical character orientation")
        if _f(tau) != str(term["tau_f64_hex"]):
            raise QHTRIGateIRV02Error("non-canonical character tau")
        gain = float.fromhex(str(term["gain_f64_hex"]))
        if not math.isfinite(gain) or gain < 0.0:
            raise QHTRIGateIRV02Error("character gain must be finite and non-negative")

    norm = ir.get("normalization")
    if not isinstance(norm, Mapping) or norm.get("gcd_reduction") is not False:
        raise QHTRIGateIRV02Error("gcd normalization is forbidden")

    field_core = _field_core(terms)
    expected_field = hashlib.blake2b(FIELD_DOMAIN + _canonical(field_core), digest_size=32).hexdigest()
    if str(ir.get("character_field_commitment", "")) != expected_field:
        raise QHTRIGateIRV02Error("character field commitment mismatch")

    if ir.get("authority_grant") is not False or ir.get("execution_admitted") is not False:
        raise QHTRIGateIRV02Error("gate IR authority boundary violated")

    supplied = str(ir.get("operator_profile_commitment", ""))
    core = dict(ir)
    core.pop("operator_profile_commitment", None)
    expected = hashlib.blake2b(IR_DOMAIN + _canonical(core), digest_size=32).hexdigest()
    if supplied != expected:
        raise QHTRIGateIRV02Error("operator profile commitment mismatch")
    return True


def character_force(theta: Sequence[float], ir: Mapping[str, Any]) -> tuple[float, ...]:
    validate_gate_ir_v02(ir)
    state = phase_vector(theta, "theta")
    force = [0.0] * DIM
    terms = ir["kernel_families"]["KCHI_TORUS_CHARACTER_FIELD"]
    for term in terms:
        ell = tuple(int(v) for v in term["ell"])
        tau = float.fromhex(str(term["tau_f64_hex"]))
        gain = float.fromhex(str(term["gain_f64_hex"]))
        phase = math.fsum(c * t for c, t in zip(ell, state))
        epsilon = wrap_phase(phase - tau)
        s = gain * math.sin(epsilon)
        for j, coeff in enumerate(ell):
            if coeff:
                force[j] += -coeff * s
    return tuple(force)


def character_stability_bound(ir: Mapping[str, Any]) -> float:
    validate_gate_ir_v02(ir)
    terms = ir["kernel_families"]["KCHI_TORUS_CHARACTER_FIELD"]
    return math.fsum(
        float.fromhex(str(term["gain_f64_hex"]))
        * math.fsum(int(v) * int(v) for v in term["ell"])
        for term in terms
    )


def make_m10_receipt_v3(
    step: Mapping[str, Any],
    fabric: CompiledFabric,
    *,
    hypercrystal_commitment: str | None = None,
    evidence_refs: Sequence[str] = (),
) -> dict[str, Any]:
    ir = gate_ir_v02(fabric)
    validate_gate_ir_v02(ir)
    if step.get("schema") != FABRIC_SCHEMA:
        raise QHTRIGateIRV02Error("unsupported QHTRI step schema")
    if step.get("m10_receipt_enabled") is not True:
        raise QHTRIGateIRV02Error("M10 receipt observer unavailable")

    core = {
        "schema": RECEIPT_SCHEMA,
        "gate_schema": FABRIC_SCHEMA,
        "operator_ir_schema": IR_SCHEMA,
        "operator_profile_commitment": ir["operator_profile_commitment"],
        "character_field_commitment": ir["character_field_commitment"],
        "theta_before": step["theta_before"],
        "theta_after": step["theta_after"],
        "dt_used": step["dt_used"],
        "stability_bound": step["stability_bound"],
        "layer_status": step["layer_status"],
        "hypercrystal_commitment": hypercrystal_commitment,
        "evidence_refs": sorted(str(v) for v in evidence_refs),
        "authority_grant": False,
        "append_only": True,
    }
    receipt_id = hashlib.sha256(RECEIPT_DOMAIN + _canonical(core)).hexdigest()
    return {**core, "receipt_id": receipt_id}
