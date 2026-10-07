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

SCHEMA = "PNSTORE_IDE_QEMU_BUILD_V0_1"
PROGRAM_BINDING = "4dd5960aad4ade9029859147c90db5b2f4fc83353407786e66e6476279ca8974"
SCHEDULER_BINDING = "bd6e79f11468a3d5e244b8df4ada6e3b7494187caa971cad0a26ea16cad38c34"
SOURCE_CONTEXT = hashlib.sha256(b"BIOOS-QEMU-PNSTORE-IDE-CI/v0.1").hexdigest()
BASIS_BINDING = bytes(range(32)).hex()

SOURCES = [
    ("pnrom_reset", "arch/x86_64/pnrom/pnrom_reset.S"),
    ("pnrom_longmode", "arch/x86_64/pnrom/pnrom_longmode.S"),
    ("pncore_entry", "arch/x86_64/pncore/pnstore_ide_qemu_entry.S"),
    ("t36_identity", "arch/x86_64/pncore/t36_identity.S"),
    ("t36_identity_boot_entry", "arch/x86_64/pncore/t36_identity_boot_entry.S"),
    ("pnscheduler", "arch/x86_64/pncore/pnscheduler.S"),
    ("pnclock", "arch/x86_64/pncore/pnclock.S"),
    ("pnstore_media", "arch/x86_64/pncore/pnstore_media.S"),
    ("pnstore_ata", "arch/x86_64/pncore/pnstore_ata_pio.S"),
    ("pnr_genesis", "arch/x86_64/pncore/pnr_genesis.S"),
    ("pnr_t36_identity_extension", "arch/x86_64/pncore/pnr_t36_identity_extension.S"),
]

CODE_BINDING_LABELS = [
    ("RESET", "pnrom_reset"),
    ("LONGMODE", "pnrom_longmode"),
    ("PNCORE_IDE_TEST", "pncore_entry"),
    ("T36_IDENTITY", "t36_identity"),
    ("T36_BOOT", "t36_identity_boot_entry"),
    ("SCHEDULER", "pnscheduler"),
    ("CLOCK", "pnclock"),
    ("PNSTORE", "pnstore_media"),
    ("PNSTORE_ATA", "pnstore_ata"),
    ("PNR1", "pnr_genesis"),
    ("T36X", "pnr_t36_identity_extension"),
]


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


