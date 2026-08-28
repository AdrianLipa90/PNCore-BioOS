from pathlib import Path

import pytest

from tools.pnh5_container_v01 import (
    PNH5ContainerError,
    checkpoint_record,
    decode_container,
    encode_container,
    read_pnh5,
    tau_frame_record,
    write_pnh5,
)
from tools.pnlf_persistence_v01 import (
    binding_from_state_checkpoint,
    persistence_manifest,
    verify_persistence_manifest,
)

A = "11" * 32
B = "22" * 32
C = "33" * 32
D = "44" * 32
E = "55" * 32
F = "66" * 32


def checkpoint():
    return {
        "schema": "PNV-LIMINAL-CHECKPOINT/0.1",
        "parent_object_id": A,
        "file_id": B,
        "generation": 3,
        "segment_commitment": C,
        "tau_end": {"p": 5, "q": 1},
        "cumulative_content_commitment": D,
        "evidence": {"source": "test"},
        "object_id": E,
    }


def manifest():
    cp = checkpoint()
    binding = binding_from_state_checkpoint(cp, tau_frame_commitment=F, t36_witness_commitment=A)
    return persistence_manifest(
        binding,
        generation=3,
        tau_start={"p": 0, "q": 1},
        tau_end={"p": 5, "q": 1},
        active_liminal_layers=("M2", "M10"),
        realization_profile="PNH5",
        state_checkpoint=cp,
    )


def records():
    cp = checkpoint()
    return (
        tau_frame_record(frame_commitment=F, realization=b"PTF1-exact-realization"),
        checkpoint_record(checkpoint_object_id=cp["object_id"], serialization=b'{"checkpoint":"opaque-state-memory-record"}'),
    )


def test_container_roundtrip_preserves_manifest_and_records():
    m = manifest()
    raw = encode_container(m, records())
    restored = decode_container(raw)
    verify_persistence_manifest(restored.manifest)
    assert restored.manifest == m
    assert restored.records == records()
    assert len(restored.container_id) == 64


def test_write_reopen_uses_real_pnh5_file(tmp_path: Path):
    path = tmp_path / "state.pnh5"
    written = write_pnh5(path, manifest(), records())
    reopened = read_pnh5(path)
    assert path.read_bytes() == encode_container(manifest(), records())
    assert reopened == written
    assert reopened.manifest["realization_profile"] == "PNH5"


def test_global_container_tamper_fails_closed():
    raw = bytearray(encode_container(manifest(), records()))
    raw[-1] ^= 0x01
    with pytest.raises(PNH5ContainerError, match="container seal mismatch"):
        decode_container(raw)


def test_missing_checkpoint_record_fails_closed():
    only_tau = (tau_frame_record(frame_commitment=F, realization=b"PTF1"),)
    with pytest.raises(PNH5ContainerError, match="CHKP record"):
        encode_container(manifest(), only_tau)


def test_manifest_checkpoint_must_exist_in_record_stream():
    wrong = checkpoint_record(checkpoint_object_id=A, serialization=b"wrong")
    raw = encode_container(manifest(), (tau_frame_record(frame_commitment=F, realization=b"PTF1"), wrong))
    with pytest.raises(PNH5ContainerError, match="manifest checkpoint is absent"):
        decode_container(raw)


def test_non_pnh5_suffix_is_rejected(tmp_path: Path):
    with pytest.raises(PNH5ContainerError, match=".pnh5 suffix"):
        write_pnh5(tmp_path / "state.bin", manifest(), records())
