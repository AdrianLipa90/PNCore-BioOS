from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

SCHEMA = "BIOOS_GREMLIN_CANON_BINDING_V0_6"
DOMAIN = b"BIOOS-GREMLIN-CANON-BINDING/v0.6\x00"
PIN_SCHEMA = "BIOOS_GREMLIN_CANON_PIN_V0_6"
PIN_DOMAIN = b"BIOOS-GREMLIN-CANON-PIN/v0.6\x00"

GREMLIN_CANON_REPOSITORY = "AdrianLipa90/GREMLIN"
GREMLIN_CANON_COMMIT = "76a2d6b46e485723eeaa0a97badd2dae6b9b3b14"
GREMLIN_LEDGER_PATH = "spec/GREMLIN_NEUTRINO_CANON_LEDGER_V2_4.md"
GREMLIN_LEDGER_BLOB_SHA = "13c058b095ff734512dab1de8455eb73eeb637e2"
GREMLIN_PIN_MANIFEST_COMMITMENT = "58d435575368c6fedc794d5d620c2b1adeec71f37b369773ad340c0c854e2ea8"
BIOOS_V05_PARENT_COMMIT = "9e7724a481a90845485854ad28a3866be0e2caf5"

C_NU_1_PARENT_COMMIT = "4d16a924a21acc2404f4af2c7e5681946c58c6fc"
C_NU_3_PARENT_COMMIT = "a9faf42bb7016c649eb8eb93cf5827bd89323684"


