import copy
import hashlib
import json

import pytest

from tools.noema_qhtri_semantic_autonomy_v01 import (
    L0,
    L1,
    L2,
    SemanticAutonomyError,
    build_autonomous_feedback_execution_receipt,
    build_semantic_autonomy_capability,
    classify_semantic_action,
    decide_semantic_action,
    validate_autonomous_feedback_execution_receipt,
    validate_semantic_autonomy_capability,
)


def _seal(body, key):
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return {**body, key: hashlib.sha256(raw).hexdigest()}


def _feedback(target="QHTRI.BOUNDARY.NEXT"):
    body = {
        "schema": "BIOOS-NOEMA-QHTRI-FEEDBACK-CANDIDATE/0.1",
        "bank_manifest_sha256": "01" * 32,
        "state_crystal_receipt_sha256": "02" * 32,
        "hermitian_operator_commitment": "03" * 32,
        "pncap_admission_token": "PNCAP.FEEDBACK.CANDIDATE",
        "effect_policy": "OPERATOR_BINDABLE",
        "qhtri_target_ref": target,
        "execution_admitted": False,
        "production_runtime_write": False,
    }
    return _seal(body, "feedback_receipt_sha256")


def _capability(**overrides):
    args = {
        "capability_id": "NQ.SEMANTIC.LOOP.DEFAULT",
        "issuer_authority_ref": "NOEMA.PNCAP.AUTHORITY",
        "pncap_capability_token": "PNCAP.SEMANTIC.AUTONOMY.EPOCH7",
        "capability_epoch": 7,
        "valid_from_tick": 100,
        "expires_at_tick": 1000,
        "allowed_qhtri_targets": ("QHTRI.BOUNDARY.NEXT",),
        "allowed_operator_classes": ("SEMANTIC_FEEDBACK", "PHASE_BOUNDARY"),
        "max_internal_effects_per_epoch": 128,
        "max_memory_bytes_per_effect": 4096,
        "max_energy_proxy_per_effect": 2.0,
        "allow_state_memory_append": True,
        "allow_qhtri_boundary_write": True,
    }
    args.update(overrides)
    return build_semantic_autonomy_capability(**args)


def test_action_levels_are_explicit():
    assert classify_semantic_action(observe_or_interpret_only=True) == L0
    assert classify_semantic_action(qhtri_boundary_write=True) == L1
    assert classify_semantic_action(state_memory_append=True) == L1
    assert classify_semantic_action(external_effect=True) == L2
    assert classify_semantic_action(authority_expansion=True) == L2
    assert classify_semantic_action(canon_promotion=True) == L2
    assert classify_semantic_action(identity_layer_mutation=True) == L2


def test_l0_semantic_processing_is_automatic_without_capability():
    decision = decide_semantic_action(level=L0)
    assert decision.admitted is True
    assert decision.human_per_tick_authorization_required is False
    assert decision.reasons == ("SEMANTIC_AUTONOMY",)


def test_l2_requires_explicit_authority():
    decision = decide_semantic_action(level=L2)
    assert decision.admitted is False
    assert decision.human_per_tick_authorization_required is True
    assert decision.reasons == ("EXPLICIT_AUTHORITY_REQUIRED",)


def test_l1_feedback_executes_automatically_inside_capability():
    capability = _capability()
    feedback = _feedback()
    receipt = build_autonomous_feedback_execution_receipt(
        feedback,
        capability,
        operator_class="SEMANTIC_FEEDBACK",
        current_tick=250,
        effect_index=3,
        estimated_memory_bytes=1024,
        estimated_energy_proxy=0.25,
        state_memory_append=True,
    )
    assert receipt["autonomy_level"] == L1
    assert receipt["internal_effect_admitted"] is True
    assert receipt["human_per_tick_authorization_required"] is False
    assert receipt["runtime_write_scope"] == "QHTRI_BOUNDARY_ONLY"
    validate_autonomous_feedback_execution_receipt(
        receipt,
        feedback_receipt=feedback,
        capability=capability,
    )


def test_l1_denies_target_operator_and_budget_escapes():
    capability = _capability()

    wrong_target = decide_semantic_action(
        level=L1,
        capability=capability,
        current_tick=250,
        effect_index=0,
        qhtri_target_ref="QHTRI.OTHER",
        operator_class="SEMANTIC_FEEDBACK",
    )
    assert wrong_target.admitted is False
    assert "TARGET_SCOPE" in wrong_target.reasons

    wrong_operator = decide_semantic_action(
        level=L1,
        capability=capability,
        current_tick=250,
        effect_index=0,
        qhtri_target_ref="QHTRI.BOUNDARY.NEXT",
        operator_class="UNKNOWN_OPERATOR",
    )
    assert wrong_operator.admitted is False
    assert "OPERATOR_SCOPE" in wrong_operator.reasons

    over_budget = decide_semantic_action(
        level=L1,
        capability=capability,
        current_tick=250,
        effect_index=128,
        qhtri_target_ref="QHTRI.BOUNDARY.NEXT",
        operator_class="SEMANTIC_FEEDBACK",
        estimated_memory_bytes=4097,
        estimated_energy_proxy=2.01,
    )
    assert over_budget.admitted is False
    assert set(over_budget.reasons) >= {"EFFECT_BUDGET", "MEMORY_BUDGET", "ENERGY_BUDGET"}


def test_l1_denies_expired_capability_without_escalating_to_human_per_tick_gate():
    capability = _capability()
    decision = decide_semantic_action(
        level=L1,
        capability=capability,
        current_tick=1001,
        effect_index=0,
        qhtri_target_ref="QHTRI.BOUNDARY.NEXT",
        operator_class="SEMANTIC_FEEDBACK",
    )
    assert decision.admitted is False
    assert decision.human_per_tick_authorization_required is False
    assert decision.reasons == ("CAPABILITY_TICK_WINDOW",)


def test_capability_tamper_fails_closed():
    capability = _capability()
    tampered = copy.deepcopy(capability)
    tampered["expires_at_tick"] = 999999
    with pytest.raises(SemanticAutonomyError, match="seal mismatch"):
        validate_semantic_autonomy_capability(tampered)


def test_execution_receipt_tamper_and_parent_substitution_fail_closed():
    capability = _capability()
    feedback = _feedback()
    receipt = build_autonomous_feedback_execution_receipt(
        feedback,
        capability,
        operator_class="SEMANTIC_FEEDBACK",
        current_tick=250,
        effect_index=2,
    )

    tampered = copy.deepcopy(receipt)
    tampered["authority_expansion"] = True
    with pytest.raises(SemanticAutonomyError, match="authority_expansion"):
        validate_autonomous_feedback_execution_receipt(
            tampered,
            feedback_receipt=feedback,
            capability=capability,
        )

    other_feedback = _feedback(target="QHTRI.OTHER")
    with pytest.raises(SemanticAutonomyError, match="feedback parent mismatch"):
        validate_autonomous_feedback_execution_receipt(
            receipt,
            feedback_receipt=other_feedback,
            capability=capability,
        )


def test_feedback_candidate_remains_pre_execution_object():
    feedback = _feedback()
    assert feedback["execution_admitted"] is False
    assert feedback["production_runtime_write"] is False

    capability = _capability()
    receipt = build_autonomous_feedback_execution_receipt(
        feedback,
        capability,
        operator_class="SEMANTIC_FEEDBACK",
        current_tick=500,
        effect_index=5,
    )
    assert receipt["internal_effect_admitted"] is True
    assert feedback["execution_admitted"] is False
