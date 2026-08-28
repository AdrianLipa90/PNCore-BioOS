from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

SCHEMA = "BIOOS_GREMLIN_NEUTRINO_CANON_IR_V0_6"
DOMAIN = b"BIOOS-GREMLIN-NEUTRINO-CANON-IR/v0.6\x00"
RECEIPT_SCHEMA = "BIOOS_GREMLIN_NEUTRINO_CANON_M10_RECEIPT_V0_6"
RECEIPT_DOMAIN = b"BIOOS-GREMLIN-NEUTRINO-CANON-M10/v0.6\x00"

GREMLIN_REPOSITORY = "AdrianLipa90/GREMLIN"
GREMLIN_CANON_COMMIT = "76a2d6b46e485723eeaa0a97badd2dae6b9b3b14"
GREMLIN_LEDGER_PATH = "spec/GREMLIN_NEUTRINO_CANON_LEDGER_V2_4.md"
GREMLIN_LEDGER_BLOB_SHA = "13c058b095ff734512dab1de8455eb73eeb637e2"
BIOOS_PARENT_V05 = "9e7724a481a90845485854ad28a3866be0e2caf5"

CLAIMS: dict[str, dict[str, Any]] = {
    "C-Nu-1": {
        "status": "CANONICAL_CONDITIONAL",
        "role": "COMPLEX_OVERLAP_FRAME_BRIDGE",
        "layers": ["M3", "M4", "M6", "M9", "M10", "M11"],
        "precondition": "SOURCE_BOUND_ORTHONORMAL_NEUTRINO_FRAME_AND_PMNS_ORIENTATION",
        "open_debt": "NEUTRINO_FRAME_TO_H_I_SOURCE_BINDING",
    },
    "C-Nu-2": {
        "status": "CANONICAL",
        "role": "PROBABILITY_SHADOW_FIREWALL",
        "layers": ["M6", "M10", "M11"],
        "precondition": "RETAIN_COMPLEX_OVERLAPS_WHEN_RELATIVE_PHASE_IS_DOWNSTREAM_RELEVANT",
        "open_debt": None,
    },
    "C-Nu-3": {
        "status": "CANONICAL_FIREWALL",
        "role": "CROSS_FRAMEWORK_NEUTRINO_SPECTRUM_HOLONOMY_FIREWALL",
        "layers": ["M4", "M9", "M10", "M11"],
        "precondition": "ABSOLUTE_SPECTRUM_USAGE_MUST_DECLARE_FRAMEWORK_BRANCH",
        "open_debt": "NEUTRINO_SPECTRUM_CROSS_FRAMEWORK_HOLONOMY",
    },
}

SHARED_ABSOLUTE_SCOPE = "SHARED_ABSOLUTE_NEUTRINO_SPECTRUM"
BRANCH_SCOPES = {
    "GRADED_PROJECTION_BRANCH",
    "TIR_TETRAHEDRON_BRANCH",
}


