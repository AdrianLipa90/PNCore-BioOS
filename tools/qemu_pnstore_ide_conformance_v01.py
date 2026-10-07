#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import signal
import struct
import subprocess
from pathlib import Path
from typing import Any

SCHEMA = "PNSTORE_IDE_QEMU_CONFORMANCE_V0_1"
BUILD_SCHEMA = "PNSTORE_IDE_QEMU_BUILD_V0_1"
FIRST_ORDER = ["PNROM", "PN32", "PN64", "T36ID", "PNCORE.IDE", "PNDEV.NEW", "PNDEV.OK"]
SECOND_ORDER = ["PNROM", "PN32", "PN64", "T36ID", "PNCORE.IDE", "PNDEV.RECOVER", "PNDEV.OK"]
FAIL_MARKERS = {"I!", "X"}
MEDIA_BYTES = 65536
EXPECTED_TRANSITION_ID = bytes.fromhex("5d12b15d523148d88d1a70037e9b6a020fa15f50776db2e5956ce00d11444901")


def canonical_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def sha256_obj(obj: Any) -> str:
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def crc32c(data: bytes) -> int:
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0x82F63B78 if crc & 1 else 0)
    return crc ^ 0xFFFFFFFF


def exact_subsequence(lines: list[str], expected: list[str]) -> bool:
    pos = 0
    for marker in expected:
        while pos < len(lines) and lines[pos] != marker:
            pos += 1
        if pos >= len(lines):
            return False
        pos += 1
    return True


def parse_media(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if len(raw) != MEDIA_BYTES:
        raise ValueError(f"media length {len(raw)} != {MEDIA_BYTES}")

    u32 = lambda off: struct.unpack_from("<I", raw, off)[0]
    u64 = lambda off: struct.unpack_from("<Q", raw, off)[0]

    checks: dict[str, bool] = {}
    checks["super_magic"] = u32(0) == 0x31534E50
    checks["super_version"] = u32(4) == 1
    checks["super_media_bytes"] = u32(8) == MEDIA_BYTES
    checks["super_sector_bytes"] = u32(12) == 512
    checks["super_extent_bytes"] = u32(16) == 4096
    checks["super_log_offset"] = u32(20) == 4096
    checks["super_max_generations"] = u32(24) == 15
    checks["super_head_offsets"] = u32(32) == 512 and u32(36) == 1024
    checks["super_crc32c"] = u32(508) == crc32c(raw[:508])

    head = 512
    checks["head_magic"] = u32(head + 0) == 0x31484E50
    checks["head_version"] = u32(head + 4) == 1
    checks["head_sequence"] = u64(head + 8) == 1
    checks["head_generation"] = u64(head + 16) == 1
    checks["head_extent_offset"] = u32(head + 24) == 4096
    checks["head_crc32c"] = u32(head + 508) == crc32c(raw[head:head + 508])
    checks["head_transition_id"] = raw[head + 32:head + 64] == EXPECTED_TRANSITION_ID

    extent = 4096
    seal = extent + 4032
    checks["extent_magic"] = u32(extent + 0) == 0x31474E50
    checks["extent_version"] = u32(extent + 4) == 1
    checks["extent_generation"] = u64(extent + 8) == 1
    checks["extent_parent_generation"] = u64(extent + 16) == 0
    checks["extent_transition_id"] = raw[extent + 24:extent + 56] == EXPECTED_TRANSITION_ID
    checks["extent_payload_bounded"] = u32(extent + 88) <= 3936
    checks["extent_candidate_flag"] = u32(extent + 92) == 1
    checks["seal_magic"] = u32(seal + 0) == 0x31434E50
    checks["seal_version"] = u32(seal + 4) == 1
    checks["seal_generation"] = u64(seal + 8) == 1
    checks["seal_committed_flag"] = u32(seal + 20) == 1
    data_crc = u32(seal + 16)
    checks["extent_data_crc32c"] = data_crc == crc32c(raw[extent:extent + 4032])
    checks["seal_crc32c"] = u32(seal + 60) == crc32c(raw[seal:seal + 60])
    checks["head_extent_crc_binding"] = u32(head + 28) == data_crc

    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "generation": u64(head + 16),
        "head_offset": head,
        "extent_offset": u32(head + 24),
        "media_sha256": hashlib.sha256(raw).hexdigest(),
    }


def verify_build_receipt(receipt_path: Path, rom: Path) -> dict[str, Any]:
    data = json.loads(receipt_path.read_text(encoding="utf-8"))
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
    if int(data.get("rom_bytes", -1)) != MEDIA_BYTES:
        raise ValueError("build receipt ROM size mismatch")
    actual_sha = sha256_file(rom)
    if data.get("rom_sha256") != actual_sha:
        raise ValueError("build receipt ROM SHA mismatch")
    return data


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
        "timed_out_after_halt_expected": timed_out,
        "returncode_after_capture": proc.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "debug_lines": lines,
        "failure_marker_present": any(line in FAIL_MARKERS for line in lines),
    }


