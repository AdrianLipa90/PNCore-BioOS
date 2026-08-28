import copy

import pytest

from tools.noema_qhtri_semantic_loop_v01 import (
    FULL_BANK_ISOMORPHISM_IDS,
    NoemaQhtriSemanticLoopError,
    build_bifurcation_receipt,
    build_feedback_candidate_receipt,
    build_loop_receipt,
    build_projective_anchor_receipt,
    build_semantic_path_receipt,
    build_state_crystal_receipt,
    validate_feedback_candidate_receipt,
    validate_loop_receipt,
)

H = {
    "bank": "01" * 32,
    "qhtri": "02" * 32,
    "t36": "03" * 32,
    "cp1": "04" * 32,
    "adapter": "05" * 32,
    "holonomy": "06" * 32,
    "checkpoint": "07" * 32,
    "operator": "08" * 32,
}


def _fixture(*, identity_mutation=False, identity_authority_ref=None):
    bif = build_bifurcation_receipt(
        bank_manifest_sha256=H["bank"],
        qhtri_tick=42,
        qhtri_state_commitment=H["qhtri"],
        magnitude_M=2.5,
        beta=-0.125,
        generator_ref="QHTRI.GENERATOR.G0",
        t36_witness_commitment=H["t36"],
        cp1_state_commitment=H["cp1"],
        telemetry_evidence_ref="/dev/shm/ciel_noema:tick=42",
    )
    anchor = build_projective_anchor_receipt(
        bif,
        poincare_re=0.25,
        poincare_im=-0.5,
        spinor_sheet=-1,
        cp1_poincare_adapter_commitment=H["adapter"],
        holonomy_audit_commitment=H["holonomy"],
    )
    semantic = build_semantic_path_receipt(
        (anchor,),
        ordered_relation_ids=(),
        ordered_kaku_candidate_ids=("KAKU.CAND.001",),
        ordered_radical_candidate_ids=("RADICAL.CAND.001",),
        ordered_operator_candidate_ids=("OP.CAND.001", "OP.CAND.RETURN"),
        gremlin_isomorphism_ids=FULL_BANK_ISOMORPHISM_IDS,
    )
    crystal = build_state_crystal_receipt(
        semantic,
        state_object_id="STATE.OBJECT.0001",
        pnfs_object_id="PNFS.OBJECT.0001",
        generation=3,
        memory_epoch=11,
        checkpoint_commitment=H["checkpoint"],
        identity_layer_mutation=identity_mutation,
        identity_authority_ref=identity_authority_ref,
    )
    feedback = build_feedback_candidate_receipt(
        crystal,
        hermitian_operator_commitment=H["operator"],
        pncap_admission_token="PNCAP.TEST.GEN3.OPERATOR",
        qhtri_target_ref="QHTRI.BOUNDARY.NEXT",
    )
    loop = build_loop_receipt(
        bifurcation_receipt=bif,
        anchor_receipt=anchor,
        semantic_path_receipt=semantic,
        state_crystal_receipt=crystal,
        feedback_receipt=feedback,
    )
    return bif, anchor, semantic, crystal, feedback, loop


def test_full_loop_is_deterministic_and_non_authoritative_candidate():
    first = _fixture()
    second = _fixture()
    assert first[-1] == second[-1]
    assert first[-1]["ordered_isomorphism_ids"] == list(FULL_BANK_ISOMORPHISM_IDS)
    assert first[-1]["full_bank"] is True
    assert first[-1]["runtime_execution_authority"] is False
    assert first[-1]["canon_write_authority"] is False
    assert first[-1]["epistemic"] == "CHYBA"
    validate_loop_receipt(
        first[-1],
        bifurcation_receipt=first[0],
        anchor_receipt=first[1],
        semantic_path_receipt=first[2],
        state_crystal_receipt=first[3],
        feedback_receipt=first[4],
    )


def test_projective_anchor_rejects_invalid_z2_sheet():
    bif, *_ = _fixture()
    with pytest.raises(NoemaQhtriSemanticLoopError, match="spinor_sheet"):
        build_projective_anchor_receipt(
            bif,
            poincare_re=0.1,
            poincare_im=0.2,
            spinor_sheet=0,
            cp1_poincare_adapter_commitment=H["adapter"],
            holonomy_audit_commitment=H["holonomy"],
        )


def test_projective_anchor_rejects_boundary_or_external_disk_point():
    bif, *_ = _fixture()
    with pytest.raises(NoemaQhtriSemanticLoopError, match="unit disk"):
        build_projective_anchor_receipt(
            bif,
            poincare_re=1.0,
            poincare_im=0.0,
            spinor_sheet=1,
            cp1_poincare_adapter_commitment=H["adapter"],
            holonomy_audit_commitment=H["holonomy"],
        )


