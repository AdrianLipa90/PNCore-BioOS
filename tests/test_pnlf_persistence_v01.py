import pytest

from tools.pnlf_persistence_v01 import (
    PNLFPersistenceBinding,
    PNLFPersistenceError,
    persistence_manifest,
    pnh5_view,
)

A = "11" * 32
B = "22" * 32
C = "33" * 32
D = "44" * 32
E = "55" * 32


def binding():
    return PNLFPersistenceBinding(A, B, C, D, E)


def test_identity_axes_remain_distinct():
    b = binding()
    assert len({b.file_id, b.content_commitment, b.checkpoint_object_id}) == 3


def test_identity_alias_fails_closed():
    with pytest.raises(PNLFPersistenceError, match="must remain distinct"):
        PNLFPersistenceBinding(A, A, C, D, E)


def test_manifest_binds_tau_t36_and_state_memory():
    m = persistence_manifest(
        binding(),
        generation=7,
        tau_start={"p": 0, "q": 1},
        tau_end={"p": 783, "q": 100},
        active_liminal_layers=("M2", "M7", "M10", "M11"),
    )
    assert m["content_parameter"] == "SCALAR_TAU"
    assert m["integrity_witness"] == "T36_WHOLE_LANE"
    assert m["consolidation_boundary"] == "STATE_MEMORY_CHECKPOINT"
    assert m["wall_clock_role"] == "REALIZATION_EVIDENCE"
    assert len(m["manifest_id"]) == 64


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