class BioOSCanonBindingV06Error(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def authority_snapshot() -> dict[str, str]:
    return {
        "repository": GREMLIN_REPOSITORY,
        "canon_commit": GREMLIN_CANON_COMMIT,
        "ledger_path": GREMLIN_LEDGER_PATH,
        "ledger_blob_sha": GREMLIN_LEDGER_BLOB_SHA,
        "bioos_parent_v05": BIOOS_PARENT_V05,
    }


def validate_authority_snapshot(snapshot: Mapping[str, Any]) -> bool:
    expected = authority_snapshot()
    if dict(snapshot) != expected:
        raise BioOSCanonBindingV06Error("GREMLIN canonical authority snapshot mismatch")
    return True


def _claim_record(claim_id: str) -> dict[str, Any]:
    try:
        claim = CLAIMS[str(claim_id)]
    except KeyError as exc:
        raise BioOSCanonBindingV06Error(f"unknown canonical claim: {claim_id}") from exc
    return {
        "claim_id": str(claim_id),
        "status": claim["status"],
        "role": claim["role"],
        "m0_m11_layers": list(claim["layers"]),
        "precondition": claim["precondition"],
        "open_debt": claim["open_debt"],
    }


def build_canon_ir_v06(
    *,
    claim_ids: Sequence[str] = ("C-Nu-1", "C-Nu-2", "C-Nu-3"),
    usage_scope: str = "KNOWLEDGE_BINDING_ONLY",
    source_snapshot: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    snapshot = dict(source_snapshot or authority_snapshot())
    validate_authority_snapshot(snapshot)

    ids = [str(v) for v in claim_ids]
    if not ids or len(ids) != len(set(ids)):
        raise BioOSCanonBindingV06Error("claim_ids must be unique and non-empty")
    claims = [_claim_record(v) for v in ids]

    scope = str(usage_scope)
    shared_absolute_requested = scope == SHARED_ABSOLUTE_SCOPE
    cnu3_present = "C-Nu-3" in ids
    m11_no_go = bool(shared_absolute_requested and cnu3_present)

    if shared_absolute_requested and not cnu3_present:
        raise BioOSCanonBindingV06Error("C-Nu-3 firewall is mandatory for shared absolute-spectrum scope")

    core = {
        "schema": SCHEMA,
        "authority_source": snapshot,
        "authority_mode": "READ_ONLY_HASH_PINNED_EXTERNAL_CANON",
        "claims": claims,
        "usage_scope": scope,
        "branch_scope_declared": scope in BRANCH_SCOPES,
        "m11_no_go": m11_no_go,
        "m11_reason": (
            "SHARED_ABSOLUTE_NEUTRINO_SPECTRUM_AUTHORITY_WITHHELD"
            if m11_no_go
            else None
        ),
        "execution_contract": {
            "authority_grant": False,
            "execution_admitted": False,
            "production_runtime_write": False,
            "qhtri_operator_profile_created": False,
            "next_gate": "EXPLICIT_M4_VALIDATION_AND_SEPARATE_QHTRI_OPERATOR_BINDING",
        },
        "m10_policy": {
            "append_only": True,
            "preserve_external_authority_pin": True,
        },
    }
    commitment = hashlib.blake2b(DOMAIN + _canonical(core), digest_size=32).hexdigest()
    return {**core, "canon_ir_commitment": commitment}


def validate_canon_ir_v06(ir: Mapping[str, Any]) -> bool:
    if ir.get("schema") != SCHEMA:
        raise BioOSCanonBindingV06Error("unsupported BioOS canon IR schema")
    validate_authority_snapshot(ir.get("authority_source", {}))

    claims = ir.get("claims")
    if not isinstance(claims, list) or not claims:
        raise BioOSCanonBindingV06Error("canonical claim list required")
    ids = [str(v.get("claim_id")) for v in claims if isinstance(v, Mapping)]
    if len(ids) != len(claims) or len(ids) != len(set(ids)):
        raise BioOSCanonBindingV06Error("invalid canonical claim list")
    expected_claims = [_claim_record(v) for v in ids]
    if claims != expected_claims:
        raise BioOSCanonBindingV06Error("canonical claim metadata mismatch")

    scope = str(ir.get("usage_scope"))
    expected_no_go = scope == SHARED_ABSOLUTE_SCOPE and "C-Nu-3" in ids
    if scope == SHARED_ABSOLUTE_SCOPE and "C-Nu-3" not in ids:
        raise BioOSCanonBindingV06Error("shared absolute spectrum requires C-Nu-3")
    if ir.get("m11_no_go") is not expected_no_go:
        raise BioOSCanonBindingV06Error("M11 firewall state mismatch")

    execution = ir.get("execution_contract")
    if not isinstance(execution, Mapping):
        raise BioOSCanonBindingV06Error("execution contract required")
    for key in (
        "authority_grant",
        "execution_admitted",
        "production_runtime_write",
        "qhtri_operator_profile_created",
    ):
        if execution.get(key) is not False:
            raise BioOSCanonBindingV06Error(f"authority boundary violated: {key}")

    supplied = str(ir.get("canon_ir_commitment", ""))
    core = dict(ir)
    core.pop("canon_ir_commitment", None)
    expected = hashlib.blake2b(DOMAIN + _canonical(core), digest_size=32).hexdigest()
    if supplied != expected:
        raise BioOSCanonBindingV06Error("canon IR commitment mismatch")
    return True


def make_m10_canon_receipt_v06(
    ir: Mapping[str, Any],
    *,
    evidence_refs: Sequence[str] = (),
) -> dict[str, Any]:
    validate_canon_ir_v06(ir)
    core = {
        "schema": RECEIPT_SCHEMA,
        "canon_ir_commitment": str(ir["canon_ir_commitment"]),
        "authority_source": dict(ir["authority_source"]),
        "claim_ids": [str(v["claim_id"]) for v in ir["claims"]],
        "usage_scope": str(ir["usage_scope"]),
        "m11_no_go": bool(ir["m11_no_go"]),
        "evidence_refs": sorted(str(v) for v in evidence_refs),
        "append_only": True,
        "authority_grant": False,
        "execution_admitted": False,
        "production_runtime_write": False,
    }
    receipt_id = hashlib.sha256(RECEIPT_DOMAIN + _canonical(core)).hexdigest()
    return {**core, "receipt_id": receipt_id}
