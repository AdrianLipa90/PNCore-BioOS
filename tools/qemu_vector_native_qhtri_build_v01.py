#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

from tools.vector_native_qhtri_replay_v01 import (
    build_replay_binary,
    build_replay_receipt,
    validate_replay_receipt,
    validate_source_snapshot,
)

SCHEMA = "BIOOS_VECTOR_NATIVE_QHTRI_QEMU_BUILD_V0_1"
PROGRAM_BINDING = "4dd5960aad4ade9029859147c90db5b2f4fc83353407786e66e6476279ca8974"
SCHEDULER_BINDING = "bd6e79f11468a3d5e244b8df4ada6e3b7494187caa971cad0a26ea16cad38c34"
BASIS_BINDING = bytes(range(32)).hex()

SOURCES = [
    ("pnrom_reset", "arch/x86_64/pnrom/pnrom_reset.S"),
    ("pnrom_longmode", "arch/x86_64/pnrom/pnrom_longmode.S"),
    ("pncore_entry", "arch/x86_64/pncore/vector_native_qhtri_replay_entry.S"),
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
    ("PNCORE_VECTOR_REPLAY", "pncore_entry"),
    ("T36_IDENTITY", "t36_identity"),
    ("T36_BOOT", "t36_identity_boot_entry"),
    ("SCHEDULER", "pnscheduler"),
    ("CLOCK", "pnclock"),
    ("PNSTORE", "pnstore_media"),
    ("PNR1", "pnr_genesis"),
    ("T36X", "pnr_t36_identity_extension"),
]


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def run(cmd: list[str], root: Path) -> None:
    subprocess.run(cmd, cwd=root, check=True)


def tool_version(tool: str) -> str:
    resolved = shutil.which(tool)
    if not resolved:
        raise RuntimeError(f"required tool missing: {tool}")
    p = subprocess.run([resolved, "--version"], text=True, capture_output=True, check=False)
    text = p.stdout or p.stderr
    return text.splitlines()[0] if text else resolved


def fold64(replay: bytes) -> int:
    if len(replay) != 680:
        raise ValueError("replay payload must be exactly 680 bytes")
    value = 0
    for offset in range(40, 616, 8):
        word = struct.unpack_from("<Q", replay, offset)[0]
        value ^= word
        value = ((value << 1) & 0xffffffffffffffff) | (value >> 63)
    return value


