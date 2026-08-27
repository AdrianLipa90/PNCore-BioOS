#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

SCHEMA = "PNCORE_QEMU_BOOT_CONFORMANCE_V0_1"
EXPECTED_ORDER = ["PNROM", "PN32", "PN64", "PNCORE", "PNR.OK", "SIGMA0", "SCHED"]

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

def parse_pnr(path: Path) -> dict[str, str]:
    out = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or s.startswith("END "):
            continue
        parts = s.split(None, 1)
        if len(parts) == 2:
            out[parts[0]] = parts[1]
    return out

def in_order(text: str, seq: list[str]) -> bool:
    pos = 0
    for item in seq:
        nxt = text.find(item, pos)
        if nxt < 0:
            return False
        pos = nxt + len(item)
    return True

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo_root", type=Path)
    ap.add_argument("--rom", type=Path, default=None)
    ap.add_argument("--qemu", default="qemu-system-x86_64")
    ap.add_argument("--timeout", type=float, default=2.0)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    pnr_path = args.repo_root / "realizations/x86_64/GENESIS_X86_64_V0_1.pnr"
    rom = args.rom or (args.repo_root / "build/pnrom_v0_2.bin")
    payload: dict[str, Any] = {"schema": SCHEMA, "rom": str(rom), "expected_debug_order": EXPECTED_ORDER, "canon_allowed": False, "epistemic": "CHYBA"}

    if not pnr_path.is_file():
        payload.update(status="FAIL_CLOSED", reason="PNR_MISSING")
        payload["receipt_sha256"] = sha256_obj(payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2
    if not rom.is_file():
        payload.update(status="FAIL_CLOSED", reason="ROM_MISSING")
        payload["receipt_sha256"] = sha256_obj(payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2

    pnr = parse_pnr(pnr_path)
    actual_sha = sha256_file(rom)
    expected_sha = pnr.get("ROM_SHA256")
    payload["rom_sha256"] = actual_sha
    payload["expected_rom_sha256"] = expected_sha
    if actual_sha != expected_sha:
        payload.update(status="FAIL_CLOSED", reason="ROM_SHA_MISMATCH")
        payload["receipt_sha256"] = sha256_obj(payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2

    qemu = shutil.which(args.qemu)
    if not qemu:
        payload.update(status="BLOCKED_QEMU_MISSING", reason="QEMU_EXECUTABLE_NOT_FOUND")
        payload["receipt_sha256"] = sha256_obj(payload)
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        if args.out:
            args.out.write_text(text, encoding="utf-8")
        print(text, end="")
        return 2

    version = subprocess.run([qemu, "--version"], text=True, capture_output=True, check=False)
    payload["qemu_version"] = (version.stdout or version.stderr).splitlines()[0] if (version.stdout or version.stderr) else "UNKNOWN"
    cmd = [qemu, "-machine", "pc,accel=tcg", "-cpu", "max", "-m", "16M", "-bios", str(rom), "-display", "none", "-serial", "none", "-monitor", "none", "-debugcon", "stdio", "-global", "isa-debugcon.iobase=0xe9", "-no-reboot", "-no-shutdown"]
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
    payload["failure_marker_present"] = "X\n" in stdout or stdout.rstrip().endswith("X")
    payload["expected_sequence_present"] = in_order(stdout, EXPECTED_ORDER)
    passed = payload["expected_sequence_present"] and not payload["failure_marker_present"]
    payload["status"] = "PASS_QEMU_BOOT_CONFORMANCE" if passed else "FAIL_QEMU_BOOT_CONFORMANCE"
    payload["receipt_sha256"] = sha256_obj(payload)

    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if passed else 1

if __name__ == "__main__":
    raise SystemExit(main())
