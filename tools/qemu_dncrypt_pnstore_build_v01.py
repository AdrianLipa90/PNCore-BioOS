#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import qemu_pnstore_ide_build_v01 as base

FIXTURE_HEX = Path("fixtures/BIOOS_DN36_DNCRYPT_BINARY_ENVELOPE_V0_1.hex")
EXPECTED_PAYLOAD_BYTES = 2552
EXPECTED_PAYLOAD_SHA256 = "3cda2a329301411a84f13b7f1163422ed79ef92355fd837394cec4d4b37a981e"
DNCrypt_PROVENANCE = {
    "repository": "AdrianLipa90/DNCrypt",
    "branch": "feat/dncrypt-bioos-dn36-aad-conformance-v0.1",
    "head": "b3b39ab8de059803502c227bab5924df24425f21",
    "workflow_run_id": 35243667226,
    "artifact_digest": "sha256:d15c5c3fc8eba16c744c3b27e9d1f74a8b5770be6296bb98bd7ce2c6e5fc9bc6",
    "conformance_receipt_sha256": "ac07fd1dee4837e8f0c846be82f240d624d8e6ee171fd5e10fdbda4cad3498ae",
}
TRANSITION_DOMAIN = b"BIOOS/DNCRYPT/PNSTORE/TRANSITION/V0.1\x00"
BUILD_RECEIPT = Path("provenance/PNSTORE_DNCRYPT_QEMU_BUILD_V0_1.json")


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def main() -> int:
    root = Path(".").resolve()
    fixture_path = root / FIXTURE_HEX
    text = fixture_path.read_text(encoding="ascii").strip()
    try:
        payload = bytes.fromhex(text)
    except ValueError as exc:
        raise SystemExit(f"FAIL_CLOSED: invalid DNCrypt fixture hex: {exc}") from exc

    payload_sha = hashlib.sha256(payload).hexdigest()
    if len(payload) != EXPECTED_PAYLOAD_BYTES:
        raise SystemExit(f"FAIL_CLOSED: DNCrypt payload size drift: {len(payload)}")
    if payload_sha != EXPECTED_PAYLOAD_SHA256:
        raise SystemExit(f"FAIL_CLOSED: DNCrypt payload SHA drift: {payload_sha}")
    if payload[:4] != b"DNCB":
        raise SystemExit("FAIL_CLOSED: DNCrypt binary-envelope magic mismatch")
    if len(payload) > 3936:
        raise SystemExit("FAIL_CLOSED: DNCrypt payload exceeds PNStore extent payload maximum")

    build = root / "build/x86_64"
    build.mkdir(parents=True, exist_ok=True)
    payload_path = build / "pnstore_dncrypt_payload.bin"
    object_digest_path = build / "pnstore_dncrypt_object_digest.bin"
    transition_path = build / "pnstore_dncrypt_transition_id.bin"
    payload_path.write_bytes(payload)
    object_digest = hashlib.sha256(payload).digest()
    transition_id = hashlib.sha256(TRANSITION_DOMAIN + object_digest).digest()
    object_digest_path.write_bytes(object_digest)
    transition_path.write_bytes(transition_id)

    # Reuse the already validated PNStore/QEMU build pipeline, changing only the
    # dedicated PNCore entry object and source-context binding for this bridge.
    base.SOURCE_CONTEXT = hashlib.sha256(b"BIOOS-QEMU-PNSTORE-DNCRYPT-BRIDGE/v0.1").hexdigest()
    base.SOURCES = [
        (name, "arch/x86_64/pncore/pnstore_dncrypt_qemu_entry.S" if name == "pncore_entry" else source)
        for name, source in base.SOURCES
    ]
    sys.argv = [
        "qemu_pnstore_ide_build_v01.py",
        ".",
        "--receipt",
        str(BUILD_RECEIPT),
    ]
    rc = base.main()
    if rc != 0:
        return rc

    receipt_path = root / BUILD_RECEIPT
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt.pop("receipt_sha256", None)
    receipt["bridge_schema"] = "PNSTORE_DNCRYPT_QEMU_BUILD_V0_1"
    receipt["scope"] = "DEDICATED_QEMU_PIIX_IDE_PNSTORE_EXACT_DNCRYPT_ENVELOPE_BRIDGE"
    receipt["dncrypt_fixture"] = {
        "bytes": len(payload),
        "sha256": payload_sha,
        "binary_envelope_id": f"dncrypt:binary-envelope:sha256:{payload_sha}",
        "fixture_hex_path": str(FIXTURE_HEX),
        "object_digest_hex": object_digest.hex(),
        "transition_id_hex": transition_id.hex(),
        "pnstore_payload_max_bytes": 3936,
        "remaining_margin_bytes": 3936 - len(payload),
        "provenance": DNCrypt_PROVENANCE,
    }
    receipt["security_claim"] = False
    receipt["dn36_identity_authority"] = False
    receipt["dn36_aead_authority"] = False
    receipt["claim_boundary"] = (
        "Host build of a dedicated QEMU ROM carrying one exact pinned DNCrypt binary envelope into PNStore. "
        "This is a build/conformance bridge, not cryptanalysis, bare-metal validation, physical durability, or canon promotion."
    )
    receipt["receipt_sha256"] = hashlib.sha256(canonical_bytes(receipt)).hexdigest()
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
