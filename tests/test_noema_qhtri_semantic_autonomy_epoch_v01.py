import hashlib
import json

import pytest

from tools.noema_qhtri_semantic_autonomy_epoch_v01 import SemanticAutonomyEpoch
from tools.noema_qhtri_semantic_autonomy_v01 import (
    SemanticAutonomyError,
    build_semantic_autonomy_capability,
)


def _seal(body, key):
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return {**body, key: hashlib.sha256(raw).hexdigest()}


def _feedback(target="QHTRI.BOUNDARY.NEXT", operator="03" * 32):
    body = {
        "schema": "BIOOS-NOEMA-QHTRI-FEEDBACK-CANDIDATE/0.1",
        "bank_manifest_sha256": "01" * 32,
        "state_crystal_receipt_sha256": "02" * 32,
        "hermitian_operator_commitment": operator,
        "pncap_admission_token": "PNCAP.FEEDBACK.CANDIDATE",
        "effect_policy": "OPERATOR_BINDABLE",
        "qhtri_target_ref": target,
        "execution_admitted": False,
        "production_runtime_write": False,
    }
    return _seal(body, "feedback_receipt_sha256")


def _capability(max_effects=3):
    return build_semantic_autonomy_capability(
        capability_id="NQ.EPOCH.TEST",
        issuer_authority_ref="NOEMA.PNCAP.AUTHORITY",
        pncap_capability_token="PNCAP.AUTONOMY.EPOCH9",
        capability_epoch=9,
        valid_from_tick=10,
        expires_at_tick=1000,
        allowed_qhtri_targets=("QHTRI.BOUNDARY.NEXT",),
        allowed_operator_classes=("SEMANTIC_FEEDBACK",),
        max_internal_effects_per_epoch=max_effects,
        max_memory_bytes_per_effect=2048,
        max_energy_proxy_per_effect=1.0,
    )


def test_epoch_assigns_monotonic_effect_indices_without_caller_input():
    epoch = SemanticAutonomyEpoch(_capability())
    first = epoch.execute_feedback(
        _feedback(operator="03" * 32),
        operator_class="SEMANTIC_FEEDBACK",
        current_tick=100,
    )
    second = epoch.execute_feedback(
        _feedback(operator="04" * 32),
        operator_class="SEMANTIC_FEEDBACK",
        current_tick=101,
    )
    assert first["effect_index"] == 0
    assert second["effect_index"] == 1
    assert epoch.next_effect_index == 2
    assert epoch.snapshot().consumed_effects == 2


def test_epoch_exhaustion_fails_closed():
    epoch = SemanticAutonomyEpoch(_capability(max_effects=1))
    epoch.execute_feedback(
        _feedback(),
        operator_class="SEMANTIC_FEEDBACK",
        current_tick=100,
    )
    with pytest.raises(SemanticAutonomyError, match="budget exhausted"):
        epoch.execute_feedback(
            _feedback(operator="04" * 32),
            operator_class="SEMANTIC_FEEDBACK",
            current_tick=101,
        )


def test_failed_effect_does_not_consume_index():
    epoch = SemanticAutonomyEpoch(_capability())
    with pytest.raises(SemanticAutonomyError, match="bounded internal feedback denied"):
        epoch.execute_feedback(
            _feedback(target="QHTRI.OTHER"),
            operator_class="SEMANTIC_FEEDBACK",
            current_tick=100,
        )
    assert epoch.next_effect_index == 0


def test_recovery_replay_requires_exact_next_effect_index():
    capability = _capability()
    writer = SemanticAutonomyEpoch(capability)
    feedback0 = _feedback(operator="03" * 32)
    feedback1 = _feedback(operator="04" * 32)
    receipt0 = writer.execute_feedback(
        feedback0,
        operator_class="SEMANTIC_FEEDBACK",
        current_tick=100,
    )
    receipt1 = writer.execute_feedback(
        feedback1,
        operator_class="SEMANTIC_FEEDBACK",
        current_tick=101,
    )

    recovery = SemanticAutonomyEpoch(capability)
    with pytest.raises(SemanticAutonomyError, match="replay order mismatch"):
        recovery.admit_replayed_receipt(receipt1, feedback_receipt=feedback1)
    assert recovery.next_effect_index == 0

    recovery.admit_replayed_receipt(receipt0, feedback_receipt=feedback0)
    assert recovery.next_effect_index == 1
    recovery.admit_replayed_receipt(receipt1, feedback_receipt=feedback1)
    assert recovery.next_effect_index == 2

    with pytest.raises(SemanticAutonomyError, match="replay order mismatch"):
        recovery.admit_replayed_receipt(receipt1, feedback_receipt=feedback1)