def main() -> int:
    ap = argparse.ArgumentParser(description="Build dedicated PNStore IDE/QEMU device-semantics ROM")
    ap.add_argument("repo_root", type=Path, nargs="?", default=Path("."))
    ap.add_argument("--receipt", type=Path, default=Path("provenance/PNSTORE_IDE_QEMU_BUILD_V0_1.json"))
    args = ap.parse_args()

    root = args.repo_root.resolve()
    build = root / "build/x86_64"
    build.mkdir(parents=True, exist_ok=True)
    (root / "provenance").mkdir(parents=True, exist_ok=True)

    for tool in ("as", "ld", "objcopy"):
        if not shutil.which(tool):
            raise SystemExit(f"BLOCKED_TOOL_MISSING: {tool}")

    vector_path = build / "pnstore_ide_vector_test.bin"
    vector_path.write_bytes(struct.pack("<36d", *[0.01 * i for i in range(36)]))
    genesis_path = build / "pnstore_ide_genesis_anchor.bin"
    genesis_path.write_bytes(hashlib.sha256(b"BIOOS-QEMU-PNSTORE-IDE-GENESIS/v0.1").digest())

    pnvh = build / "pnstore_ide_pnvh.bin"
    run([
        sys.executable,
        "tools/pnvector_handoff_builder_v01.py",
        "build",
        "--vector", str(vector_path.relative_to(root)),
        "--basis-binding-hex", BASIS_BINDING,
        "--source-context-sha256", SOURCE_CONTEXT,
        "--out", str(pnvh.relative_to(root)),
        "--receipt", "provenance/PNSTORE_IDE_QEMU_PNVH_RECEIPT_V0_1.json",
    ], root)

    objects: dict[str, Path] = {}
    for name, source in SOURCES:
        obj = build / f"{name}.pnstore_ide.o"
        run(["as", "--32", "-o", str(obj.relative_to(root)), source], root)
        objects[name] = obj

    code_binding = build / "pnstore_ide_code_binding.bin"
    code_cmd = [sys.executable, "tools/pnrom_code_binding_v01.py"]
    for label, name in CODE_BINDING_LABELS:
        code_cmd += ["--input", f"{label}={objects[name].relative_to(root)}"]
    code_cmd += [
        "--input", "LINKER=arch/x86_64/pnrom/pnrom.ld",
        "--out-binding", str(code_binding.relative_to(root)),
        "--receipt", "provenance/PNSTORE_IDE_QEMU_CODE_BINDING_RECEIPT_V0_1.json",
    ]
    run(code_cmd, root)

    pnr_binding = build / "pnstore_ide_pnr_t36_binding.bin"
    run([
        sys.executable,
        "tools/pnr_t36_binding_v01.py",
        "--pnr-genesis-object", str(objects["pnr_genesis"].relative_to(root)),
        "--t36-extension-object", str(objects["pnr_t36_identity_extension"].relative_to(root)),
        "--out-binding", str(pnr_binding.relative_to(root)),
        "--receipt", "provenance/PNSTORE_IDE_QEMU_PNR_T36_RECEIPT_V0_1.json",
    ], root)

    t36 = build / "pnstore_ide_t36_identity.bin"
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
        "--receipt", "provenance/PNSTORE_IDE_QEMU_T36_RECEIPT_V0_1.json",
    ], root)
    if t36.stat().st_size != 256:
        raise SystemExit("FAIL_CLOSED: T36 identity record is not 256 bytes")

    pnvh_template = build / "pnstore_ide_pnvh_template.o"
    t36_template = build / "pnstore_ide_t36_template.o"
    run(["as", "--32", "-o", str(pnvh_template.relative_to(root)), "arch/x86_64/pncore/pnvh_template_pnstore_ide.S"], root)
    run(["as", "--32", "-o", str(t36_template.relative_to(root)), "arch/x86_64/pncore/t36_identity_template_pnstore_ide.S"], root)

    elf = build / "pnstore_ide_qemu_test.elf"
    rom = build / "pnstore_ide_qemu_test.bin"
    link_objects = [objects[name] for name, _ in SOURCES] + [pnvh_template, t36_template]
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

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "PASS_HOST_BUILD",
        "scope": "DEDICATED_QEMU_PIIX_IDE_PNSTORE_DEVICE_SEMANTICS_ROM",
        "rom": str(rom.relative_to(root)),
        "rom_bytes": len(raw),
        "rom_sha256": sha256_file(rom),
        "elf_sha256": sha256_file(elf),
        "reset_vector_offset": 0xFFF0,
        "reset_vector_prefix_hex": raw[0xFFF0:0xFFF5].hex(),
        "pnvh_sha256": sha256_file(pnvh),
        "t36_identity_sha256": sha256_file(t36),
        "vector_sha256": sha256_file(vector_path),
        "genesis_anchor_sha256": sha256_file(genesis_path),
        "source_context_sha256": SOURCE_CONTEXT,
        "basis_binding_hex": BASIS_BINDING,
        "program_binding_hex": PROGRAM_BINDING,
        "scheduler_binding_hex": SCHEDULER_BINDING,
        "backend": "ATA_PIO_PRIMARY_MASTER_LBA28",
        "pnstore_media_bytes": 65536,
        "pnstore_sector_bytes": 512,
        "physical_power_loss_claim": False,
        "physical_machine_claim": False,
        "canon_allowed": False,
        "epistemic": "CHYBA",
        "tool_versions": {
            "as": tool_version("as"),
            "ld": tool_version("ld"),
            "objcopy": tool_version("objcopy"),
            "python": sys.version.split()[0],
        },
    }
    receipt_path = args.receipt if args.receipt.is_absolute() else root / args.receipt
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    payload["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()
    receipt_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
