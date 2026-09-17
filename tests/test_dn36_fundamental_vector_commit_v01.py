from __future__ import annotations

import hashlib

from tools.dn36_fundamental_vector_commit_v01 import (
    DIM,
    ROUNDS,
    basis36,
    commit,
    golden_mean_decode,
    golden_mean_encode,
)


def _hamming(a: bytes, b: bytes) -> int:
    assert len(a) == len(b)
    return sum((x ^ y).bit_count() for x, y in zip(a, b))


def test_basis_is_exactly_36_slots() -> None:
    basis = basis36()
    assert len(basis) == DIM == 36
    assert basis[0][1:] == ("1s", 1, 0, 0, 0)
    assert basis[-1][1] == "4p"
    assert len({row[0] for row in basis}) == 36


def test_golden_mean_morphism_is_no_11_and_roundtrips() -> None:
    raw = bytes(range(256))
    symbols = golden_mean_encode(raw)
    assert all(not (symbols[i] == symbols[i + 1] == 1) for i in range(len(symbols) - 1))
    assert golden_mean_decode(symbols) == raw


def test_commit_is_deterministic_and_domain_separated() -> None:
    payload = bytes((i * 131 + 17) & 0xFF for i in range(288))
    a = commit(payload)
    b = commit(payload)
    c = commit(payload, domain=b"BIOOS/DN36/V0.1/OTHER")
    assert a == b
    assert a.fold256 != c.fold256
    assert a.anchor256 != c.anchor256


def test_output_geometry_and_standard_anchor() -> None:
    result = commit(b"dn36-test")
    assert len(result.state2304) == 288
    assert len(result.fold256) == 32
    assert len(result.anchor256) == 32
    expected = hashlib.blake2b(
        result.state2304, digest_size=32, person=b"BioOS-DN36-v01"
    ).digest()
    assert result.anchor256 == expected


def test_single_bit_change_diffuses_candidate_fold() -> None:
    payload = bytearray((i * 29 + 7) & 0xFF for i in range(288))
    reference = commit(bytes(payload)).fold256
    payload[0] ^= 0x01
    changed = commit(bytes(payload)).fold256
    # Conservative conformance floor only; not a cryptographic-strength gate.
    assert _hamming(reference, changed) >= 64


def test_preregistered_avalanche_sample_is_centered() -> None:
    payload = bytearray((i * 73 + 41) & 0xFF for i in range(288))
    reference = commit(bytes(payload)).fold256
    fractions = []
    for bit_index in range(128):
        mutated = bytearray(payload)
        mutated[bit_index // 8] ^= 1 << (bit_index % 8)
        fractions.append(_hamming(reference, commit(bytes(mutated)).fold256) / 256.0)
    mean = sum(fractions) / len(fractions)
    # This is an engineering sanity band, not a security proof.
    assert 0.45 <= mean <= 0.55


def test_receipt_refuses_security_and_canon_claims() -> None:
    receipt = commit(b"claim-firewall").receipt()
    assert receipt["rounds"] == ROUNDS
    assert receipt["security_claim"] is False
    assert receipt["replacement_for_standard_hash"] is False
    assert receipt["canon_allowed"] is False
