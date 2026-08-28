import pytest

from tools.pnlf_persistence_v01 import (
    PNLFPersistenceBinding,
    PNLFPersistenceError,
    binding_from_state_checkpoint,
    persistence_manifest,
    pnh5_view,
    verify_persistence_manifest,
)

A = "11" * 32
B = "22" * 32
C = "33" * 32
D = "44" * 32
E = "55" * 32
F = "66" * 32


def binding():
    return PNLFPersistenceBinding(A, B, C, D, E)


def checkpoint():
    return {
        "schema": "PNV-LIMINAL-CHECKPOINT/0.1",
        "file_id": A,
        "cumulative_content_commitment": B,
        "object_id": C,
        "generation": 7,
        "tau_end": {"p": 783, "q": 100},
        "segment_commitment": F,
    }


def test_identity_axes_remain_distinct():
    b = binding()
    assert len({b.file_id, b.content_commitment, b.checkpoint_object_id}) == 3
    assert b.tau_frame_commitment != b.t36_witness_commitment


def test_identity_alias_fails_closed():
    with pytest.raises(PNLFPersistenceError, match="must remain distinct"):
        PNLFPersistenceBinding(A, A, C, D, E)
    with pytest.raises(PNLFPersistenceError, match="tau-frame and T36 witness"):
        PNLFPersistenceBinding(A, B, C, D, D)


def test_binding_is_derived_from_state_memory_checkpoint():
    b = binding_from_state_checkpoint(
        checkpoint(),
        tau_frame_commitment=D,
        t36_witness_commitment=E,
    )
    assert b == binding()


def test_manifest_binds_tau_t36_and_state_memory_checkpoint():
    cp = checkpoint()
    m = persistence_manifest(
        binding(),
        generation=7,
        tau_start={"p": 0, "q": 1},
        tau_end={"p": 783, "q": 100},
        active_liminal_layers=("M2", "M7", "M10", "M11"),
        state_checkpoint=cp,
    )
    verify_persistence_manifest(m)
    assert m["content_parameter"] == "SCALAR_TAU"
    assert m["integrity_witness"] == "T36_WHOLE_LANE"
    assert m["consolidation_boundary"] == "STATE_MEMORY_CHECKPOINT"
    assert m["wall_clock_role"] == "REALIZATION_EVIDENCE"
    assert m["commitment_holonomy"]["PNCS.frame_commitment"].startswith("StateMemory.carrier_commitment")
    assert len(m["manifest_id"]) == 64


def test_manifest_identity_tamper_fails_closed():
    m = persistence_manifest(
        binding(),
        generation=0,
        tau_start={"p": 0, "q": 1},
        tau_end={"p": 1, "q": 1},
        active_liminal_layers=("M2", "M10"),
    )
    m["generation"] = 1
    with pytest.raises(PNLFPersistenceError, match="manifest identity mismatch"):
        verify_persistence_manifest(m)


def test_checkpoint_generation_or_tau_mismatch_fails_closed():
    cp = checkpoint()
    with pytest.raises(PNLFPersistenceError, match="generation mismatch"):
        persistence_manifest(
            binding(),
            generation=8,
            tau_start={"p": 0, "q": 1},
            tau_end={"p": 783, "q": 100},
            active_liminal_layers=("M2", "M10"),
            state_checkpoint=cp,
        )
    with pytest.raises(PNLFPersistenceError, match="tau_end mismatch"):
        persistence_manifest(
            binding(),
            generation=7,
            tau_start={"p": 0, "q": 1},
            tau_end={"p": 8, "q": 1},
            active_liminal_layers=("M2", "M10"),
            state_checkpoint=cp,
        )


def test_pnh5_is_a_view_of_same_file_and_content_identity():
    m = persistence_manifest(
        binding(),
        generation=0,
        tau_start={"p": 0, "q": 1},
        tau_end={"p": 1, "q": 1},
        active_liminal_layers=("M2", "M10"),
        realization_profile="PNH5",
    )
    view = pnh5_view(m, dataset_path="/measurements/t36", dataset_schema="T36_PHASE_FIELD")
    assert view["file_id"] == m["file_id"]
    assert view["content_commitment"] == m["content_commitment"]
    assert view["source_manifest_id"] == m["manifest_id"]