class BioOSGremlinCanonBindingV06Error(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _seal(value: Mapping[str, Any]) -> str:
    return hashlib.blake2b(DOMAIN + _canonical(value), digest_size=32).hexdigest()


def _pin_seal(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(PIN_DOMAIN + _canonical(value)).hexdigest()


CLAIMS: dict[str, dict[str, Any]] = {
    "C-Nu-1": {
        "canon_status": "CANONICAL_CONDITIONAL",
        "role": "COMPLEX_OVERLAP_FRAME_BRIDGE",
        "semantic_layers": ["M3", "M6", "M9"],
        "enforcement_layers": ["M4", "M10", "M11"],
        "required_preconditions": [
            "SOURCE_BOUND_ORTHONORMAL_NEUTRINO_FRAME",
            "PMNS_ORIENTATION_BOUND",
        ],
        "open_debts": ["NEUTRINO_FRAME_TO_H_I_SOURCE_BINDING"],
        "effect_policy": "M4_AND_M11_GATED",
    },
    "C-Nu-2": {
        "canon_status": "CANONICAL",
        "role": "PROBABILITY_SHADOW_FIREWALL",
        "semantic_layers": ["M6"],
        "enforcement_layers": ["M10", "M11"],
        "required_preconditions": [],
        "open_debts": [],
        "effect_policy": "KNOWLEDGE_FIREWALL_NO_DIRECT_EFFECT",
    },
    "C-Nu-3": {
        "canon_status": "CANONICAL_FIREWALL",
        "role": "CROSS_FRAMEWORK_NEUTRINO_SPECTRUM_HOLONOMY_FIREWALL",
        "semantic_layers": ["M9", "M11"],
        "enforcement_layers": ["M4", "M10", "M11"],
        "required_preconditions": [],
        "open_debts": ["NEUTRINO_SPECTRUM_CROSS_FRAMEWORK_HOLONOMY"],
        "effect_policy": "HARD_NO_GO_ON_SHARED_ABSOLUTE_SPECTRUM",
    },
}


def _claim_binding(claim_id: str) -> dict[str, Any]:
    if claim_id not in CLAIMS:
        raise BioOSGremlinCanonBindingV06Error(f"unsupported canonical claim: {claim_id}")
    raw = CLAIMS[claim_id]
    return {
        "claim_id": claim_id,
        "canon_status": raw["canon_status"],
        "role": raw["role"],
        "semantic_layers": list(raw["semantic_layers"]),
        "enforcement_layers": list(raw["enforcement_layers"]),
        "required_preconditions": list(raw["required_preconditions"]),
        "open_debts": list(raw["open_debts"]),
        "effect_policy": raw["effect_policy"],
    }


def expected_canon_pin_manifest_core_v06() -> dict[str, Any]:
    return {
        "schema": PIN_SCHEMA,
        "source_authority": {
            "repository": GREMLIN_CANON_REPOSITORY,
            "canon_commit": GREMLIN_CANON_COMMIT,
            "ledger_path": GREMLIN_LEDGER_PATH,
            "ledger_blob_sha": GREMLIN_LEDGER_BLOB_SHA,
            "source_mode": "PINNED_READ_ONLY_CANON_SOURCE",
        },
        "canonical_claims": [
            {
                "claim_id": "C-Nu-1",
                "status": "CANONICAL_CONDITIONAL",
                "parent_commit": C_NU_1_PARENT_COMMIT,
                "open_debts": ["NEUTRINO_FRAME_TO_H_I_SOURCE_BINDING"],
            },
            {
                "claim_id": "C-Nu-2",
                "status": "CANONICAL",
                "parent_commit": C_NU_1_PARENT_COMMIT,
                "open_debts": [],
            },
            {
                "claim_id": "C-Nu-3",
                "status": "CANONICAL_FIREWALL",
                "parent_commit": C_NU_3_PARENT_COMMIT,
                "open_debts": ["NEUTRINO_SPECTRUM_CROSS_FRAMEWORK_HOLONOMY"],
            },
        ],
        "bioos_binding": {
            "parent_commit": BIOOS_V05_PARENT_COMMIT,
            "binding_schema": SCHEMA,
            "m0_m11_binding": {
                "C-Nu-1": ["M3", "M6", "M9", "M4", "M10", "M11"],
                "C-Nu-2": ["M6", "M10", "M11"],
                "C-Nu-3": ["M9", "M11", "M4", "M10"],
            },
        },
        "authority": {
            "m10_append_only": True,
            "m11_fail_closed": True,
            "execution_authority_mode": "SEPARATE_RUNTIME_VALIDATION_REQUIRED",
        },
    }


def build_canon_pin_manifest_v06() -> dict[str, Any]:
    core = expected_canon_pin_manifest_core_v06()
    return {**core, "manifest_commitment": _pin_seal(core)}


def validate_canon_pin_manifest_v06(manifest: Mapping[str, Any]) -> bool:
    if manifest.get("schema") != PIN_SCHEMA:
        raise BioOSGremlinCanonBindingV06Error("unsupported GREMLIN canon pin manifest schema")
    supplied = str(manifest.get("manifest_commitment", ""))
    core = dict(manifest)
    core.pop("manifest_commitment", None)
    expected_core = expected_canon_pin_manifest_core_v06()
    if _canonical(core) != _canonical(expected_core):
        raise BioOSGremlinCanonBindingV06Error("GREMLIN canon pin manifest content mismatch")
    expected = _pin_seal(expected_core)
    if supplied != expected or supplied != GREMLIN_PIN_MANIFEST_COMMITMENT:
        raise BioOSGremlinCanonBindingV06Error("GREMLIN canon pin manifest commitment mismatch")
    return True


def build_neutrino_canon_binding_v06(
    *,
    binding_id: str,
    gremlin_canon_commit: str = GREMLIN_CANON_COMMIT,
    gremlin_ledger_blob_sha: str = GREMLIN_LEDGER_BLOB_SHA,
    gremlin_pin_manifest_commitment: str = GREMLIN_PIN_MANIFEST_COMMITMENT,
    bioos_parent_commit: str = BIOOS_V05_PARENT_COMMIT,
    evidence_refs: Sequence[str] = (),
) -> dict[str, Any]:
    if not str(binding_id):
        raise BioOSGremlinCanonBindingV06Error("binding_id must be non-empty")
    if gremlin_canon_commit != GREMLIN_CANON_COMMIT:
        raise BioOSGremlinCanonBindingV06Error("GREMLIN canon commit pin mismatch")
    if gremlin_ledger_blob_sha != GREMLIN_LEDGER_BLOB_SHA:
        raise BioOSGremlinCanonBindingV06Error("GREMLIN ledger blob pin mismatch")
    if gremlin_pin_manifest_commitment != GREMLIN_PIN_MANIFEST_COMMITMENT:
        raise BioOSGremlinCanonBindingV06Error("GREMLIN canon pin manifest mismatch")
    if bioos_parent_commit != BIOOS_V05_PARENT_COMMIT:
        raise BioOSGremlinCanonBindingV06Error("BioOS v0.5 parent pin mismatch")

    claims = [_claim_binding(cid) for cid in ("C-Nu-1", "C-Nu-2", "C-Nu-3")]
    core = {
        "schema": SCHEMA,
        "binding_id": str(binding_id),
        "source_authority": {
            "repository": GREMLIN_CANON_REPOSITORY,
            "commit": gremlin_canon_commit,
            "ledger_path": GREMLIN_LEDGER_PATH,
            "ledger_blob_sha": gremlin_ledger_blob_sha,
            "pin_manifest_commitment": gremlin_pin_manifest_commitment,
            "mode": "PINNED_READ_ONLY_CANON_SOURCE",
        },
        "bioos_parent": {
            "repository": "AdrianLipa90/PNCore-BioOS",
            "commit": bioos_parent_commit,
            "line": "v0.5 QHTRI M0-M11 analog gate fabric",
        },
        "claims": claims,
        "m0_m11_binding": {
            "C-Nu-1": ["M3", "M6", "M9", "M4", "M10", "M11"],
            "C-Nu-2": ["M6", "M10", "M11"],
            "C-Nu-3": ["M9", "M11", "M4", "M10"],
        },
        "authority": {
            "canon_source_can_be_rewritten_by_bioos": False,
            "authority_grant": False,
            "execution_admitted": False,
            "production_runtime_write": False,
            "m10_append_only": True,
            "m11_fail_closed": True,
        },
        "cross_framework_absolute_neutrino_spectrum": {
            "shared_authority": "WITHHELD_PENDING_EXPLICIT_RELATION_OR_AUTHORITY",
            "graded_projection_scope": "BRANCH_LOCAL_EVIDENCE",
            "tir_tetrahedron_scope": "BRANCH_LOCAL_EVIDENCE",
            "conflict_marker": "2 != sqrt(7/6)",
        },
        "open_debts": [
            "NEUTRINO_FRAME_TO_H_I_SOURCE_BINDING",
            "NEUTRINO_SPECTRUM_CROSS_FRAMEWORK_HOLONOMY",
        ],
        "evidence_refs": sorted(str(v) for v in evidence_refs),
        "binding_status": "CANON_KNOWLEDGE_BOUND_EXECUTION_NOT_ADMITTED",
    }
    return {**core, "canon_binding_commitment": _seal(core)}


def validate_neutrino_canon_binding_v06(binding: Mapping[str, Any]) -> bool:
    if binding.get("schema") != SCHEMA:
        raise BioOSGremlinCanonBindingV06Error("unsupported BioOS canon binding schema")
    source = binding.get("source_authority")
    parent = binding.get("bioos_parent")
    authority = binding.get("authority")
    if not isinstance(source, Mapping) or not isinstance(parent, Mapping) or not isinstance(authority, Mapping):
        raise BioOSGremlinCanonBindingV06Error("binding sections missing")
    if source.get("commit") != GREMLIN_CANON_COMMIT or source.get("ledger_blob_sha") != GREMLIN_LEDGER_BLOB_SHA:
        raise BioOSGremlinCanonBindingV06Error("GREMLIN canon provenance mismatch")
    if source.get("pin_manifest_commitment") != GREMLIN_PIN_MANIFEST_COMMITMENT:
        raise BioOSGremlinCanonBindingV06Error("GREMLIN canon pin manifest provenance mismatch")
    if parent.get("commit") != BIOOS_V05_PARENT_COMMIT:
        raise BioOSGremlinCanonBindingV06Error("BioOS parent provenance mismatch")
    if authority.get("authority_grant") is not False or authority.get("execution_admitted") is not False:
        raise BioOSGremlinCanonBindingV06Error("BioOS canon binding may not grant execution authority")
    if authority.get("canon_source_can_be_rewritten_by_bioos") is not False:
        raise BioOSGremlinCanonBindingV06Error("GREMLIN canon source must remain read-only")
    if authority.get("m10_append_only") is not True or authority.get("m11_fail_closed") is not True:
        raise BioOSGremlinCanonBindingV06Error("M10/M11 authority firewall mismatch")
    ids = [str(c.get("claim_id")) for c in binding.get("claims", []) if isinstance(c, Mapping)]
    if ids != ["C-Nu-1", "C-Nu-2", "C-Nu-3"]:
        raise BioOSGremlinCanonBindingV06Error("exact ordered C-Nu claim set required")
    supplied = str(binding.get("canon_binding_commitment", ""))
    core = dict(binding)
    core.pop("canon_binding_commitment", None)
    if supplied != _seal(core):
        raise BioOSGremlinCanonBindingV06Error("canon binding commitment mismatch")
    return True


def evaluate_c_nu_use_v06(
    binding: Mapping[str, Any],
    *,
    claim_id: str,
    satisfied_preconditions: Sequence[str] = (),
    request_shared_absolute_spectrum: bool = False,
) -> dict[str, Any]:
    validate_neutrino_canon_binding_v06(binding)
    claim = next((c for c in binding["claims"] if c["claim_id"] == claim_id), None)
    if claim is None:
        raise BioOSGremlinCanonBindingV06Error("claim not bound")
    satisfied = {str(v) for v in satisfied_preconditions}
    missing = [p for p in claim["required_preconditions"] if p not in satisfied]
    hard_no_go = bool(claim_id == "C-Nu-3" and request_shared_absolute_spectrum)
    m4_candidate_admitted = not missing and not hard_no_go
    status = "M11_NO_GO" if hard_no_go else (
        "PRECONDITION_OPEN" if missing else "READY_FOR_SEPARATE_M4_RUNTIME_VALIDATION"
    )
    return {
        "schema": "BIOOS_C_NU_USE_EVALUATION_V0_6",
        "claim_id": claim_id,
        "missing_preconditions": missing,
        "m11_no_go": hard_no_go,
        "m4_candidate_admitted": m4_candidate_admitted,
        "execution_admitted": False,
        "status": status,
        "authority_grant": False,
    }


def make_m10_canon_binding_receipt_v06(
    binding: Mapping[str, Any],
    *,
    receipt_id: str,
    evidence_refs: Sequence[str] = (),
) -> dict[str, Any]:
    validate_neutrino_canon_binding_v06(binding)
    if not str(receipt_id):
        raise BioOSGremlinCanonBindingV06Error("receipt_id must be non-empty")
    core = {
        "schema": "BIOOS_GREMLIN_CANON_BINDING_M10_RECEIPT_V0_6",
        "receipt_id": str(receipt_id),
        "canon_binding_commitment": binding["canon_binding_commitment"],
        "gremlin_canon_commit": GREMLIN_CANON_COMMIT,
        "gremlin_ledger_blob_sha": GREMLIN_LEDGER_BLOB_SHA,
        "gremlin_pin_manifest_commitment": GREMLIN_PIN_MANIFEST_COMMITMENT,
        "bioos_parent_commit": BIOOS_V05_PARENT_COMMIT,
        "evidence_refs": sorted(str(v) for v in evidence_refs),
        "append_only": True,
        "authority_grant": False,
        "execution_admitted": False,
    }
    return {**core, "receipt_commitment": hashlib.sha256(DOMAIN + _canonical(core)).hexdigest()}