def test_semantic_path_rejects_reordered_bank_lineage():
    _, anchor, *_ = _fixture()
    wrong_order = list(FULL_BANK_ISOMORPHISM_IDS)
    wrong_order[4], wrong_order[5] = wrong_order[5], wrong_order[4]
    with pytest.raises(NoemaQhtriSemanticLoopError, match="preserve bank order"):
        build_semantic_path_receipt(
            (anchor,),
            ordered_relation_ids=(),
            ordered_kaku_candidate_ids=("KAKU.CAND.001",),
            ordered_radical_candidate_ids=("RADICAL.CAND.001",),
            ordered_operator_candidate_ids=("OP.CAND.001",),
            gremlin_isomorphism_ids=wrong_order,
        )


def test_m8_identity_mutation_requires_explicit_authority():
    _, _, semantic, *_ = _fixture()
    with pytest.raises(NoemaQhtriSemanticLoopError, match="identity_authority_ref"):
        build_state_crystal_receipt(
            semantic,
            state_object_id="STATE.OBJECT.0002",
            pnfs_object_id="PNFS.OBJECT.0002",
            generation=4,
            memory_epoch=12,
            checkpoint_commitment=H["checkpoint"],
            identity_layer_mutation=True,
        )

    crystal = build_state_crystal_receipt(
        semantic,
        state_object_id="STATE.OBJECT.0002",
        pnfs_object_id="PNFS.OBJECT.0002",
        generation=4,
        memory_epoch=12,
        checkpoint_commitment=H["checkpoint"],
        identity_layer_mutation=True,
        identity_authority_ref="NOEMA.IDENTITY.AUTHORITY.TEST",
    )
    assert crystal["identity_layer_mutation"] is True
    assert crystal["identity_authority_ref"] == "NOEMA.IDENTITY.AUTHORITY.TEST"


def test_feedback_candidate_rejects_execution_escalation():
    *_, feedback, _ = _fixture()
    tampered = copy.deepcopy(feedback)
    tampered["execution_admitted"] = True
    with pytest.raises(NoemaQhtriSemanticLoopError, match="execution-admission boundary"):
        validate_feedback_candidate_receipt(tampered)


def test_loop_rejects_parent_substitution():
    bif, anchor, semantic, crystal, feedback, _ = _fixture()
    other_bif = build_bifurcation_receipt(
        bank_manifest_sha256=H["bank"],
        qhtri_tick=43,
        qhtri_state_commitment="09" * 32,
        magnitude_M=2.5,
        beta=-0.125,
        generator_ref="QHTRI.GENERATOR.G0",
        t36_witness_commitment=H["t36"],
        cp1_state_commitment=H["cp1"],
        telemetry_evidence_ref="/dev/shm/ciel_noema:tick=43",
    )
    with pytest.raises(NoemaQhtriSemanticLoopError, match="anchor parent mismatch"):
        build_loop_receipt(
            bifurcation_receipt=other_bif,
            anchor_receipt=anchor,
            semantic_path_receipt=semantic,
            state_crystal_receipt=crystal,
            feedback_receipt=feedback,
        )


def test_partial_bank_loop_requires_explicit_partial_mode():
    bif, anchor, _, _, _, _ = _fixture()
    semantic = build_semantic_path_receipt(
        (anchor,),
        ordered_relation_ids=(),
        ordered_kaku_candidate_ids=("KAKU.CAND.001",),
        ordered_radical_candidate_ids=("RADICAL.CAND.001",),
        ordered_operator_candidate_ids=("OP.CAND.001",),
        gremlin_isomorphism_ids=FULL_BANK_ISOMORPHISM_IDS[:6],
    )
    crystal = build_state_crystal_receipt(
        semantic,
        state_object_id="STATE.PARTIAL",
        pnfs_object_id="PNFS.PARTIAL",
        generation=1,
        memory_epoch=1,
        checkpoint_commitment=H["checkpoint"],
    )
    feedback = build_feedback_candidate_receipt(
        crystal,
        hermitian_operator_commitment=H["operator"],
        pncap_admission_token="PNCAP.PARTIAL",
        qhtri_target_ref="QHTRI.PARTIAL",
    )
    with pytest.raises(NoemaQhtriSemanticLoopError, match="full loop requires all"):
        build_loop_receipt(
            bifurcation_receipt=bif,
            anchor_receipt=anchor,
            semantic_path_receipt=semantic,
            state_crystal_receipt=crystal,
            feedback_receipt=feedback,
        )

    partial = build_loop_receipt(
        bifurcation_receipt=bif,
        anchor_receipt=anchor,
        semantic_path_receipt=semantic,
        state_crystal_receipt=crystal,
        feedback_receipt=feedback,
        require_full_bank=False,
    )
    assert partial["full_bank"] is False
    assert partial["ordered_isomorphism_ids"] == list(FULL_BANK_ISOMORPHISM_IDS[:6])
