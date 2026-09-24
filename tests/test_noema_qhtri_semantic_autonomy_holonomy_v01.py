import copy
import hashlib
import json

import pytest

from tools.noema_qhtri_semantic_autonomy_v01 import (
    SemanticAutonomyError,
    build_autonomous_feedback_execution_receipt,
    build_semantic_autonomy_capability,
    validate_autonomous_feedback_execution_receipt,
)


def _seal(body, key):
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return {**body, key: hashlib.sha256(raw).hexdigest()}


def _feedback():
    body = {
        "schema": "BIOOS-NOEMA-QHTRI-FEEDBACK-CANDIDATE/0.1",
        "bank_manifest_sha256": "01" * 32,
        "state_crystal_receipt_sha256": "02" * 32,
        "hermitian_operator_commitment": "03" * 32,
        "pncap_admission_token": "PNCAP.FEEDBACK.CANDIDATE",
        "effect_policy": "OPERATOR_BINDABLE",
        "qhtri_target_ref": "QHTRI.BOUNDARY.NEXT",
        "execution_admitted": False,
        "production_runtime_write": False,
    }
    return _seal(body, "feedback_receipt_sha256")


def _capability():
    return build_semantic_autonomy_capability(
        capability_id="NQ.HOLONOMY.TEST",
        issuer_authority_ref="NOEMA.PNCAP.AUTHORITY",
        pncap_capability_token="PNCAP.CAPABILITY.TEST",
        capability_epoch=4,
        valid_from_tick=1,
        expires_at_tick=999,
        allowed_qhtri_targets=("QHTRI.BOUNDARY.NEXT",),
        allowed_operator_classes=("SEMANTIC_FEEDBACK",),
        max_internal_effects_per_epoch=8,
        max_memory_bytes_per_effect=1024,
        max_energy_proxy_per_effect=1.0,
    )


def _receipt():
    feedback = _feedback()
    capability = _capability()
    receipt = build_autonomous_feedback_execution_receipt(
        feedback,
        capability,
        operator_class="SEMANTIC_FEEDBACK",
        current_tick=100,
        effect_index=2,
        estimated_memory_bytes=128,
        estimated_energy_proxy=0.1,
    )
    return feedback, capability, receipt


def _reseal(receipt):
    body = {k: v for k, v in receipt.items() if k != "autonomous_execution_receipt_sha256"}
    return _seal(body, "autonomous_execution_receipt_sha256")


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("capability_id", "FORGED", "capability id mismatch"),
        ("capability_epoch", 99, "capability epoch mismatch"),
        ("pncap_capability_token", "PNCAP.FORGED", "capability PNCAP token mismatch"),
        ("feedback_pncap_admission_token", "PNCAP.FORGED", "feedback PNCAP token mismatch"),
        ("qhtri_boundary_write", False, "boundary write marker"),
        ("decision_reasons", ["FORGED"], "decision reasons mismatch"),
    ],
)
def test_resealed_internal_holonomy_tamper_fails(field, value, match):
    feedback, capability, receipt = _receipt()
    tampered = copy.deepcopy(receipt)
    tampered[field] = value
    tampered = _reseal(tampered)
    with pytest.raises(SemanticAutonomyError, match=match):
        validate_autonomous_feedback_execution_receipt(
            tampered,
            feedback_receipt=feedback,
            capability=capability,
        )


def test_valid_resealed_receipt_still_passes():
    feedback, capability, receipt = _receipt()
    validate_autonomous_feedback_execution_receipt(
        _reseal(receipt),
        feedback_receipt=feedback,
        capability=capability,
    )