def emit(payload: dict[str, Any], out: Path | None, code: int) -> int:
    payload.pop("receipt_sha256", None)
    payload["receipt_sha256"] = sha256_obj(payload)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


def main() -> int:
    ap = argparse.ArgumentParser(description="Two-boot QEMU/IDE PNStore persistence-semantics conformance")
    ap.add_argument("repo_root", type=Path, nargs="?", default=Path("."))
    ap.add_argument("--rom", type=Path, default=Path("build/x86_64/pnstore_ide_qemu_test.bin"))
    ap.add_argument("--build-receipt", type=Path, default=Path("provenance/PNSTORE_IDE_QEMU_BUILD_V0_1.json"))
    ap.add_argument("--disk", type=Path, default=Path("build/x86_64/pnstore_ide_test.img"))
    ap.add_argument("--qemu", default="qemu-system-x86_64")
    ap.add_argument("--expected-qemu-sha256", default=None)
    ap.add_argument("--timeout", type=float, default=4.0)
    ap.add_argument("--out", type=Path, default=Path("provenance/PNSTORE_IDE_QEMU_CONFORMANCE_V0_1.json"))
    args = ap.parse_args()

    root = args.repo_root.resolve()
    rom = args.rom if args.rom.is_absolute() else root / args.rom
    build_receipt = args.build_receipt if args.build_receipt.is_absolute() else root / args.build_receipt
    disk = args.disk if args.disk.is_absolute() else root / args.disk
    out = args.out if args.out.is_absolute() else root / args.out
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "scope": "QEMU_PIIX_IDE_PIO_FLUSH_AND_TWO_BOOT_RECOVERY_SEMANTICS",
        "claim_boundary": "QEMU device semantics and cross-process recovery; not physical power-loss durability or bare-metal validation",
        "canon_allowed": False,
        "epistemic": "CHYBA",
    }

    try:
        if not math.isfinite(args.timeout) or args.timeout <= 0:
            raise ValueError("timeout must be finite and > 0")
        if not rom.is_file() or not build_receipt.is_file():
            raise FileNotFoundError("ROM or build receipt missing")
        build = verify_build_receipt(build_receipt, rom)
        payload["build_receipt_sha256"] = build["receipt_sha256"]
        payload["rom_sha256"] = build["rom_sha256"]

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

        disk.parent.mkdir(parents=True, exist_ok=True)
        disk.write_bytes(bytes(MEDIA_BYTES))
        zero_sha = sha256_file(disk)

        first = run_boot(qemu, rom, disk, args.timeout)
        first_ok = (
            first["timed_out_after_halt_expected"]
            and not first["failure_marker_present"]
            and exact_subsequence(first["debug_lines"], FIRST_ORDER)
        )
        first_disk_sha = sha256_file(disk)
        if not first_ok:
            raise RuntimeError(f"first boot witness failed: {first['debug_lines']}")
        if first_disk_sha == zero_sha:
            raise RuntimeError("first boot did not mutate PNStore disk")
        parsed_first = parse_media(disk)
        if parsed_first["status"] != "PASS":
            raise RuntimeError(f"first boot media parser failed: {parsed_first['checks']}")

        second = run_boot(qemu, rom, disk, args.timeout)
        second_ok = (
            second["timed_out_after_halt_expected"]
            and not second["failure_marker_present"]
            and exact_subsequence(second["debug_lines"], SECOND_ORDER)
        )
        second_disk_sha = sha256_file(disk)
        if not second_ok:
            raise RuntimeError(f"second boot witness failed: {second['debug_lines']}")
        if second_disk_sha != first_disk_sha:
            raise RuntimeError("second boot unexpectedly mutated already-committed PNStore medium")
        parsed_second = parse_media(disk)
        if parsed_second["status"] != "PASS":
            raise RuntimeError(f"second boot media parser failed: {parsed_second['checks']}")

        payload.update(
            status="PASS_QEMU_IDE_PNSTORE_PERSISTENCE_SEMANTICS",
            first_boot=first,
            second_boot=second,
            first_boot_sequence=FIRST_ORDER,
            second_boot_sequence=SECOND_ORDER,
            media_after_first=parsed_first,
            media_after_second=parsed_second,
            disk_sha256_after_first=first_disk_sha,
            disk_sha256_after_second=second_disk_sha,
            second_boot_medium_unchanged=True,
            ata_flush_command_required=True,
            physical_power_loss_tested=False,
            physical_machine_tested=False,
        )
        return emit(payload, out, 0)
    except Exception as exc:
        payload.update(
            status="FAIL_CLOSED",
            error_type=type(exc).__name__,
            error=str(exc),
            physical_power_loss_tested=False,
            physical_machine_tested=False,
        )
        return emit(payload, out, 2)


if __name__ == "__main__":
    raise SystemExit(main())
