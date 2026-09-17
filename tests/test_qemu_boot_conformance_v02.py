from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parents[0] / "tools" / "qemu_boot_conformance_v02.py"
EXPECTED = ["PNROM", "PN32", "PN64", "PNCORE", "PNR.OK", "SIGMA0", "SCHED"]


def _make_fixture(tmp_path: Path, *, overrides: dict[str, str] | None = None, omit: set[str] | None = None) -> Path:
    root = tmp_path / "repo"
    (root / "build").mkdir(parents=True)
    (root / "realizations/x86_64").mkdir(parents=True)
    rom = root / "build/pnrom_v0_2.bin"
    rom.write_bytes(bytes(65536))
    fields = {
        "ROM_SHA256": hashlib.sha256(rom.read_bytes()).hexdigest(),
        "ROM_SIZE_BYTES": "65536",
        "RESET_VECTOR": "0x000ffff0",
        "REALIZATION_ID": "pnr:realization:sha256:" + "1" * 64,
        "CANON_ALLOWED": "FALSE",
    }
    if overrides:
        fields.update(overrides)
    omit = omit or set()
    lines = ["PNR 1"] + [f"{k} {v}" for k, v in fields.items() if k not in omit] + ["END PNR", ""]
    (root / "realizations/x86_64/GENESIS_X86_64_V0_1.pnr").write_text("\n".join(lines), encoding="utf-8")
    return root


def _make_qemu(tmp_path: Path, body: str) -> Path:
    qemu = tmp_path / "fake_qemu.py"
    qemu.write_text("#!/usr/bin/env python3\n" + body, encoding="utf-8")
    qemu.chmod(0o755)
    return qemu


def _run(root: Path, qemu: Path, *extra: str, timeout: str = "1.5") -> tuple[subprocess.CompletedProcess[str], dict]:
    cmd = [
        sys.executable,
        str(TOOL),
        str(root),
        "--qemu", str(qemu),
        "--timeout", timeout,
        "--probe-timeout", "5.0",
        "--drain-timeout", "1.0",
        *extra,
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=10.0, check=False)
    assert "Traceback" not in proc.stdout
    assert "Traceback" not in proc.stderr
    data = json.loads(proc.stdout)
    return proc, data


def _qemu_exact(*, sleep_after: bool, failure: bool = False) -> str:
    markers = "\n".join(EXPECTED + (["X"] if failure else []))
    tail = "time.sleep(30)" if sleep_after else "pass"
    return (
        "import sys, time\n"
        "if '--version' in sys.argv:\n"
        "    print('QEMU emulator version 99.0.0')\n"
        "else:\n"
        f"    print({markers!r}, flush=True)\n"
        f"    {tail}\n"
    )


def test_exact_markers_plus_nonexit_pass(tmp_path: Path):
    root = _make_fixture(tmp_path)
    qemu = _make_qemu(tmp_path, _qemu_exact(sleep_after=True))
    proc, data = _run(root, qemu)
    assert proc.returncode == 0
    assert data["expected_sequence_present"] is True
    assert data["failure_marker_present"] is False
    assert data["process_alive_at_observation_timeout"] is True
    assert data["status"] == "PASS_QEMU_BOOT_CONFORMANCE_UNPINNED_BINARY"


def test_substring_markers_are_not_witnesses(tmp_path: Path):
    root = _make_fixture(tmp_path)
    junk = "\n".join(f"xx{x}xx" for x in EXPECTED)
    body = (
        "import sys, time\n"
        "if '--version' in sys.argv:\n"
        "    print('QEMU emulator version 99.0.0')\n"
        "else:\n"
        f"    print({junk!r}, flush=True)\n"
        "    time.sleep(30)\n"
    )
    qemu = _make_qemu(tmp_path, body)
    proc, data = _run(root, qemu)
    assert proc.returncode == 1
    assert data["expected_sequence_present"] is False
    assert data["reason"] == "EXPECTED_DEBUG_SEQUENCE_MISSING"


def test_exact_markers_with_early_exit_fail(tmp_path: Path):
    root = _make_fixture(tmp_path)
    qemu = _make_qemu(tmp_path, _qemu_exact(sleep_after=False))
    proc, data = _run(root, qemu)
    assert proc.returncode == 1
    assert data["expected_sequence_present"] is True
    assert data["process_alive_at_observation_timeout"] is False
    assert data["reason"] == "QEMU_EXITED_BEFORE_EXPECTED_POST_SCHED_NONEXIT"


def test_failure_marker_fails_even_with_full_sequence(tmp_path: Path):
    root = _make_fixture(tmp_path)
    qemu = _make_qemu(tmp_path, _qemu_exact(sleep_after=True, failure=True))
    proc, data = _run(root, qemu)
    assert proc.returncode == 1
    assert data["failure_marker_present"] is True
    assert data["reason"] == "PNCORE_FAILURE_MARKER"


