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
TRANSITION_DOMAIN = b"BIOOS/DNCRYPT/PNSTORE/TRANSITION/V0.1\x00"
BUILD_RECEIPT = Path("provenance/PNTERM_INTERACTIVE_QEMU_BUILD_V0_1.json")
DNCrypt_PROVENANCE = {
    "repository": "AdrianLipa90/DNCrypt",
    "branch": "feat/dncrypt-bioos-dn36-aad-conformance-v0.1",
    "head": "b3b39ab8de059803502c227bab5924df24425f21",
    "workflow_run_id": 35243667226,
    "artifact_digest": "sha256:d15c5c3fc8eba16c744c3b27e9d1f74a8b5770be6296bb98bd7ce2c6e5fc9bc6",
    "conformance_receipt_sha256": "ac07fd1dee4837e8f0c846be82f240d624d8e6ee171fd5e10fdbda4cad3498ae",
}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def main() -> int:
    root = Path(".").resolve()
    payload = bytes.fromhex((root / FIXTURE_HEX).read_text(encoding="ascii").strip())
    payload_sha = hashlib.sha256(payload).hexdigest()
    if len(payload) != EXPECTED_PAYLOAD_BYTES:
        raise SystemExit(f"FAIL_CLOSED: DNCrypt payload size drift: {len(payload)}")
    if payload_sha != EXPECTED_PAYLOAD_SHA256:
        raise SystemExit(f"FAIL_CLOSED: DNCrypt payload SHA drift: {payload_sha}")
    if payload[:4] != b"DNCB":
        raise SystemExit("FAIL_CLOSED: DNCrypt binary-envelope magic mismatch")
    if len(payload) > 3936:
        raise SystemExit("FAIL_CLOSED: DNCrypt payload exceeds PNStore payload maximum")

    build = root / "build/x86_64"
    build.mkdir(parents=True, exist_ok=True)
    object_digest = hashlib.sha256(payload).digest()
    transition_id = hashlib.sha256(TRANSITION_DOMAIN + object_digest).digest()
    (build / "pnstore_dncrypt_payload.bin").write_bytes(payload)
    (build / "pnstore_dncrypt_object_digest.bin").write_bytes(object_digest)
    (build / "pnstore_dncrypt_transition_id.bin").write_bytes(transition_id)

    base.SOURCE_CONTEXT = hashlib.sha256(b"BIOOS-QEMU-PNTERM-INTERACTIVE-DNCRYPT-PNSTORE/v0.1").hexdigest()
    base.SOURCES = [
        (name, "arch/x86_64/pncore/pnterm_dncrypt_qemu_entry.S" if name == "pncore_entry" else source)
        for name, source in base.SOURCES
    ]
    if not any(name == "pnterm_uart" for name, _ in base.SOURCES):
        base.SOURCES.append(("pnterm_uart", "arch/x86_64/pncore/pnterm_uart16550.S"))
    if not any(label == "PNTERM_UART" for label, _ in base.CODE_BINDING_LABELS):
        base.CODE_BINDING_LABELS.append(("PNTERM_UART", "pnterm_uart"))

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
    receipt["bridge_schema"] = "PNTERM_INTERACTIVE_QEMU_BUILD_V0_1"
    receipt["scope"] = "QEMU_UART16550_READONLY_PNTERM_PLUS_EXACT_DNCRYPT_PNSTORE"
    receipt["dncrypt_fixture"] = {
        "bytes": len(payload),
        "sha256": payload_sha,
        "binary_envelope_id": f"dncrypt:binary-envelope:sha256:{payload_sha}",
        "object_digest_hex": object_digest.hex(),
        "transition_id_hex": transition_id.hex(),
        "pnstore_payload_max_bytes": 3936,
        "remaining_margin_bytes": 3936 - len(payload),
        "provenance": DNCrypt_PROVENANCE,
    }
    receipt["pnterm_realization"] = {
        "transport": "UART16550_COM1_POLLING_115200_8N1",
        "input_profile": "ASCII_READONLY_VERTICAL_SLICE_V0_1",
        "line_bytes_max": 255,
        "commands": ["help", "status", "store.show", "terminal.selftest", "echo"],
        "default_write_commands": 0,
        "full_pnterm_v0_1_semantic_conformance_claim": False,
    }
    receipt["physical_machine_claim"] = False
    receipt["physical_power_loss_claim"] = False
    receipt["canon_allowed"] = False
    receipt["epistemic"] = "CHYBA"
    receipt["claim_boundary"] = (
        "Host build of a QEMU ROM joining the existing UART16550 adapter, a narrow read-only PNTERM ASCII realization, "
        "and exact pinned DNCrypt payload persistence through PNStore. It does not claim full PNTERM UTF-8/envelope/PNCAP "
        "semantic conformance, physical hardware, physical power-loss durability, cryptanalysis, or canon promotion."
    )
    receipt["receipt_sha256"] = hashlib.sha256(canonical_bytes(receipt)).hexdigest()
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
