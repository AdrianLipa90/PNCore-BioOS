from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

POINCARE_SCHEMA = "BIOOS-NOEMA-QHTRI-POINCARE-ANCHOR/0.1"
SPINOR_SCHEMA = "BIOOS-NOEMA-QHTRI-SPINOR-SHEET/0.1"


class NoemaQhtriAnchorStageError(ValueError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _hex64(value: Any, name: str) -> str:
    text = str(value)
    if len(text) != 64:
        raise NoemaQhtriAnchorStageError(f"{name} must be 64 hex characters")
    try:
        bytes.fromhex(text)
    except ValueError as exc:
        raise NoemaQhtriAnchorStageError(f"{name} must be hexadecimal") from exc
    return text.lower()


def _text(value: Any, name: str) -> str:
    text = str(value).strip()
    if not text:
        raise NoemaQhtriAnchorStageError(f"{name} is required")
    return text


def _finite(value: Any, name: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise NoemaQhtriAnchorStageError(f"{name} must be numeric") from exc
    if not math.isfinite(out):
        raise NoemaQhtriAnchorStageError(f"{name} must be finite")
    return out


def build_poincare_anchor_receipt(
    *,
    bank_manifest_sha256: str,
    bifurcation_receipt_sha256: str,
    poincare_re: float,
    poincare_im: float,
    cp1_poincare_adapter_commitment: str,
    holonomy_audit_commitment: str,
    geometry_evidence_ref: str,
) -> dict[str, Any]:
    re = _finite(poincare_re, "poincare_re")
    im = _finite(poincare_im, "poincare_im")
    radius2 = re * re + im * im
    if radius2 >= 1.0:
        raise NoemaQhtriAnchorStageError("Poincare anchor must lie inside the unit disk")
    body = {
        "schema": POINCARE_SCHEMA,
        "bank_manifest_sha256": _hex64(bank_manifest_sha256, "bank_manifest_sha256"),
        "bifurcation_receipt_sha256": _hex64(bifurcation_receipt_sha256, "bifurcation_receipt_sha256"),
        "poincare_re": re,
        "poincare_im": im,
        "poincare_radius": math.sqrt(radius2),
        "cp1_poincare_adapter_commitment": _hex64(cp1_poincare_adapter_commitment, "cp1_poincare_adapter_commitment"),
        "holonomy_audit_commitment": _hex64(holonomy_audit_commitment, "holonomy_audit_commitment"),
        "geometry_evidence_ref": _text(geometry_evidence_ref, "geometry_evidence_ref"),
        "isomorphism_id": "ISO.NQ.03.CP1.POINCARE.CONTINUATION",
        "relation_type": "MAPS_TO",
    }
    return {**body, "poincare_anchor_receipt_sha256": _sha256(body)}


def validate_poincare_anchor_receipt(receipt: Mapping[str, Any]) -> None:
    if receipt.get("schema") != POINCARE_SCHEMA:
        raise NoemaQhtriAnchorStageError("Poincare anchor schema mismatch")
    if receipt.get("isomorphism_id") != "ISO.NQ.03.CP1.POINCARE.CONTINUATION" or receipt.get("relation_type") != "MAPS_TO":
        raise NoemaQhtriAnchorStageError("Poincare anchor relation typing mismatch")
    re = _finite(receipt.get("poincare_re"), "poincare_re")
    im = _finite(receipt.get("poincare_im"), "poincare_im")
    radius = math.hypot(re, im)
    if radius >= 1.0 or abs(radius - _finite(receipt.get("poincare_radius"), "poincare_radius")) > 2e-12:
        raise NoemaQhtriAnchorStageError("Poincare radius mismatch")
    for key in ("bank_manifest_sha256", "bifurcation_receipt_sha256", "cp1_poincare_adapter_commitment", "holonomy_audit_commitment"):
        _hex64(receipt.get(key), key)
    _text(receipt.get("geometry_evidence_ref"), "geometry_evidence_ref")
    body = {key: value for key, value in receipt.items() if key != "poincare_anchor_receipt_sha256"}
    if receipt.get("poincare_anchor_receipt_sha256") != _sha256(body):
        raise NoemaQhtriAnchorStageError("Poincare anchor seal mismatch")


def build_spinor_sheet_receipt(
    poincare_anchor_receipt: Mapping[str, Any],
    *,
    spinor_sheet: int,
    spinor_lift_commitment: str,
    sheet_evidence_ref: str,
) -> dict[str, Any]:
    validate_poincare_anchor_receipt(poincare_anchor_receipt)
    if spinor_sheet not in (-1, 1):
        raise NoemaQhtriAnchorStageError("spinor_sheet must be -1 or +1")
    body = {
        "schema": SPINOR_SCHEMA,
        "bank_manifest_sha256": poincare_anchor_receipt["bank_manifest_sha256"],
        "poincare_anchor_receipt_sha256": poincare_anchor_receipt["poincare_anchor_receipt_sha256"],
        "spinor_sheet": int(spinor_sheet),
        "spinor_lift_commitment": _hex64(spinor_lift_commitment, "spinor_lift_commitment"),
        "sheet_evidence_ref": _text(sheet_evidence_ref, "sheet_evidence_ref"),
        "isomorphism_id": "ISO.NQ.04.SPINOR.SHEET.WITNESS",
    }
    return {**body, "spinor_sheet_receipt_sha256": _sha256(body)}


def validate_spinor_sheet_receipt(receipt: Mapping[str, Any]) -> None:
    if receipt.get("schema") != SPINOR_SCHEMA or receipt.get("isomorphism_id") != "ISO.NQ.04.SPINOR.SHEET.WITNESS":
        raise NoemaQhtriAnchorStageError("spinor sheet schema/isomorphism mismatch")
    if receipt.get("spinor_sheet") not in (-1, 1):
        raise NoemaQhtriAnchorStageError("spinor_sheet must be -1 or +1")
    for key in ("bank_manifest_sha256", "poincare_anchor_receipt_sha256", "spinor_lift_commitment"):
        _hex64(receipt.get(key), key)
    _text(receipt.get("sheet_evidence_ref"), "sheet_evidence_ref")
    body = {key: value for key, value in receipt.items() if key != "spinor_sheet_receipt_sha256"}
    if receipt.get("spinor_sheet_receipt_sha256") != _sha256(body):
        raise NoemaQhtriAnchorStageError("spinor sheet seal mismatch")
