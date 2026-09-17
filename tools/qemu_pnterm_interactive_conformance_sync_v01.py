#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import select
import subprocess
import time
from typing import Any

import qemu_pnstore_ide_conformance_v01 as pns
import qemu_pnterm_interactive_conformance_v01 as base

PROMPT = b"bioos> "


def run_session_synchronized(
    qemu: Path,
    rom: Path,
    disk: Path,
    debug_path: Path,
    script: bytes,
    timeout: float,
) -> dict[str, Any]:
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
    if proc.stdout is None or proc.stdin is None:
        pns.kill_group(proc)
        raise RuntimeError("QEMU stdio pipes unavailable")

    prefix = bytearray()
    fd = proc.stdout.fileno()
    os.set_blocking(fd, False)
    prompt_deadline = time.monotonic() + min(timeout, 4.0)
    prompt_seen = False
    while time.monotonic() < prompt_deadline:
        if proc.poll() is not None:
            break
        readable, _, _ = select.select([fd], [], [], 0.05)
        if not readable:
            continue
        chunk = os.read(fd, 4096)
        if not chunk:
            continue
        prefix.extend(chunk)
        if PROMPT in prefix:
            prompt_seen = True
            break
    os.set_blocking(fd, True)

    if prompt_seen:
        proc.stdin.write(script)
        proc.stdin.flush()

    timed_out = False
    try:
        stdout_tail, stderr_b = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        pns.kill_group(proc)
        stdout_tail, stderr_b = proc.communicate(timeout=2.0)

    stdout_b = bytes(prefix) + stdout_tail
    serial_text = stdout_b.decode("utf-8", errors="replace")
    stderr_text = stderr_b.decode("utf-8", errors="replace")
    debug_text = debug_path.read_text(encoding="utf-8", errors="replace") if debug_path.exists() else ""
    debug_lines = [line.strip() for line in debug_text.splitlines() if line.strip()]
    return {
        "command": cmd,
        "prompt_seen_before_script": prompt_seen,
        "prompt_prefix_sha256": hashlib.sha256(bytes(prefix)).hexdigest(),
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


def main() -> int:
    base.run_session = run_session_synchronized
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