def main() -> int:
    ap = argparse.ArgumentParser(description="Build BioOS ROM consuming the exact vector-native QHTRI replay payload")
    ap.add_argument("repo_root", type=Path, nargs="?", default=Path("."))
    ap.add_argument("--source", type=Path, default=Path("provenance/BIOOS_VECTOR_NATIVE_QHTRI_SOURCE_V0_1.json"))
    ap.add_argument("--replay-receipt", type=Path, default=Path("provenance/BIOOS_VECTOR_NATIVE_QHTRI_REPLAY_V0_1.json"))
    ap.add_argument("--receipt", type=Path, default=Path("provenance/BIOOS_VECTOR_NATIVE_QHTRI_QEMU_BUILD_V0_1.json"))
    args = ap.parse_args()

    root = args.repo_root.resolve()
    build_dir = root / "build/x86_64"
    build_dir.mkdir(parents=True, exist_ok=True)
    (root / "provenance").mkdir(parents=True, exist_ok=True)

    for tool in ("as", "ld", "objcopy"):
        if not shutil.which(tool):
            raise SystemExit(f"BLOCKED_TOOL_MISSING: {tool}")

    source_path = args.source if args.source.is_absolute() else root / args.source
    replay_receipt_path = args.replay_receipt if args.replay_receipt.is_absolute() else root / args.replay_receipt
    source = json.loads(source_path.read_text(encoding="utf-8"))
    state = validate_source_snapshot(source)
    replay = build_replay_binary(source)
    expected_replay_receipt = build_replay_receipt(source)
    recorded_replay_receipt = json.loads(replay_receipt_path.read_text(encoding="utf-8"))
    validate_replay_receipt(recorded_replay_receipt, source)
    if recorded_replay_receipt != expected_replay_receipt:
        raise SystemExit("FAIL_CLOSED: replay receipt is not exact deterministic reconstruction")

    replay_path = build_dir / "vector_native_qhtri_replay_v01.bin"
    replay_path.write_bytes(replay)
    vector_path = build_dir / "qemu_vector_test.bin"
    vector_path.write_bytes(struct.pack("<36d", *state["phi"]))

    source_context = hashlib.sha256(
        b"BIOOS-QEMU-VECTOR-NATIVE-QHTRI/v0.1\0" + bytes.fromhex(state["source_receipt_sha256"])
    ).hexdigest()
    genesis_path = build_dir / "qemu_genesis_anchor.bin"
    genesis_path.write_bytes(
        hashlib.sha256(b"BIOOS-QEMU-VECTOR-NATIVE-QHTRI-GENESIS/v0.1\0" + bytes.fromhex(state["source_receipt_sha256"])).digest()
    )

    pnvh = build_dir / "pnvector_handoff_test.bin"
    run([
        sys.executable, "tools/pnvector_handoff_builder_v01.py", "build",
        "--vector", str(vector_path.relative_to(root)),
        "--basis-binding-hex", BASIS_BINDING,
        "--source-context-sha256", source_context,
        "--out", str(pnvh.relative_to(root)),
        "--receipt", "provenance/BIOOS_VECTOR_NATIVE_QHTRI_PNVH_RECEIPT_V0_1.json",
    ], root)

    objects: dict[str, Path] = {}
    for name, source_file in SOURCES:
        obj = build_dir / f"{name}.vector_qhtri.o"
        run(["as", "--32", "-o", str(obj.relative_to(root)), source_file], root)
        objects[name] = obj

    code_binding = build_dir / "pnrom_code_binding.vector_qhtri.bin"
    code_cmd = [sys.executable, "tools/pnrom_code_binding_v01.py"]
    for label, name in CODE_BINDING_LABELS:
        code_cmd += ["--input", f"{label}={objects[name].relative_to(root)}"]
    code_cmd += [
        "--input", f"REPLAY={replay_path.relative_to(root)}",
        "--input", "LINKER=arch/x86_64/pnrom/pnrom.ld",
        "--out-binding", str(code_binding.relative_to(root)),
        "--receipt", "provenance/BIOOS_VECTOR_NATIVE_QHTRI_CODE_BINDING_RECEIPT_V0_1.json",
    ]
    run(code_cmd, root)

    pnr_binding = build_dir / "pnr_t36_binding.vector_qhtri.bin"
    run([
        sys.executable, "tools/pnr_t36_binding_v01.py",
        "--pnr-genesis-object", str(objects["pnr_genesis"].relative_to(root)),
        "--t36-extension-object", str(objects["pnr_t36_identity_extension"].relative_to(root)),
        "--out-binding", str(pnr_binding.relative_to(root)),
        "--receipt", "provenance/BIOOS_VECTOR_NATIVE_QHTRI_PNR_T36_RECEIPT_V0_1.json",
    ], root)

    t36 = build_dir / "t36_identity_test.bin"
    run([
        sys.executable, "tools/t36_identity_builder_v01.py",
        "--pnvh", str(pnvh.relative_to(root)),
        "--genesis-anchor-file", str(genesis_path.relative_to(root)),
        "--pnrom-code-binding-file", str(code_binding.relative_to(root)),
        "--pnr-binding-file", str(pnr_binding.relative_to(root)),
        "--program-binding-hex", PROGRAM_BINDING,
        "--scheduler-binding-hex", SCHEDULER_BINDING,
        "--out", str(t36.relative_to(root)),
        "--receipt", "provenance/BIOOS_VECTOR_NATIVE_QHTRI_T36_RECEIPT_V0_1.json",
    ], root)
    if t36.stat().st_size != 256:
        raise SystemExit("FAIL_CLOSED: T36 identity record is not 256 bytes")

    pnvh_template = build_dir / "pnvh_template.vector_qhtri.o"
    t36_template = build_dir / "t36_identity_template.vector_qhtri.o"
    replay_template = build_dir / "vector_native_qhtri_replay_template.o"
    run(["as", "--32", "-o", str(pnvh_template.relative_to(root)), "arch/x86_64/pncore/pnvh_template.S"], root)
    run(["as", "--32", "-o", str(t36_template.relative_to(root)), "arch/x86_64/pncore/t36_identity_template.S"], root)
    run(["as", "--32", "-o", str(replay_template.relative_to(root)), "arch/x86_64/pncore/vector_native_qhtri_replay_template.S"], root)

    elf = build_dir / "bioos_vector_native_qhtri_qemu.elf"
    rom = build_dir / "bioos_vector_native_qhtri_qemu.bin"
    link_objects = [objects[name] for name, _ in SOURCES] + [pnvh_template, t36_template, replay_template]
    run([
        "ld", "-m", "elf_i386", "-T", "arch/x86_64/pnrom/pnrom.ld",
        "-o", str(elf.relative_to(root)), *[str(p.relative_to(root)) for p in link_objects],
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
    replay_offset = raw.find(replay)
    if replay_offset < 0 or raw.find(replay, replay_offset + 1) >= 0:
        raise SystemExit("FAIL_CLOSED: exact replay payload must appear exactly once in ROM")

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "PASS_HOST_BUILD",
        "scope": "QEMU_TCG_VECTOR_NATIVE_QHTRI_EXACT_REPLAY_ROM",
        "source_receipt_sha256": state["source_receipt_sha256"],
        "working_state_sha256": state["working_state_sha256"],
        "source_tick": state["tick"],
        "replay_receipt_sha256": recorded_replay_receipt["replay_receipt_sha256"],
        "replay_binary_bytes": len(replay),
        "replay_binary_sha256": hashlib.sha256(replay).hexdigest(),
        "replay_rom_offset": replay_offset,
        "expected_vector_fold64_hex": f"{fold64(replay):016x}",
        "rom": str(rom.relative_to(root)),
        "rom_bytes": len(raw),
        "rom_sha256": sha256_file(rom),
        "elf_sha256": sha256_file(elf),
        "reset_vector_offset": 0xFFF0,
        "reset_vector_prefix_hex": raw[0xFFF0:0xFFF5].hex(),
        "pnvh_sha256": sha256_file(pnvh),
        "t36_identity_sha256": sha256_file(t36),
        "source_context_sha256": source_context,
        "qemu_executed": False,
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "physical_h200_execution_claim": False,
        "physical_qpu_claim": False,
        "physical_machine_claim": False,
        "epistemic": "CHYBA",
        "tool_versions": {
            "as": tool_version("as"),
            "ld": tool_version("ld"),
            "objcopy": tool_version("objcopy"),
            "python": sys.version.split()[0],
        },
    }
    payload["receipt_sha256"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    receipt_path = args.receipt if args.receipt.is_absolute() else root / args.receipt
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