def test_rom_hash_mismatch_fails_before_qemu(tmp_path: Path):
    root = _make_fixture(tmp_path, overrides={"ROM_SHA256": "0" * 64})
    qemu = _make_qemu(tmp_path, _qemu_exact(sleep_after=True))
    proc, data = _run(root, qemu)
    assert proc.returncode == 2
    assert data["reason"] == "ROM_SHA_MISMATCH"
    assert "qemu_version" not in data


def test_pnr_contract_size_mismatch_fails(tmp_path: Path):
    root = _make_fixture(tmp_path, overrides={"ROM_SIZE_BYTES": "32768"})
    qemu = _make_qemu(tmp_path, _qemu_exact(sleep_after=True))
    proc, data = _run(root, qemu)
    assert proc.returncode == 2
    assert data["reason"] == "PNR_ROM_SIZE_CONTRACT_MISMATCH"


def test_reset_vector_mismatch_fails(tmp_path: Path):
    root = _make_fixture(tmp_path, overrides={"RESET_VECTOR": "0x0000fff0"})
    qemu = _make_qemu(tmp_path, _qemu_exact(sleep_after=True))
    proc, data = _run(root, qemu)
    assert proc.returncode == 2
    assert data["reason"] == "PNR_RESET_VECTOR_MISMATCH"


def test_missing_required_pnr_field_fails(tmp_path: Path):
    root = _make_fixture(tmp_path, omit={"REALIZATION_ID"})
    qemu = _make_qemu(tmp_path, _qemu_exact(sleep_after=True))
    proc, data = _run(root, qemu)
    assert proc.returncode == 2
    assert data["reason"] == "PNR_REQUIRED_FIELD_MISSING"
    assert "REALIZATION_ID" in data["missing_pnr_fields"]


def test_duplicate_pnr_field_fails_closed(tmp_path: Path):
    root = _make_fixture(tmp_path)
    pnr = root / "realizations/x86_64/GENESIS_X86_64_V0_1.pnr"
    pnr.write_text(pnr.read_text(encoding="utf-8").replace("END PNR", "CANON_ALLOWED FALSE\nEND PNR"), encoding="utf-8")
    qemu = _make_qemu(tmp_path, _qemu_exact(sleep_after=True))
    proc, data = _run(root, qemu)
    assert proc.returncode == 2
    assert data["reason"] == "PNR_PARSE_OR_READ_ERROR"


def test_qemu_version_probe_timeout_is_structured_fail_closed(tmp_path: Path):
    root = _make_fixture(tmp_path)
    body = (
        "import sys, time\n"
        "if '--version' in sys.argv:\n"
        "    time.sleep(30)\n"
        "else:\n"
        "    pass\n"
    )
    qemu = _make_qemu(tmp_path, body)
    cmd = [
        sys.executable, str(TOOL), str(root), "--qemu", str(qemu),
        "--timeout", "0.2", "--probe-timeout", "0.1", "--drain-timeout", "0.5",
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=3.0, check=False)
    assert proc.returncode == 2
    assert "Traceback" not in proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["reason"] == "QEMU_VERSION_PROBE_TIMEOUT"
    assert len(data["receipt_sha256"]) == 64


def test_qemu_hash_pin_mismatch_fails_before_probe(tmp_path: Path):
    root = _make_fixture(tmp_path)
    qemu = _make_qemu(tmp_path, _qemu_exact(sleep_after=True))
    proc, data = _run(root, qemu, "--expected-qemu-sha256", "0" * 64)
    assert proc.returncode == 2
    assert data["reason"] == "QEMU_BINARY_SHA_MISMATCH"
    assert "qemu_version" not in data


def test_qemu_boot_spawn_failure_is_structured(tmp_path: Path):
    root = _make_fixture(tmp_path)
    body = (
        "import os, sys\n"
        "if '--version' in sys.argv:\n"
        "    os.unlink(__file__)\n"
        "    print('QEMU emulator version 99.0.0')\n"
    )
    qemu = _make_qemu(tmp_path, body)
    proc, data = _run(root, qemu)
    assert proc.returncode == 2
    assert data["reason"] == "QEMU_BOOT_SPAWN_FAILED"
    assert "Traceback" not in proc.stdout + proc.stderr


def test_out_receipt_written_for_precondition_failure(tmp_path: Path):
    root = _make_fixture(tmp_path, overrides={"RESET_VECTOR": "0x0000fff0"})
    qemu = _make_qemu(tmp_path, _qemu_exact(sleep_after=True))
    out = tmp_path / "receipt.json"
    proc, data = _run(root, qemu, "--out", str(out))
    assert proc.returncode == 2
    assert out.is_file()
    assert json.loads(out.read_text(encoding="utf-8")) == data
