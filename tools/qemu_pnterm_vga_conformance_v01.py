#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import socket
import subprocess
import time
from typing import Any

import qemu_pnstore_ide_conformance_v01 as pns
import qemu_pnterm_interactive_conformance_v01 as interactive

SCHEMA = "PNTERM_VGA_QEMU_CONFORMANCE_V0_1"
FIXTURE_HEX = Path("fixtures/BIOOS_DN36_DNCRYPT_BINARY_ENVELOPE_V0_1.hex")
EXPECTED_PAYLOAD_BYTES = 2552
EXPECTED_PAYLOAD_SHA256 = "3cda2a329301411a84f13b7f1163422ed79ef92355fd837394cec4d4b37a981e"
TRANSITION_DOMAIN = b"BIOOS/DNCRYPT/PNSTORE/TRANSITION/V0.1\x00"
ROM = Path("build/x86_64/pnstore_ide_qemu_test.bin")
BUILD_RECEIPT = Path("provenance/PNTERM_VGA_QEMU_BUILD_V0_1.json")
DISK = Path("build/x86_64/pnterm_vga_test.img")
OUT = Path("provenance/PNTERM_VGA_QEMU_CONFORMANCE_V0_1.json")
FIRST_SERIAL = Path("provenance/PNTERM_VGA_QEMU_FIRST_SERIAL.txt")
SECOND_SERIAL = Path("provenance/PNTERM_VGA_QEMU_SECOND_SERIAL.txt")
FIRST_DEBUG = Path("provenance/PNTERM_VGA_QEMU_FIRST_DEBUG.txt")
SECOND_DEBUG = Path("provenance/PNTERM_VGA_QEMU_SECOND_DEBUG.txt")
FIRST_VGA = Path("provenance/PNTERM_VGA_QEMU_FIRST_VRAM.bin")
SECOND_VGA = Path("provenance/PNTERM_VGA_QEMU_SECOND_VRAM.bin")

FIRST_SCRIPT = interactive.FIRST_SCRIPT
SECOND_SCRIPT = interactive.SECOND_SCRIPT
FIRST_REQUIRED = interactive.FIRST_REQUIRED_SERIAL
SECOND_REQUIRED = interactive.SECOND_REQUIRED_SERIAL
FIRST_DEBUG_ORDER = ["PNROM", "PN32", "PN64", "T36ID", "PNCORE.TERM", "PNDEV.NEW", "PNTERM.VGA", "PNTERM.READY"]
SECOND_DEBUG_ORDER = ["PNROM", "PN32", "PN64", "T36ID", "PNCORE.TERM", "PNDEV.RECOVER", "PNTERM.VGA", "PNTERM.READY"]
VGA_BYTES = 80 * 25 * 2
PROMPT = b"bioos> "


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def text_contains_in_order(text: str, expected: list[str]) -> bool:
    pos = 0
    for marker in expected:
        found = text.find(marker, pos)
        if found < 0:
            return False
        pos = found + len(marker)
    return True


def exact_subsequence(lines: list[str], expected: list[str]) -> bool:
    pos = 0
    for marker in expected:
        while pos < len(lines) and lines[pos] != marker:
            pos += 1
        if pos >= len(lines):
            return False
        pos += 1
    return True


def wait_for_socket(path: Path, deadline: float) -> None:
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.02)
    raise TimeoutError(f"QEMU monitor socket did not appear: {path}")


def hmp_command(sock_path: Path, command: str, timeout: float = 2.0) -> str:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect(str(sock_path))
        received = bytearray()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and b"(qemu)" not in received:
            try:
                part = s.recv(4096)
            except socket.timeout:
                break
            if not part:
                break
            received.extend(part)
        s.sendall(command.encode("utf-8") + b"\n")
        response = bytearray()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                part = s.recv(4096)
            except socket.timeout:
                break
            if not part:
                break
            response.extend(part)
            if b"(qemu)" in response:
                break
        return (bytes(received) + bytes(response)).decode("utf-8", errors="replace")


def read_available(fd: int, sink: bytearray) -> None:
    while True:
        readable, _, _ = select.select([fd], [], [], 0)
        if not readable:
            return
        try:
            chunk = os.read(fd, 4096)
        except BlockingIOError:
            return
        if not chunk:
            return
        sink.extend(chunk)


