#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import signal
import subprocess
from pathlib import Path
from typing import Any

SCHEMA = "PNCORE_QEMU_BOOT_CONFORMANCE_V0_2"
BUILD_SCHEMA = "PNCORE_QEMU_FULL_BOOT_BUILD_V0_1"
EXPECTED_BUILD_STATUS = "PASS_HOST_BUILD"
EXPECTED_BUILD_SCOPE = "DETERMINISTIC_SYNTHETIC_QEMU_TEST_ROM"
EXPECTED_ORDER = ["PNROM", "PN32", "PN64", "T36ID", "PNCORE", "PNR.OK", "SIGMA0", "SCHED"]
FAILURE_MARKERS = {"I!", "X"}
EXPECTED_ROM_BYTES = 65536
RESET_OFFSET = 0xFFF0
RESET_PREFIX = bytes([0xEA, 0x00, 0x00, 0x00, 0xF0])
HEX64 = re.compile(r"^[0-9a-f]{64}$")


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


def exact_marker_subsequence(lines: list[str], seq: list[str]) -> bool:
    pos = 0
    for marker in seq:
        while pos < len(lines) and lines[pos] != marker:
            pos += 1
        if pos >= len(lines):
            return False
        pos += 1
    return True


def _text(value: object | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def emit(
    payload: dict[str, Any],
    *,
    status: str,
    reason: str | None,
    exit_code: int,
    out: Path,
) -> int:
    payload["status"] = status
    payload["reason"] = reason
    payload.pop("receipt_sha256", None)
    payload["receipt_sha256"] = sha256_obj(payload)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    except OSError as exc:
        payload["receipt_output_error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "path": str(out),
        }
        payload.pop("receipt_sha256", None)
        payload["receipt_sha256"] = sha256_obj(payload)
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    return exit_code


def fail(
    payload: dict[str, Any],
    reason: str,
    *,
    out: Path,
    status: str = "FAIL_CLOSED",
    exit_code: int = 2,
) -> int:
    return emit(payload, status=status, reason=reason, exit_code=exit_code, out=out)


def _kill_process_group(proc: subprocess.Popen[str]) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    except OSError:
        try:
            proc.kill()
        except OSError:
            pass


def load_and_verify_build_receipt(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("build receipt must be a JSON object")
    recorded = obj.get("receipt_sha256")
    if not isinstance(recorded, str) or not HEX64.fullmatch(recorded):
        raise ValueError("build receipt has invalid receipt_sha256")
    core = dict(obj)
    del core["receipt_sha256"]
    actual = sha256_obj(core)
    if actual != recorded:
        raise ValueError(f"build receipt digest mismatch: {actual} != {recorded}")
    return obj, hashlib.sha256(raw).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run full PNROM -> T36 identity -> PNCore QEMU boot conformance"
    )
    ap.add_argument("repo_root", type=Path)
    ap.add_argument("--rom", type=Path, default=Path("build/x86_64/pnrom_v0_3_qemu_test.bin"))
    ap.add_argument(
        "--build-receipt",
        type=Path,
        default=Path("provenance/PNCORE_QEMU_FULL_BOOT_BUILD_V0_1.json"),
    )
    ap.add_argument("--qemu", default="qemu-system-x86_64")
    ap.add_argument("--timeout", type=float, default=3.0, help="QEMU observation window")
    ap.add_argument("--probe-timeout", type=float, default=5.0, help="QEMU --version timeout")
    ap.add_argument("--drain-timeout", type=float, default=2.0, help="bounded pipe drain after QEMU termination")
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("provenance/PNCORE_QEMU_BOOT_CONFORMANCE_V0_2.json"),
    )
    ap.add_argument("--expected-qemu-sha256", default=None)
    args = ap.parse_args()

    root = args.repo_root.resolve()
    rom = args.rom if args.rom.is_absolute() else root / args.rom
    build_receipt_path = (
        args.build_receipt
        if args.build_receipt.is_absolute()
        else root / args.build_receipt
    )
    out = args.out if args.out.is_absolute() else root / args.out

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "scope": "QEMU_TCG_SYNTHETIC_TEST_ROM_NOT_CANON",
        "rom": str(rom),
        "build_receipt": str(build_receipt_path),
        "expected_debug_order": EXPECTED_ORDER,
        "failure_markers": sorted(FAILURE_MARKERS),
        "physical_execution_claim": False,
        "canon_allowed": False,
        "epistemic": "CHYBA",
    }

    for name, value in (
        ("timeout", args.timeout),
        ("probe_timeout", args.probe_timeout),
        ("drain_timeout", args.drain_timeout),
    ):
        if not math.isfinite(value) or value <= 0.0:
            payload["invalid_timeout_field"] = name
            payload["invalid_timeout_value"] = repr(value)
            return fail(payload, "INVALID_TIMEOUT", out=out)

    if not rom.is_file():
        return fail(payload, "ROM_MISSING", out=out)
    if not build_receipt_path.is_file():
        return fail(payload, "BUILD_RECEIPT_MISSING", out=out)

    try:
        build_receipt, build_receipt_file_sha = load_and_verify_build_receipt(build_receipt_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        payload["build_receipt_error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        return fail(payload, "BUILD_RECEIPT_INVALID", out=out)

    payload["build_receipt_file_sha256"] = build_receipt_file_sha
    payload["build_receipt_payload_sha256"] = build_receipt["receipt_sha256"]
    payload["build_receipt_schema"] = build_receipt.get("schema")
    payload["build_receipt_status"] = build_receipt.get("status")
    payload["build_receipt_scope"] = build_receipt.get("scope")

    if build_receipt.get("schema") != BUILD_SCHEMA:
        return fail(payload, "BUILD_RECEIPT_SCHEMA_MISMATCH", out=out)
    if build_receipt.get("status") != EXPECTED_BUILD_STATUS:
        return fail(payload, "BUILD_RECEIPT_STATUS_NOT_PASS_HOST_BUILD", out=out)
    if build_receipt.get("scope") != EXPECTED_BUILD_SCOPE:
        return fail(payload, "BUILD_RECEIPT_SCOPE_MISMATCH", out=out)
    if build_receipt.get("canon_allowed") is not False:
        return fail(payload, "BUILD_RECEIPT_CANON_BOUNDARY_OPEN", out=out)
    if build_receipt.get("physical_execution_claim") is not False:
        return fail(payload, "BUILD_RECEIPT_PHYSICAL_CLAIM_INVALID", out=out)
    if build_receipt.get("qemu_executed") is not False:
        return fail(payload, "BUILD_RECEIPT_EXECUTION_LAYER_MIXED", out=out)

    receipt_rom = build_receipt.get("rom")
    if not isinstance(receipt_rom, str) or not receipt_rom:
        return fail(payload, "BUILD_RECEIPT_ROM_PATH_MISSING", out=out)
    receipt_rom_path = Path(receipt_rom)
    if not receipt_rom_path.is_absolute():
        receipt_rom_path = root / receipt_rom_path
    if receipt_rom_path.resolve() != rom.resolve():
        payload["build_receipt_rom_resolved"] = str(receipt_rom_path.resolve())
        return fail(payload, "BUILD_RECEIPT_ROM_PATH_MISMATCH", out=out)

    try:
        raw = rom.read_bytes()
    except OSError as exc:
        payload["rom_error"] = {"type": type(exc).__name__, "message": str(exc)}
        return fail(payload, "ROM_READ_ERROR", out=out)

    rom_sha = hashlib.sha256(raw).hexdigest()
    payload["rom_bytes"] = len(raw)
    payload["rom_sha256"] = rom_sha
    payload["build_receipt_rom_bytes"] = build_receipt.get("rom_bytes")
    payload["build_receipt_rom_sha256"] = build_receipt.get("rom_sha256")

    if len(raw) != EXPECTED_ROM_BYTES:
        return fail(payload, "ROM_SIZE_MISMATCH", out=out)
    if build_receipt.get("rom_bytes") != len(raw):
        return fail(payload, "BUILD_RECEIPT_ROM_SIZE_MISMATCH", out=out)
    if build_receipt.get("rom_sha256") != rom_sha:
        return fail(payload, "BUILD_RECEIPT_ROM_SHA_MISMATCH", out=out)

    payload["reset_vector_prefix_hex"] = raw[RESET_OFFSET:RESET_OFFSET + len(RESET_PREFIX)].hex()
    payload["build_receipt_reset_vector_offset"] = build_receipt.get("reset_vector_offset")
    payload["build_receipt_reset_vector_prefix_hex"] = build_receipt.get("reset_vector_prefix_hex")
    if raw[RESET_OFFSET:RESET_OFFSET + len(RESET_PREFIX)] != RESET_PREFIX:
        return fail(payload, "RESET_VECTOR_MISMATCH", out=out)
    if build_receipt.get("reset_vector_offset") != RESET_OFFSET:
        return fail(payload, "BUILD_RECEIPT_RESET_OFFSET_MISMATCH", out=out)
    if build_receipt.get("reset_vector_prefix_hex") != RESET_PREFIX.hex():
        return fail(payload, "BUILD_RECEIPT_RESET_PREFIX_MISMATCH", out=out)

    if args.expected_qemu_sha256 is not None and not HEX64.fullmatch(args.expected_qemu_sha256):
        return fail(payload, "EXPECTED_QEMU_SHA256_INVALID", out=out)

    qemu = shutil.which(args.qemu)
    if not qemu:
        return fail(
            payload,
            "QEMU_EXECUTABLE_NOT_FOUND",
            out=out,
            status="BLOCKED_QEMU_MISSING",
        )

    try:
        qemu_path = Path(qemu).resolve(strict=True)
        qemu_sha = sha256_file(qemu_path)
    except OSError as exc:
        payload["qemu_binary_error"] = {"type": type(exc).__name__, "message": str(exc)}
        return fail(payload, "QEMU_BINARY_READ_ERROR", out=out)

    payload["qemu_binary"] = str(qemu_path)
    payload["qemu_binary_sha256"] = qemu_sha
    payload["expected_qemu_sha256"] = args.expected_qemu_sha256
    payload["qemu_binary_pinned"] = bool(args.expected_qemu_sha256)
    if args.expected_qemu_sha256 and qemu_sha != args.expected_qemu_sha256:
        return fail(payload, "QEMU_BINARY_SHA_MISMATCH", out=out)

    try:
        version = subprocess.run(
            [str(qemu_path), "--version"],
            text=True,
            capture_output=True,
            check=False,
            timeout=args.probe_timeout,
        )
    except subprocess.TimeoutExpired as exc:
        payload["qemu_version_probe_timeout_s"] = args.probe_timeout
        payload["qemu_version_probe_partial_stdout"] = _text(exc.stdout or exc.output)
        payload["qemu_version_probe_partial_stderr"] = _text(exc.stderr)
        return fail(payload, "QEMU_VERSION_PROBE_TIMEOUT", out=out)
    except OSError as exc:
        payload["qemu_version_probe_error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        return fail(payload, "QEMU_VERSION_PROBE_OS_ERROR", out=out)

    version_text = version.stdout or version.stderr
    first_line = version_text.splitlines()[0] if version_text else ""
    payload["qemu_version"] = first_line or "UNKNOWN"
    payload["qemu_version_returncode"] = version.returncode
    if version.returncode != 0 or not first_line.startswith("QEMU emulator version "):
        return fail(payload, "QEMU_VERSION_PROBE_FAILED", out=out)

    cmd = [
        str(qemu_path),
        "-machine", "pc,accel=tcg",
        "-cpu", "max",
        "-m", "16M",
        "-bios", str(rom),
        "-display", "none",
        "-serial", "none",
        "-monitor", "none",
        "-debugcon", "stdio",
        "-global", "isa-debugcon.iobase=0xe9",
        "-d", "int,guest_errors,cpu_reset",
        "-D", "/dev/stderr",
        "-no-reboot",
        "-no-shutdown",
    ]
    payload["command"] = cmd

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
    except OSError as exc:
        payload["qemu_spawn_error"] = {"type": type(exc).__name__, "message": str(exc)}
        return fail(payload, "QEMU_BOOT_SPAWN_FAILED", out=out)

    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=args.timeout)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        payload["observation_timeout_s"] = args.timeout
        _kill_process_group(proc)
        try:
            stdout, stderr = proc.communicate(timeout=args.drain_timeout)
        except subprocess.TimeoutExpired as drain_exc:
            payload["qemu_drain_timeout_s"] = args.drain_timeout
            payload["qemu_partial_stdout"] = _text(
                drain_exc.stdout or drain_exc.output or exc.stdout or exc.output
            )
            payload["qemu_partial_stderr"] = _text(drain_exc.stderr or exc.stderr)
            _kill_process_group(proc)
            return fail(payload, "QEMU_PIPE_DRAIN_TIMEOUT", out=out)
    except OSError as exc:
        _kill_process_group(proc)
        payload["qemu_communicate_error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        return fail(payload, "QEMU_BOOT_IO_ERROR", out=out)

    lines = [line.strip() for line in stdout.splitlines()]
    payload["debug_output"] = stdout
    payload["debug_lines"] = lines
    payload["stderr"] = stderr
    payload["process_alive_at_observation_timeout"] = timed_out
    payload["process_returncode_after_capture"] = proc.returncode
    payload["failure_marker_present"] = any(line in FAILURE_MARKERS for line in lines)
    payload["expected_sequence_present"] = exact_marker_subsequence(lines, EXPECTED_ORDER)
    payload["post_sched_nonexit_observed"] = timed_out

    passed = (
        bool(payload["expected_sequence_present"])
        and not bool(payload["failure_marker_present"])
        and timed_out
    )
    if passed:
        status = (
            "PASS_QEMU_BOOT_CONFORMANCE_PINNED"
            if args.expected_qemu_sha256
            else "PASS_QEMU_BOOT_CONFORMANCE_UNPINNED_BINARY"
        )
        return emit(payload, status=status, reason=None, exit_code=0, out=out)

    if not payload["expected_sequence_present"]:
        reason = "EXPECTED_DEBUG_SEQUENCE_MISSING"
    elif payload["failure_marker_present"]:
        reason = "BOOT_FAILURE_MARKER"
    else:
        reason = "QEMU_EXITED_BEFORE_EXPECTED_POST_SCHED_NONEXIT"
    return emit(
        payload,
        status="FAIL_QEMU_BOOT_CONFORMANCE",
        reason=reason,
        exit_code=1,
        out=out,
    )


if __name__ == "__main__":
    raise SystemExit(main())
