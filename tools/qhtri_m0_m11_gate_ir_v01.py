from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from tools.qhtri_m0_m11_gate_fabric_v01 import (
    CompiledFabric,
    SCHEMA as FABRIC_SCHEMA,
)

IR_SCHEMA = "BIOOS_QHTRI_M0_M11_GATE_IR_V0_1"
IR_DOMAIN = b"BIOOS-QHTRI-M0-M11-GATE-IR/v0.1\x00"
RECEIPT_SCHEMA = "BIOOS_QHTRI_M0_M11_ANALOG_GATE_RECEIPT_V0_2"
RECEIPT_DOMAIN = b"BIOOS-QHTRI-M0-M11-RECEIPT/v0.2\x00"


class QHTRIGateIRError(ValueError):
    pass


def _f(value: float) -> str:
    return float(value).hex()


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def gate_ir(fabric: CompiledFabric) -> dict[str, Any]:
    k0 = []
    for term in fabric.anchors:
        k0.append({
            "layer": term.layer,
            "target_f64_hex": [_f(v) for v in term.target],
            "gain_f64_hex": [_f(v) for v in term.gain],
            "tau_f64_hex": _f(term.tau),
            "effect_carrying": bool(term.effect_carrying),
            "source_ref": term.source_ref,
        })
    k0.sort(key=lambda x: (x["layer"], str(x["source_ref"]), x["target_f64_hex"]))

    k1 = []
    for edge in fabric.torsion_edges:
        k1.append({
            "i": edge.i,
            "j": edge.j,
            "m": edge.m,
            "n": edge.n,
            "tau_f64_hex": _f(edge.tau),
            "K_f64_hex": _f(edge.K),
            "R_f64_hex": _f(edge.R),
            "effect_carrying": bool(edge.effect_carrying),
            "source_ref": edge.source_ref,
        })
    k1.sort(key=lambda x: (x["i"], x["j"], x["m"], x["n"], str(x["source_ref"])))

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

    core = {
        "schema": IR_SCHEMA,
        "source_fabric_schema": FABRIC_SCHEMA,
        "geometry": {
            "space": "T^36",
            "dimension": 36,
            "whole_semantic_lanes": True,
            "coordinate_position_mapping": False,
        },
        "kernel_families": {
            "K0_PHASE_LOCK_ANCHOR": k0,
            "K1_TORSION_COUPLING": k1,
            "K2_GAIN_MODULATION": k2,
            "K3_RECEIPT_OBSERVER": k3,
        },
        "layer_status": {k: str(v) for k, v in sorted(fabric.layer_status.items())},
        "authority_grant": False,
        "execution_admitted": False,
    }
    commitment = hashlib.blake2b(IR_DOMAIN + _canonical(core), digest_size=32).hexdigest()
    return {**core, "operator_profile_commitment": commitment}


def validate_gate_ir(ir: Mapping[str, Any]) -> bool:
    if ir.get("schema") != IR_SCHEMA:
        raise QHTRIGateIRError("unsupported QHTRI gate IR schema")
    geometry = ir.get("geometry")
    if not isinstance(geometry, Mapping):
        raise QHTRIGateIRError("missing gate IR geometry")
    if geometry.get("space") != "T^36" or int(geometry.get("dimension")) != 36:
        raise QHTRIGateIRError("invalid gate IR geometry")
    if geometry.get("whole_semantic_lanes") is not True:
        raise QHTRIGateIRError("whole semantic lanes required")
    if geometry.get("coordinate_position_mapping") is not False:
        raise QHTRIGateIRError("coordinate-position mapping forbidden")
    families = ir.get("kernel_families")
    if not isinstance(families, Mapping) or set(families) != {
        "K0_PHASE_LOCK_ANCHOR",
        "K1_TORSION_COUPLING",
        "K2_GAIN_MODULATION",
        "K3_RECEIPT_OBSERVER",
    }:
        raise QHTRIGateIRError("exact four-kernel family set required")
    if ir.get("authority_grant") is not False or ir.get("execution_admitted") is not False:
        raise QHTRIGateIRError("gate IR authority boundary violated")
    supplied = str(ir.get("operator_profile_commitment", ""))
    core = dict(ir)
    core.pop("operator_profile_commitment", None)
    expected = hashlib.blake2b(IR_DOMAIN + _canonical(core), digest_size=32).hexdigest()
    if supplied != expected:
        raise QHTRIGateIRError("operator profile commitment mismatch")
    return True


def make_m10_receipt_v2(
    step: Mapping[str, Any],
    fabric: CompiledFabric,
    *,
    hypercrystal_commitment: str | None = None,
    evidence_refs: Sequence[str] = (),
) -> dict[str, Any]:
    ir = gate_ir(fabric)
    validate_gate_ir(ir)
    if step.get("schema") != FABRIC_SCHEMA:
        raise QHTRIGateIRError("unsupported QHTRI step schema")
    if step.get("m10_receipt_enabled") is not True:
        raise QHTRIGateIRError("M10 receipt observer unavailable")

    core = {
        "schema": RECEIPT_SCHEMA,
        "gate_schema": FABRIC_SCHEMA,
        "operator_ir_schema": IR_SCHEMA,
        "operator_profile_commitment": ir["operator_profile_commitment"],
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
