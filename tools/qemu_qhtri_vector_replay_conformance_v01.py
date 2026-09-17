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
import struct
import subprocess
from pathlib import Path
from typing import Any

SCHEMA = "PNCORE_QEMU_QHTRI_VECTOR_REPLAY_CONFORMANCE_V0_1"
BUILD_SCHEMA = "PNCORE_QEMU_QHTRI_VECTOR_REPLAY_BUILD_V0_1"
BUILD_SCOPE = "QHTRI_VECTOR_NATIVE_STATE_QEMU_REALIZATION_ADAPTER"
SOURCE_SCHEMA = "BIOOS_VECTOR_NATIVE_QHTRI_SOURCE_V0_1"
EXPECTED_ORDER = ["PNROM", "PN32", "PN64", "T36ID", "PNCORE", "PNR.OK", "SIGMA0", "SCHED"]
FAILURE_MARKERS = {"I!", "X"}
RESET_PREFIX = bytes([0xEA, 0x00, 0x00, 0x00, 0xF0])
RESET_OFFSET = 0xFFF0
EXPECTED_ROM_BYTES = 65536
PNVH_BYTES = 128 + 36 * 8
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


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


def resolve(root: Path, value: Any, name: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} path missing")
    path = Path(value)
    return path if path.is_absolute() else root / path


def verify_receipt(path: Path) -> tuple[dict[str, Any], str]:
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


def verify_pnvh_against_source(pnvh: bytes, source: dict[str, Any]) -> dict[str, Any]:
    if len(pnvh) != PNVH_BYTES:
        raise ValueError(f"PNVH must be {PNVH_BYTES} bytes")
    if pnvh[0:4] != b"PNVH" or pnvh[4:8] != b"36\x00\x00":
        raise ValueError("PNVH magic mismatch")
    major, minor, header_bytes, total_bytes, dim, width, endian, flags = struct.unpack_from(
        "<HHIIHHII", pnvh, 8
    )
    if (major, minor, header_bytes, total_bytes, dim, width, endian) != (
        1, 0, 128, PNVH_BYTES, 36, 8, 0x01020304
    ):
        raise ValueError("PNVH geometry/version mismatch")
    vector = pnvh[128:]
    expected = struct.pack("<36d", *[float(v) for v in source["phi"]])
    if vector != expected:
        raise ValueError("PNVH vector bytes do not exactly equal source QHTRI phi lanes")
    vector_sha = hashlib.sha256(vector).hexdigest()
    if pnvh[64:96].hex() != vector_sha:
        raise ValueError("PNVH embedded vector SHA mismatch")
    return {
        "major": major,
        "minor": minor,
        "flags": flags,
        "basis_binding_hex": pnvh[32:64].hex(),
        "vector_sha256": vector_sha,
        "source_context_sha256": pnvh[96:128].hex(),
    }


def kill_group(proc: subprocess.Popen[str]) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    except OSError:
        try:
            proc.kill()
        except OSError:
            pass