def session(
    *,
    qemu: Path,
    rom: Path,
    disk: Path,
    monitor_socket: Path,
    debug_path: Path,
    vga_dump: Path,
    script: bytes,
    required_serial: list[str],
    min_prompt_count: int,
    timeout: float,
) -> dict[str, Any]:
    for path in (monitor_socket, debug_path, vga_dump):
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    cmd = [
        str(qemu),
        "-machine", "pc,accel=tcg",
        "-cpu", "max",
        "-m", "16M",
        "-bios", str(rom),
        "-drive", f"file={disk},format=raw,if=ide,index=0,media=disk,cache=writeback",
        "-display", "none",
        "-serial", "stdio",
        "-monitor", f"unix:{monitor_socket},server=on,wait=off",
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
    if proc.stdin is None or proc.stdout is None:
        pns.kill_group(proc)
        raise RuntimeError("QEMU stdio pipes unavailable")
    out = bytearray()
    fd = proc.stdout.fileno()
    os.set_blocking(fd, False)
    started = time.monotonic()
    deadline = started + timeout
    prompt_seen = False
    script_sent = False
    serial_complete = False
    monitor_text = ""
    try:
        wait_for_socket(monitor_socket, deadline)
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                break
            readable, _, _ = select.select([fd], [], [], 0.05)
            if readable:
                try:
                    chunk = os.read(fd, 4096)
                except BlockingIOError:
                    chunk = b""
                if chunk:
                    out.extend(chunk)
            if not prompt_seen and PROMPT in out:
                prompt_seen = True
                proc.stdin.write(script)
                proc.stdin.flush()
                script_sent = True
            text = out.decode("utf-8", errors="replace")
            if script_sent and text_contains_in_order(text, required_serial) and text.count("bioos> ") >= min_prompt_count:
                serial_complete = True
                break
        if not prompt_seen:
            raise RuntimeError("guest prompt not observed before input")
        if not serial_complete:
            raise RuntimeError(f"required serial transcript not completed: {out.decode('utf-8', errors='replace')!r}")

        # Freeze a direct physical-memory witness while the guest remains live.
        vga_dump.parent.mkdir(parents=True, exist_ok=True)
        monitor_text = hmp_command(monitor_socket, f"pmemsave 0xb8000 {VGA_BYTES} {vga_dump.resolve()}")
        dump_deadline = time.monotonic() + 2.0
        while time.monotonic() < dump_deadline:
            if vga_dump.is_file() and vga_dump.stat().st_size == VGA_BYTES:
                break
            time.sleep(0.02)
        if not vga_dump.is_file() or vga_dump.stat().st_size != VGA_BYTES:
            raise RuntimeError(f"VGA pmemsave missing or wrong size; monitor={monitor_text!r}")
    finally:
        pns.kill_group(proc)
        try:
            proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            pns.kill_group(proc)
        os.set_blocking(fd, True)
        read_available(fd, out)

    stderr_b = b""
    if proc.stderr is not None:
        try:
            stderr_b = proc.stderr.read() or b""
        except Exception:
            stderr_b = b""
    serial_text = out.decode("utf-8", errors="replace")
    debug_text = debug_path.read_text(encoding="utf-8", errors="replace") if debug_path.exists() else ""
    return {
        "command": cmd,
        "prompt_seen_before_script": prompt_seen,
        "script_hex": script.hex(),
        "script_sha256": hashlib.sha256(script).hexdigest(),
        "serial_complete_before_dump": serial_complete,
        "serial_text": serial_text,
        "serial_sha256": hashlib.sha256(bytes(out)).hexdigest(),
        "debug_text": debug_text,
        "debug_lines": [line.strip() for line in debug_text.splitlines() if line.strip()],
        "debug_sha256": hashlib.sha256(debug_text.encode("utf-8")).hexdigest(),
        "monitor_response": monitor_text,
        "vga_dump_sha256": sha256_file(vga_dump),
        "stderr": stderr_b.decode("utf-8", errors="replace"),
        "returncode_after_capture": proc.returncode,
    }


def parse_vga(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if len(raw) != VGA_BYTES:
        raise ValueError(f"VGA dump size {len(raw)} != {VGA_BYTES}")
    rows: list[str] = []
    bad_attributes: list[int] = []
    for cell in range(80 * 25):
        if raw[cell * 2 + 1] != 0x07:
            bad_attributes.append(cell)
    for row in range(25):
        chars = []
        start = row * 80
        for col in range(80):
            ch = raw[(start + col) * 2]
            if ch == 0:
                ch = 0x20
            chars.append(chr(ch) if 0x20 <= ch <= 0x7e else "?")
        rows.append("".join(chars).rstrip())
    visible_text = "\n".join(rows)
    return {
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "rows": rows,
        "nonempty_rows": [row for row in rows if row],
        "all_attributes_07": not bad_attributes,
        "bad_attribute_cells": bad_attributes[:32],
        "visible_text": visible_text,
    }


def main() -> int:
    root = Path(".").resolve()
    rom = root / ROM
    build_receipt_path = root / BUILD_RECEIPT
    disk = root / DISK
    out_path = root / OUT
    first_serial_path = root / FIRST_SERIAL
    second_serial_path = root / SECOND_SERIAL
    first_debug_path = root / FIRST_DEBUG
    second_debug_path = root / SECOND_DEBUG
    first_vga_path = root / FIRST_VGA
    second_vga_path = root / SECOND_VGA
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "scope": "QEMU_UART16550_READONLY_PNTERM_PLUS_VGA80X25_EXACT_DNCRYPT_PNSTORE",
        "canon_allowed": False,
        "epistemic": "CHYBA",
        "physical_machine_tested": False,
        "physical_display_tested": False,
        "physical_power_loss_tested": False,
        "desktop_or_compositor_claim": False,
        "full_pnterm_v0_1_semantic_conformance_claim": False,
    }
    try:
        build = pns.verify_build_receipt(build_receipt_path, rom)
        if build.get("bridge_schema") != "PNTERM_VGA_QEMU_BUILD_V0_1":
            raise ValueError("unexpected VGA build bridge schema")
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

        first = session(
            qemu=qemu,
            rom=rom,
            disk=disk,
            monitor_socket=Path("/tmp/bioos_pnterm_vga_1.sock"),
            debug_path=first_debug_path,
            vga_dump=first_vga_path,
            script=FIRST_SCRIPT,
            required_serial=FIRST_REQUIRED,
            min_prompt_count=6,
            timeout=8.0,
        )
        first_serial_path.parent.mkdir(parents=True, exist_ok=True)
        first_serial_path.write_text(first["serial_text"], encoding="utf-8")
        if not exact_subsequence(first["debug_lines"], FIRST_DEBUG_ORDER):
            raise RuntimeError(f"first debug witness mismatch: {first['debug_lines']}")
        first_disk_sha = sha256_file(disk)
        if first_disk_sha == zero_sha:
            raise RuntimeError("first boot did not persist PNStore state")
        parsed_first = pns.parse_media(disk)
        if parsed_first["status"] != "PASS":
            raise RuntimeError(f"first PNStore parse failed: {parsed_first['checks']}")
        exact_first = interactive.verify_exact_payload(disk, fixture, transition_id)
        if not all(exact_first.values()):
            raise RuntimeError(f"first exact DNCrypt payload verification failed: {exact_first}")
        vga_first = parse_vga(first_vga_path)
        if not vga_first["all_attributes_07"]:
            raise RuntimeError(f"first VGA attribute drift: {vga_first['bad_attribute_cells']}")
        if not text_contains_in_order(vga_first["visible_text"], FIRST_REQUIRED):
            raise RuntimeError(f"first VGA visible transcript mismatch: {vga_first['nonempty_rows']}")

        second = session(
            qemu=qemu,
            rom=rom,
            disk=disk,
            monitor_socket=Path("/tmp/bioos_pnterm_vga_2.sock"),
            debug_path=second_debug_path,
            vga_dump=second_vga_path,
            script=SECOND_SCRIPT,
            required_serial=SECOND_REQUIRED,
            min_prompt_count=6,
            timeout=8.0,
        )
        second_serial_path.write_text(second["serial_text"], encoding="utf-8")
        if not exact_subsequence(second["debug_lines"], SECOND_DEBUG_ORDER):
            raise RuntimeError(f"second debug witness mismatch: {second['debug_lines']}")
        second_disk_sha = sha256_file(disk)
        if second_disk_sha != first_disk_sha:
            raise RuntimeError("read-only/rejected second VGA session mutated PNStore medium")
        parsed_second = pns.parse_media(disk)
        if parsed_second["status"] != "PASS":
            raise RuntimeError(f"second PNStore parse failed: {parsed_second['checks']}")
        exact_second = interactive.verify_exact_payload(disk, fixture, transition_id)
        if not all(exact_second.values()):
            raise RuntimeError(f"second exact DNCrypt payload verification failed: {exact_second}")
        vga_second = parse_vga(second_vga_path)
        if not vga_second["all_attributes_07"]:
            raise RuntimeError(f"second VGA attribute drift: {vga_second['bad_attribute_cells']}")
        if not text_contains_in_order(vga_second["visible_text"], SECOND_REQUIRED):
            raise RuntimeError(f"second VGA visible transcript mismatch: {vga_second['nonempty_rows']}")

        payload.update(
            status="PASS_QEMU_PNTERM_VGA80X25_READONLY_EXACT_DNCRYPT_PERSISTENCE",
            first_session=first,
            second_session=second,
            first_vga=vga_first,
            second_vga=vga_second,
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
            vga_text_base_hex="0x000b8000",
            vga_geometry="80x25",
            vga_cell_bytes=2,
            vga_attribute_hex="0x07",
            dncrypt_payload_sha256=EXPECTED_PAYLOAD_SHA256,
            dncrypt_payload_bytes=EXPECTED_PAYLOAD_BYTES,
            claim_boundary=(
                "Actual QEMU execution of a narrow ASCII read-only PNTERM serial vertical slice mirrored into VGA 80x25 "
                "text memory at physical 0xB8000, with direct pmemsave witnesses and exact pinned DNCrypt persistence "
                "through PNStore. This is not a framebuffer/compositor desktop, not full PNTERM UTF-8/token/envelope/PNCAP "
                "semantic conformance, not physical display/hardware or power-loss evidence, and not canon promotion."
            ),
        )
        payload["receipt_sha256"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        payload.update(status="FAIL_CLOSED", error_type=type(exc).__name__, error=str(exc))
        payload["receipt_sha256"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
