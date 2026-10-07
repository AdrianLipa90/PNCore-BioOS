#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys

import qemu_full_boot_build_v01 as base

SCHEMA = "PNTERM_CONSOLE_QEMU_BUILD_V0_1"
ROM = Path("build/x86_64/pnterm_console_qemu_test.bin")
RECEIPT = Path("provenance/PNTERM_CONSOLE_QEMU_BUILD_V0_1.json")


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
    base.SOURCE_CONTEXT = hashlib.sha256(b"BIOOS-QEMU-PNTERM-LIVE-CONSOLE/v0.1").hexdigest()
    base.NON_TEMPLATE_SOURCES = [
        (name, "arch/x86_64/pncore/pnterm_console_qemu_entry.S" if name == "pncore_entry" else source)
        for name, source in base.NON_TEMPLATE_SOURCES
    ]
    base.NON_TEMPLATE_SOURCES.append(("pnterm_uart16550", "arch/x86_64/pncore/pnterm_uart16550.S"))
    base.CODE_BINDING_LABELS = list(base.CODE_BINDING_LABELS) + [("PNTERM_UART16550", "pnterm_uart16550")]

    sys.argv = ["qemu_full_boot_build_v01.py", ".", "--receipt", str(RECEIPT)]
    rc = base.main()
    if rc != 0:
        return rc

    source_rom = root / "build/x86_64/pnrom_v0_3_qemu_test.bin"
    target_rom = root / ROM
    shutil.copyfile(source_rom, target_rom)

    receipt_path = root / RECEIPT
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt.pop("receipt_sha256", None)
    receipt["schema"] = SCHEMA
    receipt["status"] = "PASS_HOST_BUILD"
    receipt["scope"] = "DEDICATED_QEMU_PNROM_T36_PNTERM_UART16550_INTERACTIVE_CONSOLE"
    receipt["rom"] = str(ROM)
    receipt["rom_bytes"] = target_rom.stat().st_size
    receipt["rom_sha256"] = sha256_file(target_rom)
    receipt["console"] = {
        "transport": "UART16550_COM1_POLLING",
        "baud": 115200,
        "format": "8N1",
        "line_bytes_max": 128,
        "semantic_subset": "ASCII_READ_ONLY_STAGE1",
        "commands": ["help", "status", "echo"],
        "write_commands": 0,
        "arbitrary_shell": False,
    }
    receipt["physical_execution_claim"] = False
    receipt["canon_allowed"] = False
    receipt["epistemic"] = "CHYBA"
    receipt["claim_boundary"] = (
        "Host build of a dedicated PNROM->T36->PNTERM UART16550 interactive-console realization for QEMU. "
        "It is a bounded ASCII/read-only transport realization, not the complete Unicode PNTERM semantic layer, "
        "not a general shell, not bare-metal validation, and not canon promotion."
    )
    receipt["receipt_sha256"] = hashlib.sha256(canonical_bytes(receipt)).hexdigest()
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
