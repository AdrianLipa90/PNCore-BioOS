from __future__ import annotations

import json

import pytest

from tools.dn36_dncrypt_aux_binding_v01 import (
    AAD_SCHEMA,
    DN36DNCryptBindingError,
    build_authenticated_user_aad,
    canonical_json_bytes,
    parse_authenticated_user_aad,
    verify_authenticated_user_aad,
)


def _paux() -> bytes:
    return bytes((index * 37 + 11) & 0xFF for index in range(288))


def _core() -> dict[str, object]:
    return {
        "profile": "PAUX_EXACT_FLOAT64_LE_36_V0_2",
        "object_id": "pnv:state:test-object-001",
        "state_id": "state:test-state-001",
        "parent_id": "state:test-parent-000",
        "generation": 7,
        "relation": "CHECKPOINT",
        "persistence_context": "PNSTORE_TEST",
        "pncap_receipt_id": "pncap:test:001",
    }


def test_dn36_aux_aad_roundtrip_passes_exactly() -> None:
    paux = _paux()
    core = _core()
    aad = build_authenticated_user_aad(paux, core)
    parsed = parse_authenticated_user_aad(aad)
    assert parsed["schema"] == AAD_SCHEMA
    assert parsed["core"] == core
    assert parsed["dn36_aux"]["security_claim"] is False
    assert parsed["dn36_aux"]["identity_authority"] is False
    assert parsed["dn36_aux"]["aead_authority"] is False
    assert parsed["dn36_aux"]["canon_allowed"] is False
    receipt = verify_authenticated_user_aad(paux, aad, expected_core=core)
    assert receipt["status"] == "PASS"
    assert receipt["object_id"] == core["object_id"]


def test_paux_tamper_fails_closed() -> None:
    paux = _paux()
    aad = build_authenticated_user_aad(paux, _core())
    tampered = bytearray(paux)
    tampered[143] ^= 0x80
    with pytest.raises(DN36DNCryptBindingError, match="commitment mismatch"):
        verify_authenticated_user_aad(bytes(tampered), aad)


def test_authenticated_core_tamper_fails_closed() -> None:
    paux = _paux()
    aad = build_authenticated_user_aad(paux, _core())
    parsed = json.loads(aad)
    parsed["core"]["generation"] = 8
    tampered_aad = canonical_json_bytes(parsed)
    with pytest.raises(DN36DNCryptBindingError, match="commitment mismatch"):
        verify_authenticated_user_aad(paux, tampered_aad)


def test_aux_record_tamper_fails_closed() -> None:
    paux = _paux()
    aad = build_authenticated_user_aad(paux, _core())
    parsed = json.loads(aad)
    fold = parsed["dn36_aux"]["fold256_hex"]
    parsed["dn36_aux"]["fold256_hex"] = ("0" if fold[0] != "0" else "1") + fold[1:]
    tampered_aad = canonical_json_bytes(parsed)
    with pytest.raises(DN36DNCryptBindingError, match="commitment mismatch"):
        verify_authenticated_user_aad(paux, tampered_aad)


def test_expected_core_mismatch_is_independent_gate() -> None:
    paux = _paux()
    core = _core()
    aad = build_authenticated_user_aad(paux, core)
    expected = dict(core)
    expected["object_id"] = "pnv:state:other-object"
    with pytest.raises(DN36DNCryptBindingError, match="does not match expected core"):
        verify_authenticated_user_aad(paux, aad, expected_core=expected)


def test_noncanonical_aad_is_rejected() -> None:
    paux = _paux()
    aad = build_authenticated_user_aad(paux, _core())
    parsed = json.loads(aad)
    noncanonical = json.dumps(parsed, indent=2, sort_keys=False).encode("utf-8")
    with pytest.raises(DN36DNCryptBindingError, match="not canonical JSON"):
        verify_authenticated_user_aad(paux, noncanonical)


def test_wrong_paux_size_is_rejected() -> None:
    with pytest.raises(DN36DNCryptBindingError, match="exactly 288 bytes"):
        build_authenticated_user_aad(b"x" * 287, _core())


def test_core_cannot_self_embed_dn36_extension() -> None:
    core = _core()
    core["dn36_aux"] = {"bad": True}
    with pytest.raises(DN36DNCryptBindingError, match="must not contain dn36_aux"):
        build_authenticated_user_aad(_paux(), core)
