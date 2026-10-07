#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import signal
import subprocess
from pathlib import Path
from typing import Any

SCHEMA = "PNSTORE_IDE_QEMU_ADVERSARIAL_V0_1"
BUILD_SCHEMA = "PNSTORE_IDE_QEMU_BUILD_V0_1"
MEDIA_BYTES = 65536
EXPECTED_FAIL_ORDER = ["PNROM", "PN32", "PN64", "T36ID", "PNCORE.IDE", "X"]
FORBIDDEN_SUCCESS_MARKERS = {"PNDEV.NEW", "PNDEV.RECOVER", "PNDEV.OK"}


def canonical_bytes(obj: Any) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_obj(obj: Any) -> str:
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def exact_subsequence(lines: list[str], expected: list[str]) -> bool:
    pos = 0
    for marker in expected:
        while pos < len(lines) and lines[pos] != marker:
            pos += 1
        if pos >= len(lines):
            return False
        pos += 1
    return True


def kill_group(proc: subprocess.Popen[str]) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            proc.kill()
        except OSError:
            pass


def run_boot(qemu: Path, rom: Path, disk: Path, timeout: float) -> dict[str, Any]:
    cmd = [
        str(qemu),
        "-machine", "pc,accel=tcg",
        "-cpu", "max",
        "-m", "16M",
        "-bios", str(rom),
        "-drive", f"file={disk},format=raw,if=ide,index=0,media=disk,cache=writeback",
        "-display", "none",
        "-serial", "none",
        "-monitor", "none",
        "-debugcon", "stdio",
        "-global", "isa-debugcon.iobase=0xe9",
        "-no-reboot",
        "-no-shutdown",
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        kill_group(proc)
        stdout, stderr = proc.communicate(timeout=2.0)
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    return {
        "command": cmd,
        "timed_out_after_fail_halt_expected": timed_out,
        "returncode_after_capture": proc.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "debug_lines": lines,
    }


def verify_build_receipt(path: Path, rom: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    recorded = data.get("receipt_sha256")
    core = dict(data)
    core.pop("receipt_sha256", None)
    if recorded != sha256_obj(core):
        raise ValueError("build receipt digest mismatch")
    if data.get("schema") != BUILD_SCHEMA or data.get("status") != "PASS_HOST_BUILD":
        raise ValueError("unexpected build receipt schema/status")
    if data.get("canon_allowed") is not False:
        raise ValueError("build receipt canon boundary open")
    if data.get("physical_power_loss_claim") is not False or data.get("physical_machine_claim") is not False:
        raise ValueError("build receipt physical claim boundary open")
    if data.get("rom_sha256") != sha256_file(rom):
        raise ValueError("build receipt ROM SHA mismatch")
    return data


def mutate_case(src: Path, dst: Path, offset: int, xor_mask: int = 0x01) -> dict[str, Any]:
    raw = bytearray(src.read_bytes())
    if len(raw) != MEDIA_BYTES:
        raise ValueError(f"source media length {len(raw)} != {MEDIA_BYTES}")
    before = raw[offset]
    raw[offset] ^= xor_mask
    after = raw[offset]
    if before == after:
        raise RuntimeError("mutation did not change target byte")
    dst.write_bytes(raw)
    return {
        "offset": offset,
        "before_hex": f"{before:02x}",
        "after_hex": f"{after:02x}",
        "xor_mask_hex": f"{xor_mask:02x}",
        "sha256_before_boot": sha256_file(dst),
    }


def run_case(
    *,
    name: str,
    source_disk: Path,
    case_disk: Path,
    offset: int,
    qemu: Path,
    rom: Path,
    timeout: float,
) -> dict[str, Any]:
    mutation = mutate_case(source_disk, case_disk, offset)
    result = run_boot(qemu, rom, case_disk, timeout)
    after_sha = sha256_file(case_disk)
    lines = result["debug_lines"]
    fail_sequence = exact_subsequence(lines, EXPECTED_FAIL_ORDER)
    no_success_marker = not any(line in FORBIDDEN_SUCCESS_MARKERS for line in lines)
    medium_unchanged = after_sha == mutation["sha256_before_boot"]
    passed = (
        result["timed_out_after_fail_halt_expected"]
        and fail_sequence
        and no_success_marker
        and medium_unchanged
    )
    return {
        "name": name,
        "status": "PASS_FAIL_CLOSED" if passed else "FAIL",
        "mutation": mutation,
        "sha256_after_boot": after_sha,
        "medium_unchanged_after_rejected_boot": medium_unchanged,
        "expected_fail_sequence_present": fail_sequence,
        "success_marker_absent": no_success_marker,
        "boot": result,
    }


def emit(payload: dict[str, Any], out: Path, code: int) -> int:
    payload.pop("receipt_sha256", None)
    payload["receipt_sha256"] = sha256_obj(payload)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


def main() -> int:
    ap = argparse.ArgumentParser(description="Adversarial corruption/reboot tests for QEMU IDE PNStore")
    ap.add_argument("repo_root", type=Path, nargs="?", default=Path("."))
    ap.add_argument("--rom", type=Path, default=Path("build/x86_64/pnstore_ide_qemu_test.bin"))
    ap.add_argument("--build-receipt", type=Path, default=Path("provenance/PNSTORE_IDE_QEMU_BUILD_V0_1.json"))
    ap.add_argument("--disk", type=Path, default=Path("build/x86_64/pnstore_ide_test.img"))
    ap.add_argument("--qemu", default="qemu-system-x86_64")
    ap.add_argument("--expected-qemu-sha256", default=None)
    ap.add_argument("--timeout", type=float, default=3.0)
    ap.add_argument("--out", type=Path, default=Path("provenance/PNSTORE_IDE_QEMU_ADVERSARIAL_V0_1.json"))
    args = ap.parse_args()

    root = args.repo_root.resolve()
    rom = args.rom if args.rom.is_absolute() else root / args.rom
    receipt = args.build_receipt if args.build_receipt.is_absolute() else root / args.build_receipt
    disk = args.disk if args.disk.is_absolute() else root / args.disk
    out = args.out if args.out.is_absolute() else root / args.out
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "scope": "QEMU_PIIX_IDE_CORRUPTION_FAIL_CLOSED_REBOOT",
        "claim_boundary": "Adversarial QEMU device-image corruption and reboot rejection; not physical power-loss or bare-metal evidence",
        "canon_allowed": False,
        "epistemic": "CHYBA",
        "physical_power_loss_tested": False,
        "physical_machine_tested": False,
    }

    try:
        if not math.isfinite(args.timeout) or args.timeout <= 0:
            raise ValueError("timeout must be finite and > 0")
        if not rom.is_file() or not receipt.is_file() or not disk.is_file():
            raise FileNotFoundError("ROM, build receipt, or good PNStore disk missing")
        if disk.stat().st_size != MEDIA_BYTES:
            raise ValueError("good PNStore disk has unexpected size")

        build = verify_build_receipt(receipt, rom)
        payload["build_receipt_sha256"] = build["receipt_sha256"]
        payload["rom_sha256"] = build["rom_sha256"]
        payload["good_disk_sha256"] = sha256_file(disk)

        qemu_raw = shutil.which(args.qemu)
        if not qemu_raw:
            raise FileNotFoundError("QEMU executable not found")
        qemu = Path(qemu_raw).resolve(strict=True)
        qemu_sha = sha256_file(qemu)
        if args.expected_qemu_sha256 and qemu_sha != args.expected_qemu_sha256:
            raise ValueError("QEMU binary SHA mismatch")
        version = subprocess.run([str(qemu), "--version"], text=True, capture_output=True, check=False, timeout=5.0)
        version_text = version.stdout or version.stderr
        first_line = version_text.splitlines()[0] if version_text else ""
        if version.returncode != 0 or not first_line.startswith("QEMU emulator version "):
            raise RuntimeError("QEMU version probe failed")
        payload["qemu_binary"] = str(qemu)
        payload["qemu_binary_sha256"] = qemu_sha
        payload["qemu_binary_pinned"] = bool(args.expected_qemu_sha256)
        payload["qemu_version"] = first_line

        case_dir = root / "build/x86_64/pnstore_ide_adversarial"
        case_dir.mkdir(parents=True, exist_ok=True)
        cases = [
            ("superblock_crc_break", 40),
            ("head_a_crc_break", 512 + 508),
            ("extent_payload_crc_break", 4096 + 96),
            ("extent_seal_crc_break", 4096 + 4032 + 60),
        ]
        results = []
        for name, offset in cases:
            case_disk = case_dir / f"{name}.img"
            results.append(
                run_case(
                    name=name,
                    source_disk=disk,
                    case_disk=case_disk,
                    offset=offset,
                    qemu=qemu,
                    rom=rom,
                    timeout=args.timeout,
                )
            )

        all_pass = all(item["status"] == "PASS_FAIL_CLOSED" for item in results)
        payload["cases"] = results
        payload["case_count"] = len(results)
        payload["all_cases_fail_closed"] = all_pass
        payload["status"] = "PASS_QEMU_IDE_ADVERSARIAL_FAIL_CLOSED" if all_pass else "FAIL_ADVERSARIAL"
        return emit(payload, out, 0 if all_pass else 1)
    except Exception as exc:
        payload.update(status="FAIL_CLOSED", error_type=type(exc).__name__, error=str(exc))
        return emit(payload, out, 2)


if __name__ == "__main__":
    raise SystemExit(main())
