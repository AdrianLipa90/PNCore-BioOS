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

from tools.vector_native_qhtri_replay_v01 import build_replay_binary, validate_replay_receipt, validate_source_snapshot

SCHEMA = "BIOOS_VECTOR_NATIVE_QHTRI_QEMU_CONFORMANCE_V0_1"
BUILD_SCHEMA = "BIOOS_VECTOR_NATIVE_QHTRI_QEMU_BUILD_V0_1"
EXPECTED_SCOPE = "QEMU_TCG_VECTOR_NATIVE_QHTRI_EXACT_REPLAY_ROM"
EXPECTED_ROM_BYTES = 65536
RESET_PREFIX = bytes([0xEA, 0x00, 0x00, 0x00, 0xF0])


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def fold64(replay: bytes) -> int:
    value = 0
    for offset in range(40, 616, 8):
        word = struct.unpack_from("<Q", replay, offset)[0]
        value ^= word
        value = ((value << 1) & 0xffffffffffffffff) | (value >> 63)
    return value


def verify_receipt(obj: dict[str, Any]) -> None:
    recorded = obj.get("receipt_sha256")
    if not isinstance(recorded, str) or len(recorded) != 64:
        raise ValueError("invalid build receipt digest")
    body = dict(obj)
    del body["receipt_sha256"]
    if hashlib.sha256(canonical_bytes(body)).hexdigest() != recorded:
        raise ValueError("build receipt digest mismatch")


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
    except OSError:
        try:
            proc.kill()
        except OSError:
            pass