def emit(payload: dict[str, Any], out: Path, *, status: str, reason: str | None, code: int) -> int:
    payload["status"] = status
    payload["reason"] = reason
    payload.pop("receipt_sha256", None)
    payload["receipt_sha256"] = sha256_obj(payload)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return code


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Execute and verify the frozen QHTRI 36D vector replay through the x86_64/QEMU realization boundary"
    )
    ap.add_argument("repo_root", type=Path, nargs="?", default=Path("."))
    ap.add_argument(
        "--build-receipt",
        type=Path,
        default=Path("provenance/PNCORE_QEMU_QHTRI_VECTOR_REPLAY_BUILD_V0_1.json"),
    )
    ap.add_argument("--qemu", default="qemu-system-x86_64")
    ap.add_argument("--timeout", type=float, default=5.0)
    ap.add_argument("--probe-timeout", type=float, default=5.0)
    ap.add_argument("--drain-timeout", type=float, default=2.0)
    ap.add_argument("--expected-qemu-sha256", default=None)
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("provenance/PNCORE_QEMU_QHTRI_VECTOR_REPLAY_CONFORMANCE_V0_1.json"),
    )
    args = ap.parse_args()

    root = args.repo_root.resolve()
    build_receipt_path = args.build_receipt if args.build_receipt.is_absolute() else root / args.build_receipt
    out = args.out if args.out.is_absolute() else root / args.out

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "scope": BUILD_SCOPE,
        "semantic_runtime": "QHTRI_NOEMA_VECTOR_NATIVE",
        "realization_adapter": "X86_64_QEMU_TCG_BINARY_BOUNDARY",
        "binary_adapter_only": True,
        "expected_debug_order": EXPECTED_ORDER,
        "failure_markers": sorted(FAILURE_MARKERS),
        "physical_execution_claim": False,
        "physical_qpu_claim": False,
        "canon_allowed": False,
        "epistemic": "CHYBA",
    }

    for name, value in (("timeout", args.timeout), ("probe_timeout", args.probe_timeout), ("drain_timeout", args.drain_timeout)):
        if not math.isfinite(value) or value <= 0.0:
            payload["invalid_timeout_field"] = name
            return emit(payload, out, status="FAIL_CLOSED", reason="INVALID_TIMEOUT", code=2)

    try:
        build, build_file_sha = verify_receipt(build_receipt_path)
        if build.get("schema") != BUILD_SCHEMA:
            raise ValueError("build schema mismatch")
        if build.get("status") != "PASS_HOST_BUILD":
            raise ValueError("build status is not PASS_HOST_BUILD")
        if build.get("scope") != BUILD_SCOPE:
            raise ValueError("build scope mismatch")
        if build.get("binary_adapter_only") is not True:
            raise ValueError("build does not preserve binary-adapter-only boundary")
        if build.get("canon_allowed") is not False or build.get("physical_execution_claim") is not False or build.get("physical_qpu_claim") is not False:
            raise ValueError("build claim boundary is open")
        if build.get("qemu_executed") is not False:
            raise ValueError("build receipt mixes build and execution layers")

        source_path = resolve(root, build.get("source_snapshot"), "source_snapshot")
        pnvh_path = resolve(root, build.get("pnvh"), "pnvh")
        t36_path = resolve(root, build.get("t36_identity"), "t36_identity")
        rom_path = resolve(root, build.get("rom"), "rom")

        source_raw = source_path.read_bytes()
        source = json.loads(source_raw.decode("utf-8"))
        if not isinstance(source, dict) or source.get("schema") != SOURCE_SCHEMA:
            raise ValueError("source snapshot schema mismatch")
        if hashlib.sha256(source_raw).hexdigest() != build.get("source_snapshot_file_sha256"):
            raise ValueError("source snapshot file SHA mismatch")
        if source.get("receipt_sha256") != build.get("source_snapshot_receipt_sha256"):
            raise ValueError("source snapshot receipt lineage mismatch")
        if source.get("tick") != build.get("source_tick"):
            raise ValueError("source tick lineage mismatch")
        if source.get("surface_state", {}).get("noema_tick") != source.get("tick"):
            raise ValueError("source is not same-tick bound")

        pnvh = pnvh_path.read_bytes()
        pnvh_info = verify_pnvh_against_source(pnvh, source)
        if hashlib.sha256(pnvh).hexdigest() != build.get("pnvh_sha256"):
            raise ValueError("PNVH SHA mismatch")
        if pnvh_info["vector_sha256"] != build.get("vector_sha256"):
            raise ValueError("PNVH vector SHA differs from build vector SHA")
        if pnvh_info["basis_binding_hex"] != build.get("basis_binding_hex"):
            raise ValueError("PNVH basis binding mismatch")
        if pnvh_info["source_context_sha256"] != build.get("source_context_sha256"):
            raise ValueError("PNVH source-context binding mismatch")

        t36 = t36_path.read_bytes()
        if hashlib.sha256(t36).hexdigest() != build.get("t36_identity_sha256"):
            raise ValueError("T36 identity SHA mismatch")
        if len(t36) != 256:
            raise ValueError("T36 identity size mismatch")

        rom = rom_path.read_bytes()
        if len(rom) != EXPECTED_ROM_BYTES or build.get("rom_bytes") != len(rom):
            raise ValueError("ROM size mismatch")
        if hashlib.sha256(rom).hexdigest() != build.get("rom_sha256"):
            raise ValueError("ROM SHA mismatch")
        if rom[RESET_OFFSET:RESET_OFFSET + len(RESET_PREFIX)] != RESET_PREFIX:
            raise ValueError("ROM reset vector mismatch")
        if rom.count(pnvh) != 1 or build.get("pnvh_exact_rom_occurrences") != 1:
            raise ValueError("exact PNVH embedding is not unique")
        if rom.count(t36) != 1 or build.get("t36_exact_rom_occurrences") != 1:
            raise ValueError("exact T36 embedding is not unique")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError, KeyError, struct.error) as exc:
        payload["preflight_error"] = {"type": type(exc).__name__, "message": str(exc)}
        return emit(payload, out, status="FAIL_CLOSED", reason="REPLAY_PREFLIGHT_INVALID", code=2)

    payload.update({
        "build_receipt": str(build_receipt_path),
        "build_receipt_file_sha256": build_file_sha,
        "build_receipt_payload_sha256": build["receipt_sha256"],
        "source_snapshot": str(source_path),
        "source_snapshot_file_sha256": build["source_snapshot_file_sha256"],
        "source_snapshot_receipt_sha256": build["source_snapshot_receipt_sha256"],
        "source_tick": build["source_tick"],
        "vector_sha256": build["vector_sha256"],
        "pnvh_sha256": build["pnvh_sha256"],
        "t36_identity_sha256": build["t36_identity_sha256"],
        "rom": str(rom_path),
        "rom_sha256": build["rom_sha256"],
        "exact_source_phi_bytes_in_pnvh": True,
        "exact_pnvh_once_in_rom": True,
        "exact_t36_once_in_rom": True,
    })

    if args.expected_qemu_sha256 is not None and not HEX64.fullmatch(args.expected_qemu_sha256):
        return emit(payload, out, status="FAIL_CLOSED", reason="EXPECTED_QEMU_SHA256_INVALID", code=2)

    qemu = shutil.which(args.qemu)
    if not qemu:
        return emit(payload, out, status="BLOCKED_QEMU_MISSING", reason="QEMU_EXECUTABLE_NOT_FOUND", code=2)
    qemu_path = Path(qemu).resolve()
    try:
        qemu_sha = sha256_file(qemu_path)
    except OSError as exc:
        payload["qemu_error"] = {"type": type(exc).__name__, "message": str(exc)}
        return emit(payload, out, status="FAIL_CLOSED", reason="QEMU_BINARY_READ_ERROR", code=2)
    if args.expected_qemu_sha256 and qemu_sha != args.expected_qemu_sha256:
        payload["qemu_binary_sha256"] = qemu_sha
        return emit(payload, out, status="FAIL_CLOSED", reason="QEMU_BINARY_SHA_MISMATCH", code=2)

    try:
        version = subprocess.run(
            [str(qemu_path), "--version"],
            text=True,
            capture_output=True,
            check=False,
            timeout=args.probe_timeout,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        payload["qemu_version_error"] = {"type": type(exc).__name__, "message": str(exc)}
        return emit(payload, out, status="FAIL_CLOSED", reason="QEMU_VERSION_PROBE_FAILED", code=2)
    version_text = version.stdout or version.stderr
    first_line = version_text.splitlines()[0] if version_text else ""
    if version.returncode != 0 or not first_line.startswith("QEMU emulator version "):
        payload["qemu_version"] = first_line
        return emit(payload, out, status="FAIL_CLOSED", reason="QEMU_VERSION_PROBE_FAILED", code=2)

    payload["qemu_binary"] = str(qemu_path)
    payload["qemu_binary_sha256"] = qemu_sha
    payload["qemu_binary_pinned"] = bool(args.expected_qemu_sha256)
    payload["qemu_version"] = first_line

    cmd = [
        str(qemu_path),
        "-machine", "pc,accel=tcg",
        "-cpu", "max",
        "-m", "16M",
        "-bios", str(rom_path),
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
        return emit(payload, out, status="FAIL_CLOSED", reason="QEMU_BOOT_SPAWN_FAILED", code=2)

    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=args.timeout)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        kill_group(proc)
        try:
            stdout, stderr = proc.communicate(timeout=args.drain_timeout)
        except subprocess.TimeoutExpired:
            kill_group(proc)
            payload["partial_stdout"] = str(exc.stdout or exc.output or "")
            payload["partial_stderr"] = str(exc.stderr or "")
            return emit(payload, out, status="FAIL_CLOSED", reason="QEMU_PIPE_DRAIN_TIMEOUT", code=2)
    except OSError as exc:
        kill_group(proc)
        payload["qemu_io_error"] = {"type": type(exc).__name__, "message": str(exc)}
        return emit(payload, out, status="FAIL_CLOSED", reason="QEMU_BOOT_IO_ERROR", code=2)

    lines = [line.strip() for line in stdout.splitlines()]
    expected_sequence = exact_marker_subsequence(lines, EXPECTED_ORDER)
    failure_present = any(line in FAILURE_MARKERS for line in lines)
    t36_admission_observed = "T36ID" in lines

    payload.update({
        "debug_output": stdout,
        "debug_lines": lines,
        "stderr": stderr,
        "process_alive_at_observation_timeout": timed_out,
        "process_returncode_after_capture": proc.returncode,
        "expected_sequence_present": expected_sequence,
        "failure_marker_present": failure_present,
        "guest_t36_identity_admission_observed": t36_admission_observed,
        "guest_scheduler_reached": "SCHED" in lines,
        "qemu_executed": True,
    })

    passed = expected_sequence and not failure_present and timed_out and t36_admission_observed
    if not passed:
        return emit(payload, out, status="FAIL_CLOSED", reason="QHTRI_VECTOR_REPLAY_SEQUENCE_FAILED", code=2)

    return emit(
        payload,
        out,
        status="PASS_QEMU_QHTRI_VECTOR_REPLAY",
        reason=None,
        code=0,
    )


if __name__ == "__main__":
    raise SystemExit(main())
