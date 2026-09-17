#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

SCHEMA = "PNCORE_QEMU_QHTRI_VECTOR_REPLAY_BUILD_V0_1"
SCOPE = "QHTRI_VECTOR_NATIVE_STATE_QEMU_REALIZATION_ADAPTER"
SOURCE_SCHEMA = "BIOOS_VECTOR_NATIVE_QHTRI_SOURCE_V0_1"
SOURCE_STATUS = "LIVE_SAME_TICK_SNAPSHOT_CAPTURED_FOR_EMULATION_REPLAY"
SOURCE_CLASS = "NATURAL_SYSTEM_STATE"
DYNAMICS_CLASS = "ENDOGENOUS_RUNTIME_DYNAMICS"
VECTOR_DIM = 36
PROGRAM_BINDING = "4dd5960aad4ade9029859147c90db5b2f4fc83353407786e66e6476279ca8974"
SCHEDULER_BINDING = "bd6e79f11468a3d5e244b8df4ada6e3b7494187caa971cad0a26ea16cad38c34"
BASIS_BINDING = hashlib.sha256(b"BIOOS-QHTRI-PHI36-LANE-BASIS/v0.1").hexdigest()

NON_TEMPLATE_SOURCES = [
    ("pnrom_reset", "arch/x86_64/pnrom/pnrom_reset.S"),
    ("pnrom_longmode", "arch/x86_64/pnrom/pnrom_longmode.S"),
    ("pncore_entry", "arch/x86_64/pncore/pncore_entry.S"),
    ("t36_identity", "arch/x86_64/pncore/t36_identity.S"),
    ("t36_identity_boot_entry", "arch/x86_64/pncore/t36_identity_boot_entry.S"),
    ("pnscheduler", "arch/x86_64/pncore/pnscheduler.S"),
    ("pnclock", "arch/x86_64/pncore/pnclock.S"),
    ("pnstore_media", "arch/x86_64/pncore/pnstore_media.S"),
    ("pnr_genesis", "arch/x86_64/pncore/pnr_genesis.S"),
    ("pnr_t36_identity_extension", "arch/x86_64/pncore/pnr_t36_identity_extension.S"),
]

CODE_BINDING_LABELS = [
    ("RESET", "pnrom_reset"),
    ("LONGMODE", "pnrom_longmode"),
    ("PNCORE", "pncore_entry"),
    ("T36_IDENTITY", "t36_identity"),
    ("T36_BOOT", "t36_identity_boot_entry"),
    ("SCHEDULER", "pnscheduler"),
    ("CLOCK", "pnclock"),
    ("PNSTORE", "pnstore_media"),
    ("PNR1", "pnr_genesis"),
    ("T36X", "pnr_t36_identity_extension"),
]


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def hex64(value: Any, name: str) -> str:
    text = str(value).lower()
    if len(text) != 64:
        raise ValueError(f"{name} must be 64 hex characters")
    try:
        bytes.fromhex(text)
    except ValueError as exc:
        raise ValueError(f"{name} must be hexadecimal") from exc
    return text


def finite_vector(value: Any, name: str) -> tuple[float, ...]:
    if not isinstance(value, list) or len(value) != VECTOR_DIM:
        raise ValueError(f"{name} must contain exactly {VECTOR_DIM} values")
    out = tuple(float(v) for v in value)
    if not all(math.isfinite(v) for v in out):
        raise ValueError(f"{name} contains non-finite values")
    return out


def run(cmd: list[str], root: Path) -> None:
    subprocess.run(cmd, cwd=root, check=True)


def tool_version(tool: str) -> str:
    resolved = shutil.which(tool)
    if not resolved:
        raise RuntimeError(f"required tool missing: {tool}")
    p = subprocess.run([resolved, "--version"], text=True, capture_output=True, check=False)
    text = p.stdout or p.stderr
    return text.splitlines()[0] if text else resolved


