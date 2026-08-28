from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from tools import qhtri_spinor_runtime_patch_v02 as patcher


def test_repository_patch_artifact_matches_frozen_sha():
    root = Path(__file__).resolve().parents[1]
    patch = root / patcher.PATCH_RELATIVE_PATH
    assert patch.is_file()
    assert hashlib.sha256(patch.read_bytes()).hexdigest() == patcher.PATCH_SHA256


def test_source_and_candidate_domains_are_exact_and_stable():
    assert set(patcher.SOURCE_SHA256) == {
        "ciel_geometry/noema_surface_mmap.py",
        "ciel_geometry/phasenav/continuous_propagator.py",
    }
    assert set(patcher.CANDIDATE_SHA256) == set(patcher.SOURCE_SHA256)
    assert patcher.SOURCE_SHA256["ciel_geometry/noema_surface_mmap.py"] == (
        "79d11a6b1f147173f6ccdd59187f1b9447f6e015e5858edf8c6634daa8b0e2bd"
    )
    assert patcher.SOURCE_SHA256["ciel_geometry/phasenav/continuous_propagator.py"] == (
        "9881e9fede149b2ed74e1085c1bfa516d856f4dfa59268cf2acf7e3ae7243205"
    )


def test_unified_diff_engine_applies_context_removal_and_addition():
    source = ["a\n", "b\n", "c\n", "d\n"]
    diff = [
        "@@ -2,2 +2,3 @@\n",
        " b\n",
        "-c\n",
        "+C\n",
        "+x\n",
    ]
    assert patcher._apply_unified_file(source, diff) == ["a\n", "b\n", "C\n", "x\n", "d\n"]


def test_unified_diff_engine_fails_closed_on_context_mismatch():
    with pytest.raises(patcher.QhtriSpinorRuntimePatchError, match="context mismatch"):
        patcher._apply_unified_file(["a\n", "WRONG\n"], ["@@ -2,1 +2,1 @@\n", " b\n"])


def test_verify_source_rejects_unpinned_bytes(tmp_path):
    for rel in patcher.SOURCE_SHA256:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("not the pinned runtime\n")
    with pytest.raises(patcher.QhtriSpinorRuntimePatchError, match="SOURCE_HASH_MISMATCH"):
        patcher.verify_source(tmp_path)


def test_apply_refuses_patch_hash_substitution(tmp_path, monkeypatch):
    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir()
    fake_patch = tmp_path / "candidate.patch"
    fake_patch.write_text("changed")
    monkeypatch.setattr(patcher, "verify_source", lambda root: {})
    with pytest.raises(patcher.QhtriSpinorRuntimePatchError, match="PATCH_HASH_MISMATCH"):
        patcher.apply_pinned_patch(src, out, patch_path=fake_patch)


def test_candidate_manifest_is_content_addressed_over_declared_candidates():
    import json

    payload = json.dumps(patcher.CANDIDATE_SHA256, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(payload).hexdigest() == patcher.CANDIDATE_MANIFEST_SHA256
