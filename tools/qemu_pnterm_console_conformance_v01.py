#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
from typing import Any

SCHEMA = "PNTERM_CONSOLE_QEMU_CONFORMANCE_V0_1"
BUILD_SCHEMA = "PNTERM_CONSOLE_QEMU_BUILD_V0_1"
EXPECTED_DEBUG = ["PNROM", "PN32", "PN64", "T36ID", "PNCORE.CONSOLE", "UART.OK", "PNTERM.READY"]
FAIL_MARKERS = {"I!", "X"}
RESET_PREFIX = bytes([0xEA, 0x00, 0x00, 0x00, 0xF0])
RESET_OFFSET = 0xFFF0
ROM_BYTES = 65536


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


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


def kill_group(proc: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            proc.kill()
        except OSError:
            pass


def load_verified_receipt(path: Path, expected_schema: str) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("receipt must be object")
    recorded = data.get("receipt_sha256")
    core = dict(data)
    core.pop("receipt_sha256", None)
    if recorded != hashlib.sha256(canonical_bytes(core)).hexdigest():
        raise ValueError("receipt digest mismatch")
    if data.get("schema") != expected_schema:
        raise ValueError(f"unexpected receipt schema: {data.get('schema')}")
    return data


def command_value(cmd: list[str], flag: str) -> str:
    try:
        i = cmd.index(flag)
    except ValueError as exc:
        raise ValueError(f"missing QEMU flag {flag}") from exc
    if i + 1 >= len(cmd):
        raise ValueError(f"missing QEMU value for {flag}")
    return cmd[i + 1]


def validate_command(cmd: list[str], hard: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "machine": command_value(cmd, "-machine") == hard["machine"],
        "cpu": command_value(cmd, "-cpu") == hard["cpu"],
        "memory": command_value(cmd, "-m") == hard["memory"],
        "bios": Path(command_value(cmd, "-bios")).name == hard["bios_basename"],
        "display": command_value(cmd, "-display") == hard["display"],
        "serial": command_value(cmd, "-serial") == hard["serial"],
        "monitor": command_value(cmd, "-monitor") == hard["monitor"],
        "debugcon_file": command_value(cmd, "-debugcon").startswith("file:"),
        "debugcon_iobase": command_value(cmd, "-global") == f"isa-debugcon.iobase={hard['debugcon_iobase']}",
        "no_reboot": "-no-reboot" in cmd and hard["no_reboot"] is True,
        "no_shutdown": "-no-shutdown" in cmd and hard["no_shutdown"] is True,
        "no_drive": "-drive" not in cmd,
    }
    failed = [k for k, v in checks.items() if not v]
    if failed:
        raise ValueError(f"QEMU console semantic drift: {failed}")
    return checks


def run_case(qemu: Path, rom: Path, hard: dict[str, Any], name: str, input_bytes: bytes, required: list[bytes], forbidden: list[bytes] | None = None, exact_counts: dict[bytes, int] | None = None) -> dict[str, Any]:
    forbidden = forbidden or []
    exact_counts = exact_counts or {}
    with tempfile.TemporaryDirectory(prefix="bioos-pnterm-") as td:
        debug_path = Path(td) / "debugcon.log"
        cmd = [
            str(qemu),
            "-machine", hard["machine"],
            "-cpu", hard["cpu"],
            "-m", hard["memory"],
            "-bios", str(rom),
            "-display", hard["display"],
            "-serial", hard["serial"],
            "-monitor", hard["monitor"],
            "-debugcon", f"file:{debug_path}",
            "-global", f"isa-debugcon.iobase={hard['debugcon_iobase']}",
            "-no-reboot",
            "-no-shutdown",
        ]
        checks = validate_command(cmd, hard)
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        if proc.stdin is None:
            kill_group(proc)
            raise RuntimeError("QEMU stdin pipe unavailable")
        time.sleep(0.25)
        proc.stdin.write(input_bytes)
        proc.stdin.flush()
        timed_out = False
        try:
            proc.wait(timeout=float(hard["observation_timeout_seconds"]))
        except subprocess.TimeoutExpired:
            timed_out = True
            kill_group(proc)
        try:
            proc.stdin.close()
        except OSError:
            pass
        proc.stdin = None
        stdout, stderr = proc.communicate(timeout=2.0)
        debug_raw = debug_path.read_bytes() if debug_path.exists() else b""

    debug_lines = [line.strip() for line in debug_raw.decode("utf-8", errors="replace").splitlines() if line.strip()]
    serial_text = stdout.decode("utf-8", errors="replace")
    stderr_text = stderr.decode("utf-8", errors="replace")
    required_ok = {item.decode("utf-8", errors="replace"): item in stdout for item in required}
    forbidden_ok = {item.decode("utf-8", errors="replace"): item not in stdout for item in forbidden}
    count_ok = {item.decode("utf-8", errors="replace"): stdout.count(item) == expected for item, expected in exact_counts.items()}
    debug_ok = exact_subsequence(debug_lines, EXPECTED_DEBUG) and not any(line in FAIL_MARKERS for line in debug_lines)
    live_ok = timed_out
    passed = debug_ok and live_ok and all(required_ok.values()) and all(forbidden_ok.values()) and all(count_ok.values())
    return {
        "name": name,
        "status": "PASS" if passed else "FAIL",
        "input_hex": input_bytes.hex(),
        "command": cmd,
        "command_semantic_checks": checks,
        "timed_out_live_console_expected": timed_out,
        "returncode_after_capture": proc.returncode,
        "serial_output": serial_text,
        "stderr": stderr_text,
        "debug_lines": debug_lines,
        "debug_sequence_pass": debug_ok,
        "required_output_checks": required_ok,
        "forbidden_output_checks": forbidden_ok,
        "exact_count_checks": count_ok,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Interactive PNTERM UART16550 QEMU conformance")
    ap.add_argument("--spec", type=Path, default=Path("spec/EMULATION_REFERENCE_CONSOLE_SPEC_V0_1.json"))
    ap.add_argument("--rom", type=Path, default=Path("build/x86_64/pnterm_console_qemu_test.bin"))
    ap.add_argument("--build-receipt", type=Path, default=Path("provenance/PNTERM_CONSOLE_QEMU_BUILD_V0_1.json"))
    ap.add_argument("--qemu", default="qemu-system-x86_64")
    ap.add_argument("--expected-qemu-sha256", default=None)
    ap.add_argument("--out", type=Path, default=Path("provenance/PNTERM_CONSOLE_QEMU_CONFORMANCE_V0_1.json"))
    args = ap.parse_args()

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "FAIL_CLOSED",
        "canon_allowed": False,
        "physical_machine_claim": False,
        "epistemic": "CHYBA",
    }
    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
        if spec.get("schema") != "BIOOS_EMULATION_REFERENCE_CONSOLE_SPEC_V0_1":
            raise ValueError("unexpected console reference spec schema")
        hard = spec.get("hard_pins")
        if not isinstance(hard, dict):
            raise ValueError("console hard_pins missing")
        timeout = float(hard["observation_timeout_seconds"])
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("invalid console observation timeout")

        build = load_verified_receipt(args.build_receipt, BUILD_SCHEMA)
        if build.get("status") != "PASS_HOST_BUILD" or build.get("canon_allowed") is not False:
            raise ValueError("console build receipt not admissible")
        if build.get("console", {}).get("write_commands") != 0 or build.get("console", {}).get("arbitrary_shell") is not False:
            raise ValueError("console build authority boundary open")

        raw = args.rom.read_bytes()
        if len(raw) != ROM_BYTES or raw[RESET_OFFSET:RESET_OFFSET + len(RESET_PREFIX)] != RESET_PREFIX:
            raise ValueError("console ROM geometry/reset vector mismatch")
        if build.get("rom_sha256") != hashlib.sha256(raw).hexdigest():
            raise ValueError("console ROM digest mismatch with build receipt")

        qemu_raw = shutil.which(args.qemu)
        if not qemu_raw:
            raise FileNotFoundError("QEMU executable not found")
        qemu = Path(qemu_raw).resolve(strict=True)
        qemu_sha = sha256_file(qemu)
        if args.expected_qemu_sha256 and qemu_sha != args.expected_qemu_sha256:
            raise ValueError("QEMU binary SHA mismatch")
        version = subprocess.run([str(qemu), "--version"], capture_output=True, text=True, check=False, timeout=5.0)
        version_text = version.stdout or version.stderr
        version_line = version_text.splitlines()[0] if version_text else ""
        if version.returncode != 0 or not version_line.startswith("QEMU emulator version "):
            raise RuntimeError("QEMU version probe failed")

        common = [b"BioOS PNTERM QEMU v0.1\r\n", b"bioos> "]
        cases = [
            run_case(qemu, args.rom, hard, "help_lf", b"help\n", common + [b"help status echo\r\n"]),
            run_case(qemu, args.rom, hard, "status_crlf_single_terminator", b"status\r\n", common + [b"console=READY authority=READ_ONLY canon=false\r\n"], exact_counts={b"console=READY authority=READ_ONLY canon=false\r\n": 1}),
            run_case(qemu, args.rom, hard, "echo", b"echo hello\n", common + [b"hello\r\n"]),
            run_case(qemu, args.rom, hard, "backspace_edit", b"echo helo\x08lo\n", common + [b"hello\r\n"]),
            run_case(qemu, args.rom, hard, "unknown_command", b"shutdown\n", common + [b"ERR UNKNOWN\r\n"], forbidden=[b"console=READY authority=READ_ONLY canon=false\r\n"]),
            run_case(qemu, args.rom, hard, "control_char_fail_closed", b"bad\x1bseq\n", common + [b"ERR CONTROL\r\n"], forbidden=[b"ERR UNKNOWN\r\n"]),
            run_case(qemu, args.rom, hard, "nonascii_fail_closed", b"\xc3\xa9\n", common + [b"ERR NONASCII\r\n"], forbidden=[b"ERR UNKNOWN\r\n"]),
            run_case(qemu, args.rom, hard, "line_overflow_fail_closed", b"a" * 129 + b"\n", common + [b"ERR OVERFLOW\r\n"], forbidden=[b"ERR UNKNOWN\r\n"]),
        ]
        if not all(case["status"] == "PASS" for case in cases):
            failed = [case["name"] for case in cases if case["status"] != "PASS"]
            raise RuntimeError(f"console conformance cases failed: {failed}")

        payload.update(
            status="PASS_QEMU_PNTERM_INTERACTIVE_READONLY_CONSOLE",
            case_count=len(cases),
            cases=cases,
            expected_debug_order=EXPECTED_DEBUG,
            build_receipt_sha256=build["receipt_sha256"],
            rom_sha256=hashlib.sha256(raw).hexdigest(),
            spec_sha256=hashlib.sha256(canonical_bytes(spec)).hexdigest(),
            observed_qemu={
                "version": version_line,
                "binary_path": str(qemu),
                "binary_sha256": qemu_sha,
                "binary_pinned": bool(args.expected_qemu_sha256),
            },
            semantic_boundary=spec.get("semantic_boundary"),
            claim_boundary=(
                "Interactive QEMU UART16550 console realization with deterministic input/output, bounded line editing, "
                "read-only help/status/echo dispatch, CRLF handling, and fail-closed unknown/control/non-ASCII/overflow cases. "
                "This proves the bounded ASCII transport realization only; not full Unicode PNTERM semantics, a general shell, "
                "bare-metal operation, physical-device behavior, or canon."
            ),
        )
        code = 0
    except Exception as exc:
        payload.update(error_type=type(exc).__name__, error=str(exc))
        code = 2

    core = dict(payload)
    core.pop("receipt_sha256", None)
    payload["receipt_sha256"] = hashlib.sha256(canonical_bytes(core)).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