def load_source(path: Path) -> tuple[dict[str, Any], bytes, tuple[float, ...], tuple[float, ...]]:
    raw = path.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("QHTRI source must be a JSON object")
    if obj.get("schema") != SOURCE_SCHEMA:
        raise ValueError("QHTRI source schema mismatch")
    if obj.get("status") != SOURCE_STATUS:
        raise ValueError("QHTRI source status is not a same-tick replay snapshot")
    if obj.get("dimension") != VECTOR_DIM:
        raise ValueError("QHTRI source dimension mismatch")
    if obj.get("source_class") != SOURCE_CLASS:
        raise ValueError("QHTRI source class mismatch")
    if obj.get("dynamics_class") != DYNAMICS_CLASS:
        raise ValueError("QHTRI dynamics class mismatch")
    if obj.get("tether_status") != "ACTIVE":
        raise ValueError("QHTRI source snapshot was not captured under ACTIVE tether")
    if obj.get("canon_allowed") is not False:
        raise ValueError("QHTRI source unexpectedly grants canon authority")
    if obj.get("physical_h200_execution_claim") is not False:
        raise ValueError("QHTRI source unexpectedly claims physical H200 execution")
    if obj.get("physical_qpu_claim") is not False:
        raise ValueError("QHTRI source unexpectedly claims physical QPU execution")

    tick = obj.get("tick")
    if not isinstance(tick, int) or isinstance(tick, bool) or tick < 0:
        raise ValueError("QHTRI tick must be a non-negative integer")
    surface_state = obj.get("surface_state")
    if not isinstance(surface_state, dict) or surface_state.get("noema_tick") != tick:
        raise ValueError("QHTRI source is not same-tick bound to NOEMA surface state")

    phi = finite_vector(obj.get("phi"), "phi")
    omega = finite_vector(obj.get("omega"), "omega")
    phi_bytes = struct.pack("<36d", *phi)
    omega_bytes = struct.pack("<36d", *omega)
    if sha256_bytes(phi_bytes) != hex64(obj.get("phi_raw_sha256"), "phi_raw_sha256"):
        raise ValueError("phi_raw_sha256 mismatch")
    if sha256_bytes(omega_bytes) != hex64(obj.get("omega_raw_sha256"), "omega_raw_sha256"):
        raise ValueError("omega_raw_sha256 mismatch")

    for key in (
        "g_raw_sha256",
        "R_geom_raw_sha256",
        "psi_geom_raw_sha256",
        "tau_raw_sha256",
        "holonomy_raw_sha256",
        "working_state_sha256",
        "receipt_sha256",
    ):
        hex64(obj.get(key), key)

    selected = obj.get("selected_edge")
    if not isinstance(selected, dict):
        raise ValueError("selected_edge is required")
    i = selected.get("oscillator_i")
    j = selected.get("oscillator_j")
    if not isinstance(i, int) or not isinstance(j, int) or not (0 <= i < VECTOR_DIM and 0 <= j < VECTOR_DIM) or i == j:
        raise ValueError("selected_edge oscillator ids are invalid")
    if not math.isclose(float(selected.get("phi_i")), phi[i], rel_tol=0.0, abs_tol=1e-15):
        raise ValueError("selected_edge phi_i is not bound to source phi lane")
    if not math.isclose(float(selected.get("phi_j")), phi[j], rel_tol=0.0, abs_tol=1e-15):
        raise ValueError("selected_edge phi_j is not bound to source phi lane")
    coupling = float(selected.get("coupling"))
    if not math.isfinite(coupling) or coupling == 0.0:
        raise ValueError("selected_edge coupling must be finite and non-zero")

    return obj, raw, phi, omega


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build a QEMU realization-adapter ROM from a frozen same-tick QHTRI/NOEMA 36D vector snapshot"
    )
    ap.add_argument("repo_root", type=Path, nargs="?", default=Path("."))
    ap.add_argument(
        "--source",
        type=Path,
        default=Path("provenance/BIOOS_VECTOR_NATIVE_QHTRI_SOURCE_V0_1.json"),
    )
    ap.add_argument(
        "--receipt",
        type=Path,
        default=Path("provenance/PNCORE_QEMU_QHTRI_VECTOR_REPLAY_BUILD_V0_1.json"),
    )
    args = ap.parse_args()

    root = args.repo_root.resolve()
    source = args.source if args.source.is_absolute() else root / args.source
    receipt_path = args.receipt if args.receipt.is_absolute() else root / args.receipt
    build = root / "build/x86_64"
    build.mkdir(parents=True, exist_ok=True)
    (root / "provenance").mkdir(parents=True, exist_ok=True)

    for tool in ("as", "ld", "objcopy"):
        if not shutil.which(tool):
            raise SystemExit(f"BLOCKED_TOOL_MISSING: {tool}")

    try:
        snapshot, source_raw, phi, omega = load_source(source)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"FAIL_CLOSED_QHTRI_SOURCE_INVALID: {exc}") from exc

    vector_path = build / "qemu_vector_test.bin"
    vector_bytes = struct.pack("<36d", *phi)
    vector_path.write_bytes(vector_bytes)

    genesis_path = build / "qemu_genesis_anchor.bin"
    genesis_path.write_bytes(bytes.fromhex(hex64(snapshot["working_state_sha256"], "working_state_sha256")))

    source_file_sha = sha256_bytes(source_raw)
    pnvh = build / "pnvector_handoff_test.bin"
    pnvh_receipt = root / "provenance/QEMU_QHTRI_PNVECTOR_HANDOFF_BUILD_RECEIPT_V0_1.json"
    run([
        sys.executable,
        "tools/pnvector_handoff_builder_v01.py",
        "build",
        "--vector", str(vector_path.relative_to(root)),
        "--basis-binding-hex", BASIS_BINDING,
        "--source-context-sha256", source_file_sha,
        "--out", str(pnvh.relative_to(root)),
        "--receipt", str(pnvh_receipt.relative_to(root)),
    ], root)

    objects: dict[str, Path] = {}
    for name, source_rel in NON_TEMPLATE_SOURCES:
        obj = build / f"{name}.qhtri-replay.o"
        run(["as", "--32", "-o", str(obj.relative_to(root)), source_rel], root)
        objects[name] = obj

    code_binding = build / "pnrom_code_binding.qhtri-replay.bin"
    code_receipt = root / "provenance/QEMU_QHTRI_PNROM_CODE_BINDING_RECEIPT_V0_1.json"
    code_cmd = [sys.executable, "tools/pnrom_code_binding_v01.py"]
    for label, name in CODE_BINDING_LABELS:
        code_cmd += ["--input", f"{label}={objects[name].relative_to(root)}"]
    code_cmd += [
        "--input", "LINKER=arch/x86_64/pnrom/pnrom.ld",
        "--out-binding", str(code_binding.relative_to(root)),
        "--receipt", str(code_receipt.relative_to(root)),
    ]
    run(code_cmd, root)

    pnr_binding = build / "pnr_t36_binding.qhtri-replay.bin"
    pnr_receipt = root / "provenance/QEMU_QHTRI_PNR_T36_BINDING_RECEIPT_V0_1.json"
    run([
        sys.executable,
        "tools/pnr_t36_binding_v01.py",
        "--pnr-genesis-object", str(objects["pnr_genesis"].relative_to(root)),
        "--t36-extension-object", str(objects["pnr_t36_identity_extension"].relative_to(root)),
        "--out-binding", str(pnr_binding.relative_to(root)),
        "--receipt", str(pnr_receipt.relative_to(root)),
    ], root)

    t36 = build / "t36_identity_test.bin"
    t36_receipt = root / "provenance/QEMU_QHTRI_T36_IDENTITY_BUILD_RECEIPT_V0_1.json"
    run([
        sys.executable,
        "tools/t36_identity_builder_v01.py",
        "--pnvh", str(pnvh.relative_to(root)),
        "--genesis-anchor-file", str(genesis_path.relative_to(root)),
        "--pnrom-code-binding-file", str(code_binding.relative_to(root)),
        "--pnr-binding-file", str(pnr_binding.relative_to(root)),
        "--program-binding-hex", PROGRAM_BINDING,
        "--scheduler-binding-hex", SCHEDULER_BINDING,
        "--out", str(t36.relative_to(root)),
        "--receipt", str(t36_receipt.relative_to(root)),
    ], root)
    if t36.stat().st_size != 256:
        raise SystemExit("FAIL_CLOSED: T36 identity record is not 256 bytes")

    pnvh_template = build / "pnvh_template.qhtri-replay.o"
    t36_template = build / "t36_identity_template.qhtri-replay.o"
    run(["as", "--32", "-o", str(pnvh_template.relative_to(root)), "arch/x86_64/pncore/pnvh_template.S"], root)
    run(["as", "--32", "-o", str(t36_template.relative_to(root)), "arch/x86_64/pncore/t36_identity_template.S"], root)

    elf = build / "pnrom_v0_3_qhtri_vector_replay.elf"
    rom = build / "pnrom_v0_3_qhtri_vector_replay.bin"
    link_objects = [objects[name] for name, _ in NON_TEMPLATE_SOURCES] + [pnvh_template, t36_template]
    run([
        "ld", "-m", "elf_i386", "-T", "arch/x86_64/pnrom/pnrom.ld",
        "-o", str(elf.relative_to(root)),
        *[str(p.relative_to(root)) for p in link_objects],
    ], root)
    run([
        "objcopy", "-O", "binary", "--gap-fill", "0xff",
        str(elf.relative_to(root)), str(rom.relative_to(root)),
    ], root)

    raw = rom.read_bytes()
    if len(raw) != 65536:
        raise SystemExit(f"FAIL_CLOSED: ROM must be 65536 bytes, got {len(raw)}")
    reset_prefix = bytes([0xEA, 0x00, 0x00, 0x00, 0xF0])
    if raw[0xFFF0:0xFFF5] != reset_prefix:
        raise SystemExit(f"FAIL_CLOSED: reset vector mismatch: {raw[0xFFF0:0xFFF5].hex()}")

    pnvh_raw = pnvh.read_bytes()
    t36_raw = t36.read_bytes()
    pnvh_occurrences = raw.count(pnvh_raw)
    t36_occurrences = raw.count(t36_raw)
    if pnvh_occurrences != 1:
        raise SystemExit(f"FAIL_CLOSED: exact PNVH embedding count must be 1, got {pnvh_occurrences}")
    if t36_occurrences != 1:
        raise SystemExit(f"FAIL_CLOSED: exact T36 identity embedding count must be 1, got {t36_occurrences}")

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "PASS_HOST_BUILD",
        "scope": SCOPE,
        "semantic_runtime": "QHTRI_NOEMA_VECTOR_NATIVE",
        "realization_adapter": "X86_64_QEMU_TCG_BINARY_BOUNDARY",
        "binary_adapter_only": True,
        "source_snapshot": str(source.relative_to(root) if source.is_relative_to(root) else source),
        "source_snapshot_file_sha256": source_file_sha,
        "source_snapshot_receipt_sha256": snapshot["receipt_sha256"],
        "source_tick": snapshot["tick"],
        "source_working_state_sha256": snapshot["working_state_sha256"],
        "source_g_raw_sha256": snapshot["g_raw_sha256"],
        "source_R_geom_raw_sha256": snapshot["R_geom_raw_sha256"],
        "source_psi_geom_raw_sha256": snapshot["psi_geom_raw_sha256"],
        "source_tau_raw_sha256": snapshot["tau_raw_sha256"],
        "source_holonomy_raw_sha256": snapshot["holonomy_raw_sha256"],
        "source_selected_edge": snapshot["selected_edge"],
        "vector_semantics": "QHTRI_PHI_36_LANES_FLOAT64_LE",
        "omega_witness_sha256": sha256_bytes(struct.pack("<36d", *omega)),
        "vector_sha256": sha256_file(vector_path),
        "basis_binding_hex": BASIS_BINDING,
        "source_context_sha256": source_file_sha,
        "pnvh": str(pnvh.relative_to(root)),
        "pnvh_sha256": sha256_file(pnvh),
        "t36_identity": str(t36.relative_to(root)),
        "t36_identity_sha256": sha256_file(t36),
        "genesis_anchor_sha256": sha256_file(genesis_path),
        "program_binding_hex": PROGRAM_BINDING,
        "scheduler_binding_hex": SCHEDULER_BINDING,
        "rom": str(rom.relative_to(root)),
        "rom_bytes": len(raw),
        "rom_sha256": sha256_file(rom),
        "elf_sha256": sha256_file(elf),
        "reset_vector_offset": 0xFFF0,
        "reset_vector_prefix_hex": raw[0xFFF0:0xFFF5].hex(),
        "pnvh_exact_rom_occurrences": pnvh_occurrences,
        "t36_exact_rom_occurrences": t36_occurrences,
        "source_validation": {
            "same_tick_surface_binding": True,
            "phi_sha256_bound": True,
            "omega_sha256_bound": True,
            "selected_edge_bound_to_phi": True,
            "tether_active_at_capture": True,
        },
        "tool_versions": {
            "as": tool_version("as"),
            "ld": tool_version("ld"),
            "objcopy": tool_version("objcopy"),
            "python": sys.version.split()[0],
        },
        "qemu_executed": False,
        "physical_execution_claim": False,
        "physical_qpu_claim": False,
        "canon_allowed": False,
        "epistemic": "CHYBA",
    }
    payload["receipt_sha256"] = sha256_bytes(canonical_bytes(payload))
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
