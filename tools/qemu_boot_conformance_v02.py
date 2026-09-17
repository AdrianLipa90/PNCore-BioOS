#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

SCHEMA = "PNCORE_QEMU_BOOT_CONFORMANCE_V0_2"
EXPECTED_ORDER = ["PNROM", "PN32", "PN64", "T36ID", "PNCORE", "PNR.OK", "SIGMA0", "SCHED"]
FAILURE_MARKERS = ["I!", "X"]


def canonical_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_obj(obj: Any) -> str:
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def in_order(text: str, seq: list[str]) -> bool:
    pos = 0
    for item in seq:
        nxt = text.find(item, pos)
        if nxt < 0:
            return False
        pos = nxt + len(item)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Run full PNROM -> T36 identity -> PNCore QEMU boot conformance")
    ap.add_argument("repo_root", type=Path)
    ap.add_argument("--rom", type=Path, default=Path("build/x86_64/pnrom_v0_3_qemu_test.bin"))
    ap.add_argument("--qemu", default="qemu-system-x86_64")
    ap.add_argument("--timeout", type=float, default=3.0)
    ap.add_argument("--out", type=Path, default=Path("provenance/PNCORE_QEMU_BOOT_CONFORMANCE_V0_2.json"))
    args = ap.parse_args()

    root = args.repo_root.resolve()
    rom = args.rom if args.rom.is_absolute() else root / args.rom
    out = args.out if args.out.is_absolute() else root / args.out

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "scope": "QEMU_TCG_SYNTHETIC_TEST_ROM_NOT_CANON",
        "rom": str(rom),
        "expected_debug_order": EXPECTED_ORDER,
        "failure_markers": FAILURE_MARKERS,
        "physical_execution_claim": False,
        "canon_allowed": False,
        "epistemic": "CHYBA",
    }

    if not rom.is_file():
        payload.update(status="FAIL_CLOSED", reason="ROM_MISSING")
        payload["receipt_sha256"] = sha256_obj(payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2

    raw = rom.read_bytes()
    payload["rom_bytes"] = len(raw)
    payload["rom_sha256"] = sha256_file(rom)
    if len(raw) != 65536:
        payload.update(status="FAIL_CLOSED", reason="ROM_SIZE_MISMATCH")
        payload["receipt_sha256"] = sha256_obj(payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2

    reset_prefix = bytes([0xEA, 0x00, 0x00, 0x00, 0xF0])
    payload["reset_vector_prefix_hex"] = raw[0xFFF0:0xFFF5].hex()
    if raw[0xFFF0:0xFFF5] != reset_prefix:
        payload.update(status="FAIL_CLOSED", reason="RESET_VECTOR_MISMATCH")
        payload["receipt_sha256"] = sha256_obj(payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2

    qemu = shutil.which(args.qemu)
    if not qemu:
        payload.update(status="BLOCKED_QEMU_MISSING", reason="QEMU_EXECUTABLE_NOT_FOUND")
        payload["receipt_sha256"] = sha256_obj(payload)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2

    version = subprocess.run([qemu, "--version"], text=True, capture_output=True, check=False)
    version_text = version.stdout or version.stderr
    payload["qemu_version"] = version_text.splitlines()[0] if version_text else "UNKNOWN"

    cmd = [
        qemu,
        "-machine", "pc,accel=tcg",
        "-cpu", "max",
        "-m", "16M",
        "-bios", str(rom),
        "-display", "none",
        "-serial", "none",
        "-monitor", "none",
        "-debugcon", "stdio",
        "-global", "isa-debugcon.iobase=0xe9",
        "-no-reboot",
        "-no-shutdown",
    ]
    payload["command"] = cmd

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=args.timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        stdout, stderr = proc.communicate()

    payload["timed_out_after_halt_expected"] = timed_out
    payload["debug_output"] = stdout
    payload["stderr"] = stderr
    payload["failure_marker_present"] = any(marker in stdout for marker in FAILURE_MARKERS)
    payload["expected_sequence_present"] = in_order(stdout, EXPECTED_ORDER)

    passed = bool(payload["expected_sequence_present"]) and not bool(payload["failure_marker_present"]) and timed_out
    payload["status"] = "PASS_QEMU_BOOT_CONFORMANCE" if passed else "FAIL_QEMU_BOOT_CONFORMANCE"
    payload["receipt_sha256"] = sha256_obj(payload)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
