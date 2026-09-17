#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

import qemu_pnstore_ide_conformance_v01 as pns

SCHEMA = "PNTERM_INTERACTIVE_QEMU_CONFORMANCE_V0_1"
FIXTURE_HEX = Path("fixtures/BIOOS_DN36_DNCRYPT_BINARY_ENVELOPE_V0_1.hex")
EXPECTED_PAYLOAD_BYTES = 2552
EXPECTED_PAYLOAD_SHA256 = "3cda2a329301411a84f13b7f1163422ed79ef92355fd837394cec4d4b37a981e"
TRANSITION_DOMAIN = b"BIOOS/DNCRYPT/PNSTORE/TRANSITION/V0.1\x00"
ROM = Path("build/x86_64/pnstore_ide_qemu_test.bin")
BUILD_RECEIPT = Path("provenance/PNTERM_INTERACTIVE_QEMU_BUILD_V0_1.json")
DISK = Path("build/x86_64/pnterm_interactive_test.img")
OUT = Path("provenance/PNTERM_INTERACTIVE_QEMU_CONFORMANCE_V0_1.json")
FIRST_SERIAL = Path("provenance/PNTERM_INTERACTIVE_QEMU_FIRST_SERIAL.txt")
SECOND_SERIAL = Path("provenance/PNTERM_INTERACTIVE_QEMU_SECOND_SERIAL.txt")
FIRST_DEBUG = Path("provenance/PNTERM_INTERACTIVE_QEMU_FIRST_DEBUG.txt")
SECOND_DEBUG = Path("provenance/PNTERM_INTERACTIVE_QEMU_SECOND_DEBUG.txt")

FIRST_SCRIPT = b"help\rstatus\rstore.show\rterminal.selftest\recho vector hello\r"
SECOND_SCRIPT = b"store.write\r\x1b\rstore.show\rstatus\r"
FIRST_REQUIRED_SERIAL = [
    "BioOS PNTERM QEMU v0.1",
    "READONLY ASCII VERTICAL-SLICE / no shell / no write commands",
    "CMDS help status store.show terminal.selftest echo",
    "STATUS PASS READONLY UART16550 PNSTORE_DNCRYPT=EXACT",
    "STORE GEN=1 HEAD=A PAYLOAD=2552 MAGIC=DNCB EXACT=1",
    "SELFTEST PASS UART16550 PNSTORE EXACT_DNCRYPT",
    "ECHO vector hello",
]
SECOND_REQUIRED_SERIAL = [
    "ERR UNKNOWN_COMMAND",
    "ERR CONTROL_CHAR_REJECTED",
    "STORE GEN=1 HEAD=A PAYLOAD=2552 MAGIC=DNCB EXACT=1",
    "STATUS PASS READONLY UART16550 PNSTORE_DNCRYPT=EXACT",
]
FIRST_DEBUG_ORDER = ["PNROM", "PN32", "PN64", "T36ID", "PNCORE.TERM", "PNDEV.NEW", "PNTERM.READY"]
SECOND_DEBUG_ORDER = ["PNROM", "PN32", "PN64", "T36ID", "PNCORE.TERM", "PNDEV.RECOVER", "PNTERM.READY"]


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


def text_contains_in_order(text: str, expected: list[str]) -> bool:
    pos = 0
    for marker in expected:
        found = text.find(marker, pos)
        if found < 0:
            return False
        pos = found + len(marker)
    return True


