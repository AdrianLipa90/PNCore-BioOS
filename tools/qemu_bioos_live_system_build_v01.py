#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys

import qemu_pnstore_ide_build_v01 as base

SCHEMA = "BIOOS_LIVE_SYSTEM_QEMU_BUILD_V0_1"
FIXTURE_HEX = Path("fixtures/BIOOS_DN36_DNCRYPT_BINARY_ENVELOPE_V0_1.hex")
EXPECTED_PAYLOAD_BYTES = 2552
EXPECTED_PAYLOAD_SHA256 = "3cda2a329301411a84f13b7f1163422ed79ef92355fd837394cec4d4b37a981e"
TRANSITION_DOMAIN = b"BIOOS/DNCRYPT/PNSTORE/TRANSITION/V0.1\x00"
ROM = Path("build/x86_64/bioos_live_system_qemu_test.bin")
RECEIPT = Path("provenance/BIOOS_LIVE_SYSTEM_QEMU_BUILD_V0_1.json")


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    root = Path(".").resolve()
    payload = bytes.fromhex((root / FIXTURE_HEX).read_text(encoding="ascii").strip())
    payload_sha = hashlib.sha256(payload).hexdigest()
    if len(payload) != EXPECTED_PAYLOAD_BYTES:
        raise SystemExit(f"FAIL_CLOSED: DNCrypt fixture size drift: {len(payload)}")
    if payload_sha != EXPECTED_PAYLOAD_SHA256:
        raise SystemExit(f"FAIL_CLOSED: DNCrypt fixture SHA drift: {payload_sha}")
    if payload[:4] != b"DNCB" or len(payload) > 3936:
        raise SystemExit("FAIL_CLOSED: invalid DNCrypt binary fixture for PNStore")

    build = root / "build/x86_64"
    build.mkdir(parents=True, exist_ok=True)
    object_digest = hashlib.sha256(payload).digest()
    transition_id = hashlib.sha256(TRANSITION_DOMAIN + object_digest).digest()
    (build / "pnstore_dncrypt_payload.bin").write_bytes(payload)
    (build / "pnstore_dncrypt_object_digest.bin").write_bytes(object_digest)
    (build / "pnstore_dncrypt_transition_id.bin").write_bytes(transition_id)

    base.SOURCE_CONTEXT = hashlib.sha256(b"BIOOS-QEMU-LIVE-PNSTORE-PNTERM/v0.1").hexdigest()
    base.SOURCES = [
        (name, "arch/x86_64/pncore/bioos_live_system_qemu_entry.S" if name == "pncore_entry" else source)
        for name, source in base.SOURCES
    ]
    base.SOURCES.append(("pnterm_uart16550", "arch/x86_64/pncore/pnterm_uart16550.S"))
    base.CODE_BINDING_LABELS = list(base.CODE_BINDING_LABELS) + [("PNTERM_UART16550", "pnterm_uart16550")]

    sys.argv = ["qemu_pnstore_ide_build_v01.py", ".", "--receipt", str(RECEIPT)]
    rc = base.main()
    if rc != 0:
        return rc

    source_rom = root / "build/x86_64/pnstore_ide_qemu_test.bin"
    target_rom = root / ROM
    shutil.copyfile(source_rom, target_rom)

    receipt_path = root / RECEIPT
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt.pop("receipt_sha256", None)
    receipt["schema"] = SCHEMA
    receipt["status"] = "PASS_HOST_BUILD"
    receipt["scope"] = "PNROM_T36_PNSTORE_ATA_PIO_PNTERM_UART16550_LIVE_SYSTEM_VERTICAL_SLICE"
    receipt["rom"] = str(ROM)
    receipt["rom_bytes"] = target_rom.stat().st_size
    receipt["rom_sha256"] = sha256_file(target_rom)
    receipt["persistent_fixture"] = {
        "bytes": len(payload),
        "sha256": payload_sha,
        "binary_envelope_id": f"dncrypt:binary-envelope:sha256:{payload_sha}",
        "object_digest_hex": object_digest.hex(),
        "transition_id_hex": transition_id.hex(),
        "pnstore_payload_max_bytes": 3936,
        "remaining_margin_bytes": 3936 - len(payload),
    }
    receipt["console"] = {
        "transport": "UART16550_COM1_POLLING",
        "baud": 115200,
        "format": "8N1",
        "line_bytes_max": 128,
        "commands": ["help", "status", "store.show", "echo"],
        "write_commands": 0,
        "arbitrary_shell": False,
    }
    receipt["physical_machine_claim"] = False
    receipt["physical_power_loss_claim"] = False
    receipt["canon_allowed"] = False
    receipt["epistemic"] = "CHYBA"
    receipt["claim_boundary"] = (
        "Host build of one integrated QEMU vertical slice joining PNStore ATA-PIO persistent state and a bounded read-only PNTERM UART console. "
        "It is not bare-metal validation, physical power-loss durability, a general shell, or canon."
    )
    receipt["receipt_sha256"] = hashlib.sha256(canonical_bytes(receipt)).hexdigest()
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
