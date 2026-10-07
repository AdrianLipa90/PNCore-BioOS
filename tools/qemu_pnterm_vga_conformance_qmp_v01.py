#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import select
import socket
import subprocess
import time
from typing import Any

import qemu_pnstore_ide_conformance_v01 as pns
import qemu_pnterm_vga_conformance_v01 as base

PROMPT = b"bioos> "
VGA_PHYS_ADDR = 0x000B8000
VGA_BYTES = 80 * 25 * 2


def _qmp_read_response(stream, transcript: list[dict[str, Any]], timeout_deadline: float) -> dict[str, Any]:
    while time.monotonic() < timeout_deadline:
        raw = stream.readline()
        if not raw:
            raise RuntimeError("QMP socket closed before response")
        obj = json.loads(raw.decode("utf-8"))
        transcript.append(obj)
        if "return" in obj or "error" in obj:
            return obj
    raise TimeoutError("QMP response timeout")


def _qmp_send(stream, command: str, arguments: dict[str, Any] | None = None) -> None:
    payload: dict[str, Any] = {"execute": command}
    if arguments is not None:
        payload["arguments"] = arguments
    stream.write(json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n")
    stream.flush()


def qmp_pmemsave(sock_path: Path, filename: Path, timeout: float = 3.0) -> dict[str, Any]:
    transcript: list[dict[str, Any]] = []
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect(str(sock_path))
        stream = sock.makefile("rwb")

        greeting_raw = stream.readline()
        if not greeting_raw:
            raise RuntimeError("QMP greeting missing")
        greeting = json.loads(greeting_raw.decode("utf-8"))
        transcript.append(greeting)
        if "QMP" not in greeting:
            raise RuntimeError(f"unexpected QMP greeting: {greeting}")

        _qmp_send(stream, "qmp_capabilities")
        capabilities = _qmp_read_response(stream, transcript, time.monotonic() + timeout)
        if "error" in capabilities:
            raise RuntimeError(f"qmp_capabilities failed: {capabilities['error']}")

        _qmp_send(stream, "query-commands")
        commands = _qmp_read_response(stream, transcript, time.monotonic() + timeout)
        if "error" in commands:
            raise RuntimeError(f"query-commands failed: {commands['error']}")
        names = {
            entry.get("name")
            for entry in commands.get("return", [])
            if isinstance(entry, dict)
        }
        if "pmemsave" not in names:
            raise RuntimeError("QMP pmemsave command unavailable")

        _qmp_send(
            stream,
            "pmemsave",
            {
                "val": VGA_PHYS_ADDR,
                "size": VGA_BYTES,
                "filename": str(filename.resolve()),
            },
        )
        saved = _qmp_read_response(stream, transcript, time.monotonic() + timeout)
        if "error" in saved:
            raise RuntimeError(f"QMP pmemsave failed: {saved['error']}")
        if saved.get("return") != {}:
            raise RuntimeError(f"unexpected QMP pmemsave return: {saved}")

    return {
        "transport": "QMP_UNIX",
        "command": "pmemsave",
        "arguments": {
            "val": VGA_PHYS_ADDR,
            "val_hex": hex(VGA_PHYS_ADDR),
            "size": VGA_BYTES,
            "filename": str(filename.resolve()),
        },
        "capabilities_enabled": True,
        "pmemsave_advertised": True,
        "result": saved,
        "transcript": transcript,
    }


def session_qmp(
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
        "-qmp", f"unix:{monitor_socket},server=on,wait=off",
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
    deadline = time.monotonic() + timeout
    prompt_seen = False
    script_sent = False
    serial_complete = False
    qmp_evidence: dict[str, Any] | None = None

    try:
        base.wait_for_socket(monitor_socket, deadline)
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
            if (
                script_sent
                and base.text_contains_in_order(text, required_serial)
                and text.count("bioos> ") >= min_prompt_count
            ):
                serial_complete = True
                break

        if not prompt_seen:
            raise RuntimeError("guest prompt not observed before input")
        if not serial_complete:
            raise RuntimeError(
                f"required serial transcript not completed: {out.decode('utf-8', errors='replace')!r}"
            )

        vga_dump.parent.mkdir(parents=True, exist_ok=True)
        qmp_evidence = qmp_pmemsave(monitor_socket, vga_dump, timeout=3.0)
        dump_deadline = time.monotonic() + 2.0
        while time.monotonic() < dump_deadline:
            if vga_dump.is_file() and vga_dump.stat().st_size == VGA_BYTES:
                break
            time.sleep(0.02)
        if not vga_dump.is_file() or vga_dump.stat().st_size != VGA_BYTES:
            raise RuntimeError(
                f"VGA QMP pmemsave missing or wrong size; qmp={qmp_evidence!r}"
            )
    finally:
        pns.kill_group(proc)
        try:
            proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            pns.kill_group(proc)
        try:
            os.set_blocking(fd, True)
            base.read_available(fd, out)
        except OSError:
            pass

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
        "memory_evidence": qmp_evidence,
        "vga_dump_sha256": base.sha256_file(vga_dump),
        "stderr": stderr_b.decode("utf-8", errors="replace"),
        "returncode_after_capture": proc.returncode,
    }


def main() -> int:
    # QMP is used deliberately instead of HMP: QMP carries the filename as a
    # JSON string and the address/size as typed integers, avoiding HMP line
    # parser ambiguity while preserving the same physical pmemsave primitive.
    base.session = session_qmp
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
