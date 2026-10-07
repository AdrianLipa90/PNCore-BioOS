#!/usr/bin/env python3
from __future__ import annotations

import sys
import qemu_pnstore_ide_adversarial_v01 as base


def main() -> int:
    base.EXPECTED_FAIL_ORDER = ["PNROM", "PN32", "PN64", "T36ID", "PNCORE.TERM", "X"]
    base.FORBIDDEN_SUCCESS_MARKERS = {"PNDEV.NEW", "PNDEV.RECOVER", "PNTERM.VGA", "PNTERM.READY"}
    sys.argv = [
        "qemu_pnstore_ide_adversarial_v01.py",
        ".",
        "--rom", "build/x86_64/pnstore_ide_qemu_test.bin",
        "--build-receipt", "provenance/PNTERM_VGA_QEMU_BUILD_V0_1.json",
        "--disk", "build/x86_64/pnterm_vga_test.img",
        "--out", "provenance/PNTERM_VGA_QEMU_ADVERSARIAL_V0_1.json",
        "--timeout", "3",
    ]
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