def emit(payload: dict[str, Any], out: Path, status: str, reason: str | None, exit_code: int) -> int:
    payload["status"] = status
    payload["reason"] = reason
    payload["receipt_sha256"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return exit_code


def main() -> int:
    ap = argparse.ArgumentParser(description="Run exact vector-native QHTRI replay through the dedicated BioOS QEMU gate")
    ap.add_argument("repo_root", type=Path, nargs="?", default=Path("."))
    ap.add_argument("--rom", type=Path, default=Path("build/x86_64/bioos_vector_native_qhtri_qemu.bin"))
    ap.add_argument("--source", type=Path, default=Path("provenance/BIOOS_VECTOR_NATIVE_QHTRI_SOURCE_V0_1.json"))
    ap.add_argument("--replay-receipt", type=Path, default=Path("provenance/BIOOS_VECTOR_NATIVE_QHTRI_REPLAY_V0_1.json"))
    ap.add_argument("--build-receipt", type=Path, default=Path("provenance/BIOOS_VECTOR_NATIVE_QHTRI_QEMU_BUILD_V0_1.json"))
    ap.add_argument("--out", type=Path, default=Path("provenance/BIOOS_VECTOR_NATIVE_QHTRI_QEMU_CONFORMANCE_V0_1.json"))
    ap.add_argument("--qemu", default="qemu-system-x86_64")
    ap.add_argument("--timeout", type=float, default=3.0)
    args = ap.parse_args()

    root = args.repo_root.resolve()
    resolve = lambda p: p if p.is_absolute() else root / p
    rom = resolve(args.rom)
    source_path = resolve(args.source)
    replay_receipt_path = resolve(args.replay_receipt)
    build_receipt_path = resolve(args.build_receipt)
    out = resolve(args.out)
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "scope": EXPECTED_SCOPE,
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "physical_h200_execution_claim": False,
        "physical_qpu_claim": False,
        "physical_machine_claim": False,
        "epistemic": "CHYBA",
    }

    if not math.isfinite(args.timeout) or args.timeout <= 0:
        return emit(payload, out, "FAIL_CLOSED", "INVALID_TIMEOUT", 2)

    try:
        source = json.loads(source_path.read_text(encoding="utf-8"))
        state = validate_source_snapshot(source)
        replay = build_replay_binary(source)
        replay_receipt = json.loads(replay_receipt_path.read_text(encoding="utf-8"))
        validate_replay_receipt(replay_receipt, source)
        build_receipt = json.loads(build_receipt_path.read_text(encoding="utf-8"))
        verify_receipt(build_receipt)
    except Exception as exc:
        payload["preflight_error"] = {"type": type(exc).__name__, "message": str(exc)}
        return emit(payload, out, "FAIL_CLOSED", "PREFLIGHT_INVALID", 2)

    expected_fold = f"{fold64(replay):016x}"
    replay_sha = hashlib.sha256(replay).hexdigest()
    payload.update({
        "source_tick": state["tick"],
        "source_receipt_sha256": state["source_receipt_sha256"],
        "working_state_sha256": state["working_state_sha256"],
        "replay_binary_sha256": replay_sha,
        "expected_vector_fold64_hex": expected_fold,
        "build_receipt_sha256": build_receipt["receipt_sha256"],
    })

    if build_receipt.get("schema") != BUILD_SCHEMA or build_receipt.get("status") != "PASS_HOST_BUILD" or build_receipt.get("scope") != EXPECTED_SCOPE:
        return emit(payload, out, "FAIL_CLOSED", "BUILD_RECEIPT_CONTRACT_MISMATCH", 2)
    for key in ("runtime_execution_authority", "canon_write_authority", "physical_h200_execution_claim", "physical_qpu_claim", "physical_machine_claim"):
        if build_receipt.get(key) is not False:
            return emit(payload, out, "FAIL_CLOSED", f"AUTHORITY_BOUNDARY_OPEN:{key}", 2)
    if build_receipt.get("qemu_executed") is not False:
        return emit(payload, out, "FAIL_CLOSED", "BUILD_EXECUTION_LAYER_MIXED", 2)
    if build_receipt.get("source_receipt_sha256") != state["source_receipt_sha256"] or build_receipt.get("working_state_sha256") != state["working_state_sha256"]:
        return emit(payload, out, "FAIL_CLOSED", "SOURCE_LINEAGE_MISMATCH", 2)
    if build_receipt.get("replay_binary_sha256") != replay_sha or build_receipt.get("expected_vector_fold64_hex") != expected_fold:
        return emit(payload, out, "FAIL_CLOSED", "REPLAY_BINDING_MISMATCH", 2)

    raw = rom.read_bytes() if rom.is_file() else b""
    if len(raw) != EXPECTED_ROM_BYTES:
        return emit(payload, out, "FAIL_CLOSED", "ROM_SIZE_MISMATCH", 2)
    rom_sha = hashlib.sha256(raw).hexdigest()
    if build_receipt.get("rom_sha256") != rom_sha or raw[0xFFF0:0xFFF5] != RESET_PREFIX:
        return emit(payload, out, "FAIL_CLOSED", "ROM_BINDING_MISMATCH", 2)
    replay_offset = int(build_receipt.get("replay_rom_offset", -1))
    if replay_offset < 0 or raw[replay_offset:replay_offset + len(replay)] != replay:
        return emit(payload, out, "FAIL_CLOSED", "ROM_REPLAY_BYTES_MISMATCH", 2)

    qemu = shutil.which(args.qemu)
    if not qemu:
        return emit(payload, out, "BLOCKED_QEMU_MISSING", "QEMU_EXECUTABLE_NOT_FOUND", 2)

    expected_lines = ["PNROM", "PN32", "PN64", "T36ID", "PNVQ", f"PNVQ.FOLD={expected_fold}", "PNVQ.OK"]
    payload["expected_debug_order"] = expected_lines
    cmd = [
        qemu, "-machine", "pc,accel=tcg", "-cpu", "max", "-m", "16M",
        "-bios", str(rom), "-display", "none", "-serial", "none", "-monitor", "none",
        "-debugcon", "stdio", "-global", "isa-debugcon.iobase=0xe9",
        "-no-reboot", "-no-shutdown",
    ]
    payload["command"] = cmd
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=args.timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        kill_group(proc)
        stdout, stderr = proc.communicate(timeout=2.0)

    lines = [line.strip() for line in stdout.splitlines()]
    payload["debug_lines"] = lines
    payload["debug_output"] = stdout
    payload["stderr"] = stderr
    payload["qemu_observation_timed_out_after_success_halt"] = timed_out
    payload["expected_sequence_present"] = exact_subsequence(lines, expected_lines)
    payload["failure_marker_present"] = "PNVQ.X" in lines or "I!" in lines or "!" in lines
    payload["qemu_executed"] = True
    passed = payload["expected_sequence_present"] and not payload["failure_marker_present"] and timed_out
    if not passed:
        return emit(payload, out, "FAIL_QEMU_VECTOR_NATIVE_REPLAY", "EXPECTED_REPLAY_SEQUENCE_MISSING_OR_FAILED", 1)
    return emit(payload, out, "PASS_QEMU_VECTOR_NATIVE_REPLAY", None, 0)


if __name__ == "__main__":
    raise SystemExit(main())
