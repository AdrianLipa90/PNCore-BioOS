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
from typing import Any, Callable

SCHEMA = "BIOOS_VECTOR_NATIVE_QHTRI_QEMU_ADVERSARIAL_V0_1"
BUILD_SCHEMA = "BIOOS_VECTOR_NATIVE_QHTRI_QEMU_BUILD_V0_1"
EXPECTED_SCOPE = "QEMU_TCG_VECTOR_NATIVE_QHTRI_EXACT_REPLAY_ROM"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def verify_build_receipt(obj: dict[str, Any]) -> None:
    if obj.get("schema") != BUILD_SCHEMA or obj.get("status") != "PASS_HOST_BUILD" or obj.get("scope") != EXPECTED_SCOPE:
        raise ValueError("build receipt contract mismatch")
    recorded = obj.get("receipt_sha256")
    if not isinstance(recorded, str) or len(recorded) != 64:
        raise ValueError("invalid build receipt digest")
    body = dict(obj)
    del body["receipt_sha256"]
    if hashlib.sha256(canonical_bytes(body)).hexdigest() != recorded:
        raise ValueError("build receipt digest mismatch")


def kill_group(proc: subprocess.Popen[str]) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except OSError:
        try:
            proc.kill()
        except OSError:
            pass


def run_case(qemu: str, rom: Path, timeout: float) -> dict[str, Any]:
    cmd = [
        qemu, "-machine", "pc,accel=tcg", "-cpu", "max", "-m", "16M",
        "-bios", str(rom), "-display", "none", "-serial", "none", "-monitor", "none",
        "-debugcon", "stdio", "-global", "isa-debugcon.iobase=0xe9",
        "-no-reboot", "-no-shutdown",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        kill_group(proc)
        stdout, stderr = proc.communicate(timeout=2.0)
    lines = [line.strip() for line in stdout.splitlines()]
    fail_seen = "PNVQ.X" in lines
    ok_seen = "PNVQ.OK" in lines
    pnvq_seen = "PNVQ" in lines
    t36_seen = "T36ID" in lines
    return {
        "rom_sha256": hashlib.sha256(rom.read_bytes()).hexdigest(),
        "debug_lines": lines,
        "stderr": stderr,
        "timed_out_after_fail_halt": timed_out,
        "t36_identity_passed_before_replay_gate": t36_seen,
        "replay_gate_entered": pnvq_seen,
        "failure_marker_seen": fail_seen,
        "success_marker_seen": ok_seen,
        "pass": bool(t36_seen and pnvq_seen and fail_seen and not ok_seen and timed_out),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Adversarial fail-closed mutations for the exact vector-native QHTRI QEMU replay gate")
    ap.add_argument("repo_root", type=Path, nargs="?", default=Path("."))
    ap.add_argument("--rom", type=Path, default=Path("build/x86_64/bioos_vector_native_qhtri_qemu.bin"))
    ap.add_argument("--build-receipt", type=Path, default=Path("provenance/BIOOS_VECTOR_NATIVE_QHTRI_QEMU_BUILD_V0_1.json"))
    ap.add_argument("--out", type=Path, default=Path("provenance/BIOOS_VECTOR_NATIVE_QHTRI_QEMU_ADVERSARIAL_V0_1.json"))
    ap.add_argument("--qemu", default="qemu-system-x86_64")
    ap.add_argument("--timeout", type=float, default=2.0)
    args = ap.parse_args()

    root = args.repo_root.resolve()
    resolve = lambda path: path if path.is_absolute() else root / path
    rom_path = resolve(args.rom)
    build_receipt_path = resolve(args.build_receipt)
    out = resolve(args.out)

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "scope": "QEMU_TCG_VECTOR_NATIVE_QHTRI_FAIL_CLOSED_MUTATIONS",
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "physical_h200_execution_claim": False,
        "physical_qpu_claim": False,
        "physical_machine_claim": False,
        "epistemic": "CHYBA",
    }

    def emit(status: str, reason: str | None, code: int) -> int:
        payload["status"] = status
        payload["reason"] = reason
        payload["receipt_sha256"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return code

    if not math.isfinite(args.timeout) or args.timeout <= 0:
        return emit("FAIL_CLOSED", "INVALID_TIMEOUT", 2)
    qemu = shutil.which(args.qemu)
    if not qemu:
        return emit("BLOCKED_QEMU_MISSING", "QEMU_EXECUTABLE_NOT_FOUND", 2)

    try:
        build_receipt = json.loads(build_receipt_path.read_text(encoding="utf-8"))
        verify_build_receipt(build_receipt)
        base = bytearray(rom_path.read_bytes())
    except Exception as exc:
        payload["preflight_error"] = {"type": type(exc).__name__, "message": str(exc)}
        return emit("FAIL_CLOSED", "PREFLIGHT_INVALID", 2)

    if len(base) != 65536 or hashlib.sha256(base).hexdigest() != build_receipt.get("rom_sha256"):
        return emit("FAIL_CLOSED", "BASE_ROM_BINDING_MISMATCH", 2)
    replay_offset = int(build_receipt.get("replay_rom_offset", -1))
    replay_bytes = int(build_receipt.get("replay_binary_bytes", -1))
    if replay_offset < 0 or replay_bytes != 680 or replay_offset + replay_bytes > len(base):
        return emit("FAIL_CLOSED", "REPLAY_GEOMETRY_INVALID", 2)

    build_dir = root / "build/x86_64"
    cases: list[tuple[str, Callable[[bytearray], None]]] = []

    def bad_dimension(raw: bytearray) -> None:
        struct.pack_into("<I", raw, replay_offset + 12, 35)

    def wrong_tick(raw: bytearray) -> None:
        struct.pack_into("<Q", raw, replay_offset + 16, 20216)

    def wrong_edge_i(raw: bytearray) -> None:
        struct.pack_into("<i", raw, replay_offset + 24, 23)

    def wrong_coupling(raw: bytearray) -> None:
        struct.pack_into("<d", raw, replay_offset + 32, 0.5)

    def nonfinite_phi(raw: bytearray) -> None:
        struct.pack_into("<Q", raw, replay_offset + 40, 0x7ff0000000000000)

    def finite_phi_single_bit(raw: bytearray) -> None:
        value = struct.unpack_from("<Q", raw, replay_offset + 40)[0]
        struct.pack_into("<Q", raw, replay_offset + 40, value ^ 0x1)

    def source_lineage_single_bit(raw: bytearray) -> None:
        raw[replay_offset + 616] ^= 0x1

    def working_state_single_bit(raw: bytearray) -> None:
        raw[replay_offset + 648] ^= 0x1

    def zero_source_lineage(raw: bytearray) -> None:
        raw[replay_offset + 616:replay_offset + 648] = b"\x00" * 32

    cases.extend([
        ("DIMENSION_35", bad_dimension),
        ("TICK_PLUS_ONE", wrong_tick),
        ("EDGE_I_CHANGED", wrong_edge_i),
        ("COUPLING_HALF", wrong_coupling),
        ("PHI0_POSITIVE_INFINITY", nonfinite_phi),
        ("PHI0_FINITE_SINGLE_BIT", finite_phi_single_bit),
        ("SOURCE_RECEIPT_SINGLE_BIT", source_lineage_single_bit),
        ("WORKING_STATE_SINGLE_BIT", working_state_single_bit),
        ("SOURCE_RECEIPT_ZEROED", zero_source_lineage),
    ])

    results: dict[str, Any] = {}
    for name, mutate in cases:
        mutated = bytearray(base)
        mutate(mutated)
        case_path = build_dir / f"bioos_vector_native_qhtri_adv_{name.lower()}.bin"
        case_path.write_bytes(mutated)
        results[name] = run_case(qemu, case_path, args.timeout)

    payload["base_rom_sha256"] = build_receipt["rom_sha256"]
    payload["build_receipt_sha256"] = build_receipt["receipt_sha256"]
    payload["replay_rom_offset"] = replay_offset
    payload["cases"] = results
    payload["cases_total"] = len(results)
    payload["cases_passed"] = sum(1 for result in results.values() if result["pass"])
    payload["qemu_executed"] = True
    if payload["cases_passed"] != payload["cases_total"]:
        return emit("FAIL_QEMU_VECTOR_NATIVE_REPLAY_ADVERSARIAL", "ONE_OR_MORE_MUTATIONS_DID_NOT_FAIL_CLOSED", 1)
    return emit("PASS_QEMU_VECTOR_NATIVE_REPLAY_ADVERSARIAL", None, 0)


if __name__ == "__main__":
    raise SystemExit(main())
