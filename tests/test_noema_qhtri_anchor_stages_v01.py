import copy

import pytest

from tools.noema_qhtri_anchor_stages_v01 import (
    NoemaQhtriAnchorStageError,
    build_poincare_anchor_receipt,
    build_spinor_sheet_receipt,
    validate_poincare_anchor_receipt,
    validate_spinor_sheet_receipt,
)


def _poincare():
    return build_poincare_anchor_receipt(
        bank_manifest_sha256="33" * 32,
        bifurcation_receipt_sha256="44" * 32,
        poincare_re=0.1,
        poincare_im=-0.2,
        cp1_poincare_adapter_commitment="55" * 32,
        holonomy_audit_commitment="66" * 32,
        geometry_evidence_ref="live:/dev/shm/ciel_noema",
    )


def test_poincare_gate_is_independently_sealed():
    receipt = _poincare()
    validate_poincare_anchor_receipt(receipt)
    assert receipt["relation_type"] == "MAPS_TO"
    assert receipt["isomorphism_id"] == "ISO.NQ.03.CP1.POINCARE.CONTINUATION"
    assert receipt["poincare_radius"] < 1.0


def test_poincare_unit_disk_boundary_fails_closed():
    with pytest.raises(NoemaQhtriAnchorStageError, match="unit disk"):
        build_poincare_anchor_receipt(
            bank_manifest_sha256="33" * 32,
            bifurcation_receipt_sha256="44" * 32,
            poincare_re=1.0,
            poincare_im=0.0,
            cp1_poincare_adapter_commitment="55" * 32,
            holonomy_audit_commitment="66" * 32,
            geometry_evidence_ref="test",
        )


def test_spinor_sheet_is_a_separate_parent_bound_receipt():
    anchor = _poincare()
    sheet = build_spinor_sheet_receipt(
        anchor,
        spinor_sheet=-1,
        spinor_lift_commitment="77" * 32,
        sheet_evidence_ref="explicit:test-sheet-lineage",
    )
    validate_spinor_sheet_receipt(sheet)
    assert sheet["poincare_anchor_receipt_sha256"] == anchor["poincare_anchor_receipt_sha256"]
    assert sheet["spinor_sheet"] == -1
    assert sheet["isomorphism_id"] == "ISO.NQ.04.SPINOR.SHEET.WITNESS"


def test_invalid_spinor_sheet_fails_closed():
    with pytest.raises(NoemaQhtriAnchorStageError, match="spinor_sheet"):
        build_spinor_sheet_receipt(
            _poincare(),
            spinor_sheet=0,
            spinor_lift_commitment="77" * 32,
            sheet_evidence_ref="test",
        )


def test_parent_commitment_tamper_is_detected():
    anchor = _poincare()
    sheet = build_spinor_sheet_receipt(
        anchor,
        spinor_sheet=1,
        spinor_lift_commitment="77" * 32,
        sheet_evidence_ref="test",
    )
    tampered = copy.deepcopy(sheet)
    tampered["poincare_anchor_receipt_sha256"] = "88" * 32
    with pytest.raises(NoemaQhtriAnchorStageError, match="seal mismatch"):
        validate_spinor_sheet_receipt(tampered)