def run_session(qemu: Path, rom: Path, disk: Path, debug_path: Path, script: bytes, timeout: float) -> dict[str, Any]:
    if debug_path.exists():
        debug_path.unlink()
    cmd = [
        str(qemu),
        "-machine", "pc,accel=tcg",
        "-cpu", "max",
        "-m", "16M",
        "-bios", str(rom),
        "-drive", f"file={disk},format=raw,if=ide,index=0,media=disk,cache=writeback",
        "-display", "none",
        "-monitor", "none",
        "-serial", "stdio",
        "-debugcon", f"file:{debug_path}",
        "-global", "isa-debugcon.iobase=0xe9",
        "-no-reboot",
        "-no-shutdown",
    ]
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    timed_out = False
    try:
        stdout_b, stderr_b = proc.communicate(input=script, timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        pns.kill_group(proc)
        stdout_b, stderr_b = proc.communicate(timeout=2.0)
    serial_text = stdout_b.decode("utf-8", errors="replace")
    stderr_text = stderr_b.decode("utf-8", errors="replace")
    debug_text = debug_path.read_text(encoding="utf-8", errors="replace") if debug_path.exists() else ""
    debug_lines = [line.strip() for line in debug_text.splitlines() if line.strip()]
    return {
        "command": cmd,
        "script_hex": script.hex(),
        "script_sha256": hashlib.sha256(script).hexdigest(),
        "timed_out_after_interactive_loop_expected": timed_out,
        "returncode_after_capture": proc.returncode,
        "serial_text": serial_text,
        "serial_sha256": hashlib.sha256(stdout_b).hexdigest(),
        "stderr": stderr_text,
        "debug_text": debug_text,
        "debug_lines": debug_lines,
        "debug_sha256": hashlib.sha256(debug_text.encode("utf-8")).hexdigest(),
    }


def verify_exact_payload(disk: Path, payload: bytes, transition_id: bytes) -> dict[str, bool]:
    raw = disk.read_bytes()
    if len(raw) != 65536:
        raise ValueError("PNStore disk geometry mismatch")
    extent = 4096
    head = 512
    stored_len = int.from_bytes(raw[extent + 88:extent + 92], "little")
    stored_payload = raw[extent + 96:extent + 96 + stored_len]
    object_digest = hashlib.sha256(payload).digest()
    return {
        "payload_length_exact": stored_len == len(payload),
        "payload_bytes_exact": stored_payload == payload,
        "payload_sha256_exact": hashlib.sha256(stored_payload).hexdigest() == hashlib.sha256(payload).hexdigest(),
        "payload_magic_dncb": stored_payload[:4] == b"DNCB",
        "extent_transition_exact": raw[extent + 24:extent + 56] == transition_id,
        "extent_object_digest_exact": raw[extent + 56:extent + 88] == object_digest,
        "head_transition_exact": raw[head + 32:head + 64] == transition_id,
        "head_object_digest_exact": raw[head + 64:head + 96] == object_digest,
    }


def main() -> int:
    root = Path(".").resolve()
    rom = root / ROM
    build_receipt_path = root / BUILD_RECEIPT
    disk = root / DISK
    out = root / OUT
    first_serial_path = root / FIRST_SERIAL
    second_serial_path = root / SECOND_SERIAL
    first_debug_path = root / FIRST_DEBUG
    second_debug_path = root / SECOND_DEBUG
    timeout = 5.0

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "scope": "QEMU_UART16550_INTERACTIVE_READONLY_PNTERM_WITH_EXACT_DNCRYPT_PNSTORE",
        "canon_allowed": False,
        "epistemic": "CHYBA",
        "physical_machine_tested": False,
        "physical_power_loss_tested": False,
        "full_pnterm_v0_1_semantic_conformance_claim": False,
    }
    try:
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and > 0")
        if not rom.is_file() or not build_receipt_path.is_file():
            raise FileNotFoundError("interactive PNTERM ROM or build receipt missing")

        build = pns.verify_build_receipt(build_receipt_path, rom)
        if build.get("bridge_schema") != "PNTERM_INTERACTIVE_QEMU_BUILD_V0_1":
            raise ValueError("unexpected interactive build bridge schema")
        payload["build_receipt_sha256"] = build["receipt_sha256"]
        payload["rom_sha256"] = build["rom_sha256"]

        fixture = bytes.fromhex((root / FIXTURE_HEX).read_text(encoding="ascii").strip())
        if len(fixture) != EXPECTED_PAYLOAD_BYTES or hashlib.sha256(fixture).hexdigest() != EXPECTED_PAYLOAD_SHA256:
            raise ValueError("pinned DNCrypt fixture mismatch")
        transition_id = hashlib.sha256(TRANSITION_DOMAIN + hashlib.sha256(fixture).digest()).digest()
        pns.EXPECTED_TRANSITION_ID = transition_id

        qemu_raw = shutil.which("qemu-system-x86_64")
        if not qemu_raw:
            raise FileNotFoundError("QEMU executable not found")
        qemu = Path(qemu_raw).resolve(strict=True)
        qemu_sha = sha256_file(qemu)
        version = subprocess.run([str(qemu), "--version"], text=True, capture_output=True, check=False, timeout=5.0)
        version_text = version.stdout or version.stderr
        version_line = version_text.splitlines()[0] if version_text else ""
        if version.returncode != 0 or not version_line.startswith("QEMU emulator version "):
            raise RuntimeError("QEMU version probe failed")
        payload["qemu_binary"] = str(qemu)
        payload["qemu_binary_sha256"] = qemu_sha
        payload["qemu_binary_pinned"] = False
        payload["qemu_version"] = version_line

        disk.parent.mkdir(parents=True, exist_ok=True)
        disk.write_bytes(bytes(65536))
        zero_sha = sha256_file(disk)

        first = run_session(qemu, rom, disk, first_debug_path, FIRST_SCRIPT, timeout)
        first_serial_path.parent.mkdir(parents=True, exist_ok=True)
        first_serial_path.write_text(first["serial_text"], encoding="utf-8")
        if not first["timed_out_after_interactive_loop_expected"]:
            raise RuntimeError("first interactive QEMU session exited unexpectedly")
        if not exact_subsequence(first["debug_lines"], FIRST_DEBUG_ORDER):
            raise RuntimeError(f"first debug witness mismatch: {first['debug_lines']}")
        if not text_contains_in_order(first["serial_text"], FIRST_REQUIRED_SERIAL):
            raise RuntimeError(f"first serial witness missing required response: {first['serial_text']!r}")
        first_disk_sha = sha256_file(disk)
        if first_disk_sha == zero_sha:
            raise RuntimeError("first boot did not persist PNStore state")
        parsed_first = pns.parse_media(disk)
        if parsed_first["status"] != "PASS":
            raise RuntimeError(f"first PNStore parse failed: {parsed_first['checks']}")
        exact_first = verify_exact_payload(disk, fixture, transition_id)
        if not all(exact_first.values()):
            raise RuntimeError(f"first exact DNCrypt payload verification failed: {exact_first}")

        # Second independent QEMU process carries rejected write-like/control input.
        # The already committed medium must remain byte-identical.
        second = run_session(qemu, rom, disk, second_debug_path, SECOND_SCRIPT, timeout)
        second_serial_path.write_text(second["serial_text"], encoding="utf-8")
        if not second["timed_out_after_interactive_loop_expected"]:
            raise RuntimeError("second interactive QEMU session exited unexpectedly")
        if not exact_subsequence(second["debug_lines"], SECOND_DEBUG_ORDER):
            raise RuntimeError(f"second debug witness mismatch: {second['debug_lines']}")
        if not text_contains_in_order(second["serial_text"], SECOND_REQUIRED_SERIAL):
            raise RuntimeError(f"second serial witness missing fail-closed/read-only response: {second['serial_text']!r}")
        second_disk_sha = sha256_file(disk)
        if second_disk_sha != first_disk_sha:
            raise RuntimeError("read-only/rejected second session mutated PNStore medium")
        parsed_second = pns.parse_media(disk)
        if parsed_second["status"] != "PASS":
            raise RuntimeError(f"second PNStore parse failed: {parsed_second['checks']}")
        exact_second = verify_exact_payload(disk, fixture, transition_id)
        if not all(exact_second.values()):
            raise RuntimeError(f"second exact DNCrypt payload verification failed: {exact_second}")

        payload.update(
            status="PASS_QEMU_INTERACTIVE_PNTERM_READONLY_EXACT_DNCRYPT_PERSISTENCE",
            first_session=first,
            second_session=second,
            first_required_serial=FIRST_REQUIRED_SERIAL,
            second_required_serial=SECOND_REQUIRED_SERIAL,
            first_debug_order=FIRST_DEBUG_ORDER,
            second_debug_order=SECOND_DEBUG_ORDER,
            media_after_first=parsed_first,
            media_after_second=parsed_second,
            exact_payload_after_first=exact_first,
            exact_payload_after_second=exact_second,
            disk_sha256_after_first=first_disk_sha,
            disk_sha256_after_second=second_disk_sha,
            second_session_medium_unchanged=True,
            invalid_write_like_command_rejected=True,
            control_character_rejected=True,
            default_write_commands=0,
            dncrypt_payload_sha256=EXPECTED_PAYLOAD_SHA256,
            dncrypt_payload_bytes=EXPECTED_PAYLOAD_BYTES,
            claim_boundary=(
                "Actual QEMU execution of a narrow ASCII read-only PNTERM serial vertical slice over the existing UART16550 "
                "adapter, with exact pinned DNCrypt binary-envelope persistence through PNStore and a byte-identical second "
                "session after rejected write-like/control input. This is not full PNTERM UTF-8/token/envelope/PNCAP semantic "
                "conformance, not physical hardware or power-loss durability, and not canon promotion."
            ),
        )
        payload["receipt_sha256"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        payload.update(status="FAIL_CLOSED", error_type=type(exc).__name__, error=str(exc))
        payload["receipt_sha256"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
