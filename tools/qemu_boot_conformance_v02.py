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
EXPECTED_ORDER = ["PNROM", "PN32", "PN64", "PNCORE", "PNR.OK", "SIGMA0", "SCHED"]
EXPECTED_RESET_VECTOR = "0x000ffff0"
EXPECTED_ROM_SIZE_BYTES = 65536
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


def parse_pnr(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        s = raw.strip()
        if not s or s.startswith("#") or s.startswith("END "):
            continue
        parts = s.split(None, 1)
        if len(parts) != 2:
            continue
        key, value = parts
        if key in out:
            raise ValueError(f"duplicate PNR field {key} at line {lineno}")
        out[key] = value
    return out


def exact_marker_subsequence(text: str, seq: list[str]) -> bool:
    # Port 0xE9 emits one canonical witness marker per line. Substring matching
    # is deliberately forbidden: e.g. 'xxPNROMxx' is not the PNROM witness.
    lines = [line.strip() for line in text.splitlines()]
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
    out: Path | None,
) -> int:
    payload["status"] = status
    payload["reason"] = reason
    payload.pop("receipt_sha256", None)
    payload["receipt_sha256"] = sha256_obj(payload)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if out is not None:
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8")
        except OSError as exc:
            # Do not lose the primary result because the optional receipt path
            # was unwritable. Surface the secondary evidence failure explicitly.
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
    out: Path | None,
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo_root", type=Path)
    ap.add_argument("--rom", type=Path, default=None)
    ap.add_argument("--qemu", default="qemu-system-x86_64")
    ap.add_argument("--timeout", type=float, default=2.0, help="boot witness observation window")
    ap.add_argument("--probe-timeout", type=float, default=5.0, help="independent QEMU --version timeout")
    ap.add_argument("--drain-timeout", type=float, default=2.0, help="bounded pipe drain after terminating QEMU")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--expected-qemu-sha256", default=None)
    ap.add_argument("--expected-pnr-sha256", default=None)
    args = ap.parse_args()

    pnr_path = args.repo_root / "realizations/x86_64/GENESIS_X86_64_V0_1.pnr"
    rom = args.rom or (args.repo_root / "build/pnrom_v0_2.bin")
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "rom": str(rom),
        "pnr": str(pnr_path),
        "expected_debug_order": EXPECTED_ORDER,
        "expected_reset_vector": EXPECTED_RESET_VECTOR,
        "expected_rom_size_bytes": EXPECTED_ROM_SIZE_BYTES,
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
            return fail(payload, "INVALID_TIMEOUT", out=args.out)

    if not pnr_path.is_file():
        return fail(payload, "PNR_MISSING", out=args.out)
    if not rom.is_file():
        return fail(payload, "ROM_MISSING", out=args.out)

    try:
        pnr = parse_pnr(pnr_path)
        pnr_sha = sha256_file(pnr_path)
    except (OSError, UnicodeError, ValueError) as exc:
        payload["pnr_error"] = {"type": type(exc).__name__, "message": str(exc)}
        return fail(payload, "PNR_PARSE_OR_READ_ERROR", out=args.out)

    payload["pnr_sha256"] = pnr_sha
    payload["expected_pnr_sha256"] = args.expected_pnr_sha256
    if args.expected_pnr_sha256 is not None:
        if not HEX64.fullmatch(args.expected_pnr_sha256):
            return fail(payload, "EXPECTED_PNR_SHA256_INVALID", out=args.out)
        if pnr_sha != args.expected_pnr_sha256:
            return fail(payload, "PNR_SHA_MISMATCH", out=args.out)

    required_fields = (
        "ROM_SHA256",
        "ROM_SIZE_BYTES",
        "RESET_VECTOR",
        "REALIZATION_ID",
        "CANON_ALLOWED",
    )
    missing = [name for name in required_fields if not pnr.get(name)]
    payload["pnr_required_fields_present"] = not missing
    if missing:
        payload["missing_pnr_fields"] = missing
        return fail(payload, "PNR_REQUIRED_FIELD_MISSING", out=args.out)

    expected_sha = pnr["ROM_SHA256"]
    if not HEX64.fullmatch(expected_sha):
        payload["expected_rom_sha256"] = expected_sha
        return fail(payload, "PNR_ROM_SHA256_INVALID", out=args.out)

    try:
        actual_sha = sha256_file(rom)
        actual_size = rom.stat().st_size
    except OSError as exc:
        payload["rom_error"] = {"type": type(exc).__name__, "message": str(exc)}
        return fail(payload, "ROM_READ_ERROR", out=args.out)

    payload["rom_sha256"] = actual_sha
    payload["expected_rom_sha256"] = expected_sha
    if actual_sha != expected_sha:
        return fail(payload, "ROM_SHA_MISMATCH", out=args.out)

    try:
        expected_size = int(pnr["ROM_SIZE_BYTES"], 10)
    except ValueError:
        return fail(payload, "PNR_ROM_SIZE_INVALID", out=args.out)
    payload["rom_size_bytes"] = actual_size
    payload["pnr_rom_size_bytes"] = expected_size
    if expected_size != EXPECTED_ROM_SIZE_BYTES:
        return fail(payload, "PNR_ROM_SIZE_CONTRACT_MISMATCH", out=args.out)
    if actual_size != expected_size:
        return fail(payload, "ROM_SIZE_MISMATCH", out=args.out)

    payload["reset_vector"] = pnr["RESET_VECTOR"]
    if pnr["RESET_VECTOR"].lower() != EXPECTED_RESET_VECTOR:
        return fail(payload, "PNR_RESET_VECTOR_MISMATCH", out=args.out)
    if pnr["CANON_ALLOWED"].upper() != "FALSE":
        return fail(payload, "PNR_CANON_BOUNDARY_OPEN", out=args.out)

    if args.expected_qemu_sha256 is not None and not HEX64.fullmatch(args.expected_qemu_sha256):
        return fail(payload, "EXPECTED_QEMU_SHA256_INVALID", out=args.out)

    qemu = shutil.which(args.qemu)
    if not qemu:
        return fail(
            payload,
            "QEMU_EXECUTABLE_NOT_FOUND",
            out=args.out,
            status="BLOCKED_QEMU_MISSING",
        )

    try:
        qemu_path = Path(qemu).resolve(strict=True)
        qemu_sha = sha256_file(qemu_path)
    except OSError as exc:
        payload["qemu_path_error"] = {"type": type(exc).__name__, "message": str(exc)}
        return fail(payload, "QEMU_BINARY_READ_ERROR", out=args.out)

    payload["qemu_binary"] = str(qemu_path)
    payload["qemu_binary_sha256"] = qemu_sha
    payload["expected_qemu_sha256"] = args.expected_qemu_sha256
    payload["qemu_binary_pinned"] = bool(args.expected_qemu_sha256)
    if args.expected_qemu_sha256 and qemu_sha != args.expected_qemu_sha256:
        return fail(payload, "QEMU_BINARY_SHA_MISMATCH", out=args.out)

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
        return fail(payload, "QEMU_VERSION_PROBE_TIMEOUT", out=args.out)
    except OSError as exc:
        payload["qemu_version_probe_error"] = {"type": type(exc).__name__, "message": str(exc)}
        return fail(payload, "QEMU_VERSION_PROBE_OS_ERROR", out=args.out)

    version_text = version.stdout or version.stderr
    first_line = version_text.splitlines()[0] if version_text else ""
    payload["qemu_version"] = first_line or "UNKNOWN"
    payload["qemu_version_returncode"] = version.returncode
    if version.returncode != 0 or not first_line.startswith("QEMU emulator version "):
        return fail(payload, "QEMU_VERSION_PROBE_FAILED", out=args.out)

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
        return fail(payload, "QEMU_BOOT_SPAWN_FAILED", out=args.out)

    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=args.timeout)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        payload["boot_timeout_s"] = args.timeout
        _kill_process_group(proc)
        try:
            stdout, stderr = proc.communicate(timeout=args.drain_timeout)
        except subprocess.TimeoutExpired as drain_exc:
            payload["qemu_drain_timeout_s"] = args.drain_timeout
            payload["qemu_partial_stdout"] = _text(drain_exc.stdout or drain_exc.output or exc.stdout or exc.output)
            payload["qemu_partial_stderr"] = _text(drain_exc.stderr or exc.stderr)
            _kill_process_group(proc)
            return fail(payload, "QEMU_PIPE_DRAIN_TIMEOUT", out=args.out)
    except OSError as exc:
        _kill_process_group(proc)
        payload["qemu_communicate_error"] = {"type": type(exc).__name__, "message": str(exc)}
        return fail(payload, "QEMU_BOOT_IO_ERROR", out=args.out)

    lines = [line.strip() for line in stdout.splitlines()]
    payload["process_alive_at_observation_timeout"] = timed_out
    payload["process_returncode_after_capture"] = proc.returncode
    payload["debug_output"] = stdout
    payload["debug_lines"] = lines
    payload["stderr"] = stderr
    payload["failure_marker_present"] = any(line == "X" for line in lines)
    payload["expected_sequence_present"] = exact_marker_subsequence(stdout, EXPECTED_ORDER)

    # Current pinned ROM reaches an explicit `hlt; jmp` loop immediately after
    # SCHED. Therefore, for this harness, an early emulator exit is not accepted
    # as the same witness as a process that remains alive through the observation
    # window after the complete debug sequence has appeared.
    payload["post_sched_nonexit_observed"] = timed_out

    passed = (
        payload["expected_sequence_present"]
        and not payload["failure_marker_present"]
        and timed_out
    )
    if passed:
        status = (
            "PASS_QEMU_BOOT_CONFORMANCE_PINNED"
            if args.expected_qemu_sha256
            else "PASS_QEMU_BOOT_CONFORMANCE_UNPINNED_BINARY"
        )
        return emit(payload, status=status, reason=None, exit_code=0, out=args.out)

    if not payload["expected_sequence_present"]:
        reason = "EXPECTED_DEBUG_SEQUENCE_MISSING"
    elif payload["failure_marker_present"]:
        reason = "PNCORE_FAILURE_MARKER"
    else:
        reason = "QEMU_EXITED_BEFORE_EXPECTED_POST_SCHED_NONEXIT"
    return emit(payload, status="FAIL_QEMU_BOOT_CONFORMANCE", reason=reason, exit_code=1, out=args.out)


if __name__ == "__main__":
    raise SystemExit(main())
