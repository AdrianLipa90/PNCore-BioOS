from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.dn36_dncrypt_aux_binding_v01 import (
    DN36DNCryptBindingError,
    build_authenticated_user_aad,
    canonical_json_bytes,
    parse_authenticated_user_aad,
    verify_authenticated_user_aad,
)

OUT = Path("build/dn36/BIOOS_DN36_DNCRYPT_AUX_CONFORMANCE_V0_1.json")


def _paux() -> bytes:
    return hashlib.shake_256(b"BIOOS/DN36/DNCRYPT-AUX/PAUX/V0.1").digest(288)


def _core() -> dict[str, object]:
    return {
        "profile": "PAUX_EXACT_FLOAT64_LE_36_V0_2",
        "dimension": 36,
        "dtype": "float64-le",
        "object_id": "pnv:state:dn36-dncrypt-conformance-v01",
        "integrity_hash": "sha256:conformance-placeholder-not-authority",
        "state_id": "state:dn36-dncrypt-conformance-v01",
        "parent_id": "state:dn36-dncrypt-conformance-parent",
        "relation": "CHECKPOINT",
        "generation": 1,
        "persistence_context": "PNSTORE_CONFORMANCE_ONLY",
        "pncap_receipt_id": "pncap:conformance-only",
    }


def _expect_fail(name: str, fn) -> dict[str, object]:
    try:
        fn()
    except DN36DNCryptBindingError as exc:
        return {"name": name, "status": "PASS_FAIL_CLOSED", "error": str(exc)}
    raise RuntimeError(f"adversarial case unexpectedly passed: {name}")


def main() -> int:
    paux = _paux()
    core = _core()
    aad = build_authenticated_user_aad(paux, core)
    parsed = parse_authenticated_user_aad(aad)
    positive = verify_authenticated_user_aad(paux, aad, expected_core=core)

    paux_mut = bytearray(paux)
    paux_mut[17] ^= 0x01

    core_mut = json.loads(aad)
    core_mut["core"]["generation"] = 2
    core_mut_aad = canonical_json_bytes(core_mut)

    aux_mut = json.loads(aad)
    anchor = str(aux_mut["dn36_aux"]["standard_anchor"])
    aux_mut["dn36_aux"]["standard_anchor"] = anchor[:-1] + ("0" if anchor[-1] != "0" else "1")
    aux_mut_aad = canonical_json_bytes(aux_mut)

    expected_core = dict(core)
    expected_core["object_id"] = "pnv:state:unexpected-object"

    noncanonical = json.dumps(parsed, indent=2).encode("utf-8")

    adversarial = [
        _expect_fail(
            "paux_byte_mutation",
            lambda: verify_authenticated_user_aad(bytes(paux_mut), aad, expected_core=core),
        ),
        _expect_fail(
            "authenticated_core_mutation",
            lambda: verify_authenticated_user_aad(paux, core_mut_aad),
        ),
        _expect_fail(
            "authenticated_dn36_record_mutation",
            lambda: verify_authenticated_user_aad(paux, aux_mut_aad),
        ),
        _expect_fail(
            "expected_core_mismatch",
            lambda: verify_authenticated_user_aad(paux, aad, expected_core=expected_core),
        ),
        _expect_fail(
            "noncanonical_user_aad",
            lambda: verify_authenticated_user_aad(paux, noncanonical),
        ),
    ]

    record = parsed["dn36_aux"]
    receipt: dict[str, object] = {
        "schema": "BIOOS_DN36_DNCRYPT_AUX_CONFORMANCE_V0_1",
        "status": "PASS_DN36_DNCRYPT_AUX_FAIL_CLOSED",
        "positive_verify": positive,
        "adversarial_cases": adversarial,
        "adversarial_case_count": len(adversarial),
        "all_adversarial_cases_fail_closed": all(
            row["status"] == "PASS_FAIL_CLOSED" for row in adversarial
        ),
        "paux_bytes": len(paux),
        "paux_sha256": hashlib.sha256(paux).hexdigest(),
        "aad_core_bytes": len(canonical_json_bytes(core)),
        "authenticated_user_aad_bytes": len(aad),
        "dn36": {
            "state2304_sha256": record["state2304_sha256"],
            "fold256_hex": record["fold256_hex"],
            "standard_anchor": record["standard_anchor"],
        },
        "authority_firewall": {
            "security_claim": False,
            "identity_authority": False,
            "aead_authority": False,
            "canon_allowed": False,
            "dncrypt_aead_authority_preserved": True,
            "pnv_object_identity_preserved": True,
            "pnstore_durability_authority_preserved": True,
        },
        "source_pins": {
            "dncrypt": "20f53a9b297b6208d74841aee7c3bb4b8b17ce2a",
            "tir": "45b54c0c8aa60ec92607e6132b69aca9ab766d75",
            "resonant_chemistry": "6a9f21678ba4f07e5bdbb1a98a0cafe5c4838697",
        },
        "claim_boundary": (
            "Deterministic auxiliary AAD construction and fail-closed recomputation only; "
            "no DN36 cryptographic-strength claim and no actual DNCrypt AEAD roundtrip in this gate"
        ),
    }
    raw = canonical_json_bytes(receipt)
    receipt["receipt_sha256"] = hashlib.sha256(raw).hexdigest()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
