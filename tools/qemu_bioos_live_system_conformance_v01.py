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

import qemu_pnstore_ide_conformance_v01 as store_base

SCHEMA = "BIOOS_LIVE_SYSTEM_QEMU_CONFORMANCE_V0_1"
BUILD_SCHEMA = "BIOOS_LIVE_SYSTEM_QEMU_BUILD_V0_1"
FIXTURE_HEX = Path("fixtures/BIOOS_DN36_DNCRYPT_BINARY_ENVELOPE_V0_1.hex")
EXPECTED_PAYLOAD_BYTES = 2552
EXPECTED_PAYLOAD_SHA256 = "3cda2a329301411a84f13b7f1163422ed79ef92355fd837394cec4d4b37a981e"
TRANSITION_DOMAIN = b"BIOOS/DNCRYPT/PNSTORE/TRANSITION/V0.1\x00"
FIRST_DEBUG = ["PNROM", "PN32", "PN64", "T36ID", "PNCORE.LIVE", "PNSTORE.NEW", "PNSTORE.OK", "UART.OK", "PNTERM.READY"]
RECOVER_DEBUG = ["PNROM", "PN32", "PN64", "T36ID", "PNCORE.LIVE", "PNSTORE.RECOVER", "PNSTORE.OK", "UART.OK", "PNTERM.READY"]
FAIL_MARKERS = {"I!", "X"}


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


def load_verified_receipt(path: Path, schema: str) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("receipt must be object")
    core = dict(data)
    recorded = core.pop("receipt_sha256", None)
    if recorded != hashlib.sha256(canonical_bytes(core)).hexdigest():
        raise ValueError("receipt digest mismatch")
    if data.get("schema") != schema:
        raise ValueError(f"receipt schema mismatch: {data.get('schema')}")
    return data


def command_value(cmd: list[str], flag: str) -> str:
    try:
        i = cmd.index(flag)
    except ValueError as exc:
        raise ValueError(f"missing QEMU flag: {flag}") from exc
    if i + 1 >= len(cmd):
        raise ValueError(f"missing QEMU value: {flag}")
    return cmd[i + 1]


