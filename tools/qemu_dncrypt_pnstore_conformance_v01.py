#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import sys

import qemu_pnstore_ide_conformance_v01 as base

FIXTURE_HEX = Path("fixtures/BIOOS_DN36_DNCRYPT_BINARY_ENVELOPE_V0_1.hex")
EXPECTED_PAYLOAD_BYTES = 2552
EXPECTED_PAYLOAD_SHA256 = "3cda2a329301411a84f13b7f1163422ed79ef92355fd837394cec4d4b37a981e"
TRANSITION_DOMAIN = b"BIOOS/DNCRYPT/PNSTORE/TRANSITION/V0.1\x00"
BUILD_RECEIPT = Path("provenance/PNSTORE_DNCRYPT_QEMU_BUILD_V0_1.json")
OUT_RECEIPT = Path("provenance/PNSTORE_DNCRYPT_QEMU_CONFORMANCE_V0_1.json")
DISK = Path("build/x86_64/pnstore_dncrypt_test.img")
ROM = Path("build/x86_64/pnstore_ide_qemu_test.bin")


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def main() -> int:
    root = Path(".").resolve()
    payload = bytes.fromhex((root / FIXTURE_HEX).read_text(encoding="ascii"))
    payload_sha = hashlib.sha256(payload).hexdigest()
    if len(payload) != EXPECTED_PAYLOAD_BYTES or payload_sha != EXPECTED_PAYLOAD_SHA256:
        raise SystemExit("FAIL_CLOSED: pinned DNCrypt fixture mismatch before QEMU")
    object_digest = hashlib.sha256(payload).digest()
    transition_id = hashlib.sha256(TRANSITION_DOMAIN + object_digest).digest()

    build = json.loads((root / BUILD_RECEIPT).read_text(encoding="utf-8"))
    fixture_meta = build.get("dncrypt_fixture")
    if not isinstance(fixture_meta, dict):
        raise SystemExit("FAIL_CLOSED: build receipt lacks DNCrypt fixture binding")
    if fixture_meta.get("sha256") != payload_sha or int(fixture_meta.get("bytes", -1)) != len(payload):
        raise SystemExit("FAIL_CLOSED: build receipt DNCrypt fixture binding mismatch")
    if fixture_meta.get("transition_id_hex") != transition_id.hex():
        raise SystemExit("FAIL_CLOSED: build receipt transition binding mismatch")

    base.EXPECTED_TRANSITION_ID = transition_id
    sys.argv = [
        "qemu_pnstore_ide_conformance_v01.py",
        ".",
        "--rom", str(ROM),
        "--build-receipt", str(BUILD_RECEIPT),
        "--disk", str(DISK),
        "--out", str(OUT_RECEIPT),
        "--timeout", "5",
    ]
    rc = base.main()
    if rc != 0:
        return rc

    raw = (root / DISK).read_bytes()
    if len(raw) != 65536:
        raise SystemExit("FAIL_CLOSED: PNStore disk geometry drift")
    extent = 4096
    head = 512
    stored_len = struct.unpack_from("<I", raw, extent + 88)[0]
    stored_transition = raw[extent + 24:extent + 56]
    stored_object_digest = raw[extent + 56:extent + 88]
    stored_payload = raw[extent + 96:extent + 96 + stored_len]
    head_transition = raw[head + 32:head + 64]
    head_object_digest = raw[head + 64:head + 96]

    gates = {
        "payload_length_exact": stored_len == len(payload),
        "payload_bytes_exact": stored_payload == payload,
        "payload_sha256_exact": hashlib.sha256(stored_payload).hexdigest() == payload_sha,
        "payload_binary_magic_exact": stored_payload[:4] == b"DNCB",
        "extent_transition_exact": stored_transition == transition_id,
        "extent_object_digest_exact": stored_object_digest == object_digest,
        "head_transition_exact": head_transition == transition_id,
        "head_object_digest_exact": head_object_digest == object_digest,
    }
    if not all(gates.values()):
        raise SystemExit(f"FAIL_CLOSED: DNCrypt PNStore payload binding mismatch: {gates}")

    receipt_path = root / OUT_RECEIPT
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("status") != "PASS_QEMU_IDE_PNSTORE_PERSISTENCE_SEMANTICS":
        raise SystemExit("FAIL_CLOSED: base PNStore QEMU conformance did not pass")
    receipt.pop("receipt_sha256", None)
    receipt["schema"] = "PNSTORE_DNCRYPT_QEMU_CONFORMANCE_V0_1"
    receipt["status"] = "PASS_QEMU_PNSTORE_EXACT_DNCRYPT_ENVELOPE_PERSISTENCE"
    receipt["scope"] = "QEMU_PIIX_IDE_PIO_FLUSH_TWO_BOOT_EXACT_DNCRYPT_BINARY_ENVELOPE_PERSISTENCE"
    receipt["dncrypt_payload"] = {
        "bytes": len(payload),
        "sha256": payload_sha,
        "binary_envelope_id": f"dncrypt:binary-envelope:sha256:{payload_sha}",
        "object_digest_hex": object_digest.hex(),
        "transition_id_hex": transition_id.hex(),
        "stored_payload_sha256": hashlib.sha256(stored_payload).hexdigest(),
        "gates": gates,
    }
    receipt["security_claim"] = False
    receipt["dn36_identity_authority"] = False
    receipt["dn36_aead_authority"] = False
    receipt["physical_power_loss_tested"] = False
    receipt["physical_machine_tested"] = False
    receipt["canon_allowed"] = False
    receipt["claim_boundary"] = (
        "QEMU PIIX IDE/ATA-PIO persistence of one exact pinned DNCrypt binary envelope through PNStore, "
        "including FLUSH ordering, device reread, independent second-process recovery, and exactly-once replay. "
        "Not physical power-loss durability, bare-metal validation, cryptanalysis, or canon promotion."
    )
    receipt["receipt_sha256"] = hashlib.sha256(canonical_bytes(receipt)).hexdigest()
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
