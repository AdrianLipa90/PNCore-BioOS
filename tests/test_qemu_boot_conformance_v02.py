from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parents[0] / "tools" / "qemu_boot_conformance_v02.py"
EXPECTED = ["PNROM", "PN32", "PN64", "T36ID", "PNCORE", "PNR.OK", "SIGMA0", "SCHED"]


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def _make_fixture(tmp_path: Path, *, tamper_receipt: bool = False) -> Path:
    root = tmp_path / "repo"
    rom = root / "build/x86_64/pnrom_v0_3_qemu_test.bin"
    rom.parent.mkdir(parents=True)
    (root / "provenance").mkdir(parents=True)
    raw = bytearray([0] * 65536)
    raw[0xFFF0:0xFFF5] = bytes([0xEA, 0, 0, 0, 0xF0])
    rom.write_bytes(raw)
    payload = {
        "schema": "PNCORE_QEMU_FULL_BOOT_BUILD_V0_1",
        "status": "PASS_HOST_BUILD",
        "scope": "DETERMINISTIC_SYNTHETIC_QEMU_TEST_ROM",
        "rom": "build/x86_64/pnrom_v0_3_qemu_test.bin",
        "rom_bytes": 65536,
        "rom_sha256": hashlib.sha256(raw).hexdigest(),
        "reset_vector_offset": 0xFFF0,
        "reset_vector_prefix_hex": "ea000000f0",
        "qemu_executed": False,
        "physical_execution_claim": False,
        "canon_allowed": False,
        "epistemic": "CHYBA",
    }
    payload["receipt_sha256"] = hashlib.sha256(_canonical(payload)).hexdigest()
    if tamper_receipt:
        payload["rom_bytes"] = 1
    (root / "provenance/PNCORE_QEMU_FULL_BOOT_BUILD_V0_1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return root


def _make_qemu(tmp_path: Path, body: str) -> Path:
    qemu = tmp_path / "fake_qemu.py"
    qemu.write_text("#!/usr/bin/env python3\n" + body, encoding="utf-8")
    qemu.chmod(0o755)
    return qemu


def _exact_body(*, sleep_after: bool, failure: str | None = None) -> str:
    markers = EXPECTED + ([failure] if failure else [])
    text = "\n".join(markers)
    tail = "time.sleep(30)" if sleep_after else "pass"
    return (
        "import sys, time\n"
        "if '--version' in sys.argv:\n"
        "    print('QEMU emulator version 99.0.0')\n"
        "else:\n"
        f"    print({text!r}, flush=True)\n"
        f"    {tail}\n"
    )


def _run(root: Path, qemu: Path, *extra: str, timeout: str = "1.0", probe_timeout: str = "2.0"):
    proc = subprocess.run(
        [
            sys.executable, str(TOOL), str(root),
            "--qemu", str(qemu),
            "--timeout", timeout,
            "--probe-timeout", probe_timeout,
            "--drain-timeout", "0.5",
            *extra,
        ],
        text=True, capture_output=True, check=False, timeout=5.0,
    )
    assert "Traceback" not in proc.stdout + proc.stderr
    return proc, json.loads(proc.stdout)


def test_exact_full_sequence_and_nonexit_pass(tmp_path):
    root = _make_fixture(tmp_path)
    qemu = _make_qemu(tmp_path, _exact_body(sleep_after=True))
    proc, data = _run(root, qemu)
    assert proc.returncode == 0
    assert data["expected_sequence_present"] is True
    assert data["process_alive_at_observation_timeout"] is True
    assert data["status"] == "PASS_QEMU_BOOT_CONFORMANCE_UNPINNED_BINARY"


def test_substring_markers_do_not_pass(tmp_path):
    root = _make_fixture(tmp_path)
    junk = "\n".join("xx" + x + "xx" for x in EXPECTED)
    qemu = _make_qemu(
        tmp_path,
        "import sys, time\n"
        "if '--version' in sys.argv:\n"
        "    print('QEMU emulator version 99.0.0')\n"
        "else:\n"
        f"    print({junk!r}, flush=True)\n"
        "    time.sleep(30)\n",
    )
    proc, data = _run(root, qemu)
    assert proc.returncode == 1
    assert data["reason"] == "EXPECTED_DEBUG_SEQUENCE_MISSING"


def test_missing_t36id_fails(tmp_path):
    root = _make_fixture(tmp_path)
    text = "\n".join(x for x in EXPECTED if x != "T36ID")
    qemu = _make_qemu(
        tmp_path,
        "import sys, time\n"
        "if '--version' in sys.argv:\n"
        "    print('QEMU emulator version 99.0.0')\n"
        "else:\n"
        f"    print({text!r}, flush=True)\n"
        "    time.sleep(30)\n",
    )
    proc, data = _run(root, qemu)
    assert proc.returncode == 1
    assert data["reason"] == "EXPECTED_DEBUG_SEQUENCE_MISSING"


def test_early_exit_after_sched_fails(tmp_path):
    root = _make_fixture(tmp_path)
    qemu = _make_qemu(tmp_path, _exact_body(sleep_after=False))
    proc, data = _run(root, qemu)
    assert proc.returncode == 1
    assert data["reason"] == "QEMU_EXITED_BEFORE_EXPECTED_POST_SCHED_NONEXIT"


def test_failure_marker_exact_line_fails(tmp_path):
    root = _make_fixture(tmp_path)
    qemu = _make_qemu(tmp_path, _exact_body(sleep_after=True, failure="I!"))
    proc, data = _run(root, qemu)
    assert proc.returncode == 1
    assert data["failure_marker_present"] is True
    assert data["reason"] == "BOOT_FAILURE_MARKER"


def test_failure_marker_substring_is_not_marker(tmp_path):
    root = _make_fixture(tmp_path)
    body = _exact_body(sleep_after=True).replace(
        "time.sleep(30)", "print('PREFIX-X-SUFFIX', flush=True); time.sleep(30)"
    )
    qemu = _make_qemu(tmp_path, body)
    proc, data = _run(root, qemu)
    assert proc.returncode == 0
    assert data["failure_marker_present"] is False


def test_tampered_build_receipt_fails_before_qemu(tmp_path):
    root = _make_fixture(tmp_path, tamper_receipt=True)
    qemu = _make_qemu(tmp_path, _exact_body(sleep_after=True))
    proc, data = _run(root, qemu)
    assert proc.returncode == 2
    assert data["reason"] == "BUILD_RECEIPT_INVALID"
    assert "qemu_version" not in data


def test_rom_tamper_against_receipt_fails_before_qemu(tmp_path):
    root = _make_fixture(tmp_path)
    rom = root / "build/x86_64/pnrom_v0_3_qemu_test.bin"
    raw = bytearray(rom.read_bytes())
    raw[1] ^= 1
    rom.write_bytes(raw)
    qemu = _make_qemu(tmp_path, _exact_body(sleep_after=True))
    proc, data = _run(root, qemu)
    assert proc.returncode == 2
    assert data["reason"] == "BUILD_RECEIPT_ROM_SHA_MISMATCH"


def test_reset_vector_tamper_fails(tmp_path):
    root = _make_fixture(tmp_path)
    rom = root / "build/x86_64/pnrom_v0_3_qemu_test.bin"
    raw = bytearray(rom.read_bytes())
    raw[0xFFF0] = 0
    rom.write_bytes(raw)
    receipt = root / "provenance/PNCORE_QEMU_FULL_BOOT_BUILD_V0_1.json"
    obj = json.loads(receipt.read_text())
    obj["rom_sha256"] = hashlib.sha256(raw).hexdigest()
    core = {k: v for k, v in obj.items() if k != "receipt_sha256"}
    obj["receipt_sha256"] = hashlib.sha256(_canonical(core)).hexdigest()
    receipt.write_text(json.dumps(obj), encoding="utf-8")
    qemu = _make_qemu(tmp_path, _exact_body(sleep_after=True))
    proc, data = _run(root, qemu)
    assert proc.returncode == 2
    assert data["reason"] == "RESET_VECTOR_MISMATCH"


def test_qemu_version_probe_timeout_structured(tmp_path):
    root = _make_fixture(tmp_path)
    qemu = _make_qemu(
        tmp_path,
        "import sys, time\n"
        "if '--version' in sys.argv:\n"
        "    time.sleep(30)\n",
    )
    proc, data = _run(root, qemu, probe_timeout="0.2")
    assert proc.returncode == 2
    assert data["reason"] == "QEMU_VERSION_PROBE_TIMEOUT"


def test_qemu_hash_pin_mismatch_fails_before_probe(tmp_path):
    root = _make_fixture(tmp_path)
    qemu = _make_qemu(tmp_path, _exact_body(sleep_after=True))
    proc, data = _run(root, qemu, "--expected-qemu-sha256", "0" * 64)
    assert proc.returncode == 2
    assert data["reason"] == "QEMU_BINARY_SHA_MISMATCH"
    assert "qemu_version" not in data


def test_output_receipt_written_for_precondition_failure(tmp_path):
    root = _make_fixture(tmp_path, tamper_receipt=True)
    qemu = _make_qemu(tmp_path, _exact_body(sleep_after=True))
    out = tmp_path / "custom-receipt.json"
    proc, data = _run(root, qemu, "--out", str(out))
    assert proc.returncode == 2
    assert out.is_file()
    assert json.loads(out.read_text()) == data


def test_invalid_timeout_fails_closed(tmp_path):
    root = _make_fixture(tmp_path)
    qemu = _make_qemu(tmp_path, _exact_body(sleep_after=True))
    proc, data = _run(root, qemu, "--timeout", "nan")
    assert proc.returncode == 2
    assert data["reason"] == "INVALID_TIMEOUT"