def parse_drive(value: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for token in value.split(","):
        if "=" not in token:
            raise ValueError(f"unkeyed drive token: {token}")
        k, v = token.split("=", 1)
        if k in out:
            raise ValueError(f"duplicate drive token: {k}")
        out[k] = v
    return out


def validate_command(cmd: list[str], hard: dict[str, Any]) -> dict[str, bool]:
    drive = parse_drive(command_value(cmd, "-drive"))
    expected_drive = dict(hard["drive"])
    checks = {
        "machine": command_value(cmd, "-machine") == hard["machine"],
        "cpu": command_value(cmd, "-cpu") == hard["cpu"],
        "memory": command_value(cmd, "-m") == hard["memory"],
        "bios": Path(command_value(cmd, "-bios")).name == hard["bios_basename"],
        "drive_file_present": bool(drive.get("file")),
        "drive_semantics": {k: drive.get(k) for k in expected_drive} == expected_drive,
        "drive_no_unknown_tokens": set(drive) == set(expected_drive) | {"file"},
        "display": command_value(cmd, "-display") == hard["display"],
        "serial": command_value(cmd, "-serial") == hard["serial"],
        "monitor": command_value(cmd, "-monitor") == hard["monitor"],
        "debugcon_file": command_value(cmd, "-debugcon").startswith("file:"),
        "debugcon_iobase": command_value(cmd, "-global") == f"isa-debugcon.iobase={hard['debugcon_iobase']}",
        "no_reboot": "-no-reboot" in cmd and hard["no_reboot"] is True,
        "no_shutdown": "-no-shutdown" in cmd and hard["no_shutdown"] is True,
    }
    failed = [k for k, v in checks.items() if not v]
    if failed:
        raise ValueError(f"live-system QEMU semantic drift: {failed}")
    return checks


def run_boot(qemu: Path, rom: Path, disk: Path, hard: dict[str, Any], input_bytes: bytes, expected_debug: list[str], required_serial: list[bytes], forbidden_serial: list[bytes] | None = None) -> dict[str, Any]:
    forbidden_serial = forbidden_serial or []
    with tempfile.TemporaryDirectory(prefix="bioos-live-") as td:
        debug_path = Path(td) / "debugcon.log"
        cmd = [
            str(qemu),
            "-machine", hard["machine"],
            "-cpu", hard["cpu"],
            "-m", hard["memory"],
            "-bios", str(rom),
            "-drive", f"file={disk},format={hard['drive']['format']},if={hard['drive']['if']},index={hard['drive']['index']},media={hard['drive']['media']},cache={hard['drive']['cache']}",
            "-display", hard["display"],
            "-serial", hard["serial"],
            "-monitor", hard["monitor"],
            "-debugcon", f"file:{debug_path}",
            "-global", f"isa-debugcon.iobase={hard['debugcon_iobase']}",
            "-no-reboot",
            "-no-shutdown",
        ]
        command_checks = validate_command(cmd, hard)
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        if proc.stdin is None:
            kill_group(proc)
            raise RuntimeError("QEMU stdin unavailable")
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
    required = {x.decode("utf-8", errors="replace"): x in stdout for x in required_serial}
    forbidden = {x.decode("utf-8", errors="replace"): x not in stdout for x in forbidden_serial}
    debug_ok = exact_subsequence(debug_lines, expected_debug) and not any(line in FAIL_MARKERS for line in debug_lines)
    passed = timed_out and debug_ok and all(required.values()) and all(forbidden.values())
    return {
        "status": "PASS" if passed else "FAIL",
        "input_hex": input_bytes.hex(),
        "command": cmd,
        "command_semantic_checks": command_checks,
        "timed_out_live_system_expected": timed_out,
        "returncode_after_capture": proc.returncode,
        "serial_output": stdout.decode("utf-8", errors="replace"),
        "stderr": stderr.decode("utf-8", errors="replace"),
        "debug_lines": debug_lines,
        "debug_sequence_pass": debug_ok,
        "required_serial_checks": required,
        "forbidden_serial_checks": forbidden,
    }


def verify_exact_disk(disk: Path, payload: bytes, transition_id: bytes, object_digest: bytes) -> dict[str, Any]:
    raw = disk.read_bytes()
    if len(raw) != 65536:
        raise ValueError("PNStore disk size mismatch")
    store_base.EXPECTED_TRANSITION_ID = transition_id
    parsed = store_base.parse_media(disk)
    if parsed.get("status") != "PASS":
        raise ValueError(f"PNStore parser failed: {parsed.get('checks')}")
    extent = 4096
    payload_len = int.from_bytes(raw[extent + 88:extent + 92], "little")
    stored_payload = raw[extent + 96:extent + 96 + payload_len]
    exact = {
        "payload_length": payload_len == len(payload),
        "payload_bytes": stored_payload == payload,
        "payload_sha256": hashlib.sha256(stored_payload).hexdigest() == EXPECTED_PAYLOAD_SHA256,
        "payload_magic": stored_payload[:4] == b"DNCB",
        "transition_id": raw[extent + 24:extent + 56] == transition_id,
        "object_digest": raw[extent + 56:extent + 88] == object_digest,
    }
    if not all(exact.values()):
        raise ValueError(f"exact persistent DNCrypt binding failed: {exact}")
    return {
        "parser": parsed,
        "exact_checks": exact,
        "disk_sha256": hashlib.sha256(raw).hexdigest(),
        "payload_bytes": payload_len,
        "payload_sha256": hashlib.sha256(stored_payload).hexdigest(),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Integrated PNStore + PNTERM BioOS QEMU live-system conformance")
    ap.add_argument("--spec", type=Path, default=Path("spec/EMULATION_REFERENCE_LIVE_SYSTEM_SPEC_V0_1.json"))
    ap.add_argument("--rom", type=Path, default=Path("build/x86_64/bioos_live_system_qemu_test.bin"))
    ap.add_argument("--build-receipt", type=Path, default=Path("provenance/BIOOS_LIVE_SYSTEM_QEMU_BUILD_V0_1.json"))
    ap.add_argument("--disk", type=Path, default=Path("build/x86_64/bioos_live_system.img"))
    ap.add_argument("--qemu", default="qemu-system-x86_64")
    ap.add_argument("--expected-qemu-sha256", default=None)
    ap.add_argument("--out", type=Path, default=Path("provenance/BIOOS_LIVE_SYSTEM_QEMU_CONFORMANCE_V0_1.json"))
    args = ap.parse_args()

    payload_out: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "FAIL_CLOSED",
        "canon_allowed": False,
        "physical_machine_tested": False,
        "physical_power_loss_tested": False,
        "epistemic": "CHYBA",
    }
    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
        if spec.get("schema") != "BIOOS_EMULATION_REFERENCE_LIVE_SYSTEM_SPEC_V0_1":
            raise ValueError("unexpected live-system reference spec schema")
        hard = spec.get("hard_pins")
        if not isinstance(hard, dict):
            raise ValueError("live-system hard_pins missing")
        if not math.isfinite(float(hard["observation_timeout_seconds"])) or float(hard["observation_timeout_seconds"]) <= 0:
            raise ValueError("invalid observation timeout")

        build = load_verified_receipt(args.build_receipt, BUILD_SCHEMA)
        if build.get("status") != "PASS_HOST_BUILD" or build.get("canon_allowed") is not False:
            raise ValueError("live-system build receipt not admissible")
        if build.get("console", {}).get("write_commands") != 0 or build.get("console", {}).get("arbitrary_shell") is not False:
            raise ValueError("live-system console authority boundary open")

        rom_raw = args.rom.read_bytes()
        if len(rom_raw) != 65536 or build.get("rom_sha256") != hashlib.sha256(rom_raw).hexdigest():
            raise ValueError("live-system ROM identity mismatch")

        fixture = bytes.fromhex(FIXTURE_HEX.read_text(encoding="ascii").strip())
        if len(fixture) != EXPECTED_PAYLOAD_BYTES or hashlib.sha256(fixture).hexdigest() != EXPECTED_PAYLOAD_SHA256:
            raise ValueError("DNCrypt fixture drift")
        object_digest = hashlib.sha256(fixture).digest()
        transition_id = hashlib.sha256(TRANSITION_DOMAIN + object_digest).digest()
        bfix = build.get("persistent_fixture", {})
        if bfix.get("sha256") != EXPECTED_PAYLOAD_SHA256 or bfix.get("transition_id_hex") != transition_id.hex():
            raise ValueError("build receipt persistent fixture binding mismatch")

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

        args.disk.parent.mkdir(parents=True, exist_ok=True)
        args.disk.write_bytes(bytes(65536))
        zero_sha = sha256_file(args.disk)

        common = [b"BioOS Live QEMU v0.1\r\n", b"bioos> "]
        first = run_boot(
            qemu, args.rom, args.disk, hard, b"store.show\n", FIRST_DEBUG,
            common + [b"store=READY generation=1 boot=NEW payload=DNCB persisted=true\r\n"],
        )
        if first["status"] != "PASS":
            raise RuntimeError(f"first live-system boot failed: {first['debug_lines']}")
        first_disk = verify_exact_disk(args.disk, fixture, transition_id, object_digest)
        if first_disk["disk_sha256"] == zero_sha:
            raise RuntimeError("first live-system boot did not persist state")

        second = run_boot(
            qemu, args.rom, args.disk, hard, b"store.show\r\n", RECOVER_DEBUG,
            common + [b"store=READY generation=1 boot=RECOVER payload=DNCB persisted=true\r\n"],
        )
        if second["status"] != "PASS":
            raise RuntimeError(f"second live-system boot failed: {second['debug_lines']}")
        second_disk = verify_exact_disk(args.disk, fixture, transition_id, object_digest)
        if second_disk["disk_sha256"] != first_disk["disk_sha256"]:
            raise RuntimeError("second live-system boot mutated already-committed medium")

        third = run_boot(
            qemu, args.rom, args.disk, hard, b"shutdown\n", RECOVER_DEBUG,
            common + [b"ERR UNKNOWN\r\n"],
            forbidden_serial=[b"store=READY generation=1 boot=NEW payload=DNCB persisted=true\r\n"],
        )
        if third["status"] != "PASS":
            raise RuntimeError(f"unknown-command live-system boot failed: {third['debug_lines']}")
        third_sha = sha256_file(args.disk)
        if third_sha != first_disk["disk_sha256"]:
            raise RuntimeError("read-only unknown command mutated persistent medium")

        payload_out.update(
            status="PASS_QEMU_BIOOS_PERSISTENT_INTERACTIVE_VERTICAL_SLICE",
            build_receipt_sha256=build["receipt_sha256"],
            spec_sha256=hashlib.sha256(canonical_bytes(spec)).hexdigest(),
            rom_sha256=hashlib.sha256(rom_raw).hexdigest(),
            first_boot=first,
            second_boot=second,
            unknown_command_boot=third,
            media_after_first=first_disk,
            media_after_second=second_disk,
            second_boot_medium_unchanged=True,
            unknown_command_medium_unchanged=True,
            observed_qemu={
                "version": version_line,
                "binary_path": str(qemu),
                "binary_sha256": qemu_sha,
                "binary_pinned": bool(args.expected_qemu_sha256),
            },
            authority_boundary=spec.get("authority_boundary"),
            claim_boundary=(
                "QEMU vertical-slice evidence that one pinned DNCrypt envelope is initialized once through PNStore ATA-PIO FLUSH ordering, "
                "recovered unchanged by a second independent QEMU process, and exposed through a bounded read-only PNTERM store.show command. "
                "An unknown shell-like command is rejected without mutating the medium. Not physical power-loss durability, bare-metal execution, "
                "a complete OS service model, or canon."
            ),
        )
        code = 0
    except Exception as exc:
        payload_out.update(error_type=type(exc).__name__, error=str(exc))
        code = 2

    core = dict(payload_out)
    core.pop("receipt_sha256", None)
    payload_out["receipt_sha256"] = hashlib.sha256(canonical_bytes(core)).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload_out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload_out, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
