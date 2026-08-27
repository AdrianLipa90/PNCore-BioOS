from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.t36_identity_record_v01 import (
    T36IdentityRecord,
    derive_configuration_sha256,
    derive_crystal_id,
    derive_genesis_anchor_commitment,
    derive_origin_binding_sha256,
    record_sha256,
)

PNVH_BYTES = 416
PNVH_VECTOR_OFF = 128
PNVH_VECTOR_BYTES = 288


def _hex32(value: str, name: str) -> bytes:
    try:
        raw = bytes.fromhex(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be hex") from exc
    if len(raw) != 32:
        raise ValueError(f"{name} must encode exactly 32 bytes")
    return raw


def _file32(path: Path, name: str) -> bytes:
    raw = path.read_bytes()
    if len(raw) != 32:
        raise ValueError(f"{name} file must contain exactly 32 bytes")
    return raw


def _load_pnvh(path: Path) -> tuple[bytes, bytes, bytes, bytes]:
    raw = path.read_bytes()
    if len(raw) != PNVH_BYTES:
        raise ValueError("PNVH must be exactly 416 bytes")
    if raw[0:4] != b"PNVH" or raw[4:8] != b"36\x00\x00":
        raise ValueError("invalid PNVH magic")
    if int.from_bytes(raw[8:10], "little") != 1 or int.from_bytes(raw[10:12], "little") != 0:
        raise ValueError("unsupported PNVH version")
    if int.from_bytes(raw[12:16], "little") != 128 or int.from_bytes(raw[16:20], "little") != 416:
        raise ValueError("invalid PNVH geometry")
    if int.from_bytes(raw[20:22], "little") != 36 or int.from_bytes(raw[22:24], "little") != 8:
        raise ValueError("invalid PNVH vector geometry")
    if int.from_bytes(raw[24:28], "little") != 0x01020304:
        raise ValueError("invalid PNVH endian marker")
    basis = raw[32:64]
    declared_vector_sha = raw[64:96]
    source_context_sha = raw[96:128]
    vector = raw[PNVH_VECTOR_OFF:PNVH_VECTOR_OFF + PNVH_VECTOR_BYTES]
    actual_vector_sha = hashlib.sha256(vector).digest()
    if actual_vector_sha != declared_vector_sha:
        raise ValueError("PNVH vector SHA-256 mismatch")
    return raw, basis, declared_vector_sha, source_context_sha


def build_record(
    *,
    pnvh_path: Path,
    genesis_anchor_path: Path,
    pnrom_code_binding: bytes,
    pnr_binding: bytes,
    program_binding: bytes,
    scheduler_binding: bytes,
    flags: int = 0x7,
    phase_index: int = 0,
    boot_epoch: int = 0,
) -> tuple[T36IdentityRecord, dict[str, object]]:
    pnvh_raw, basis, vector_sha, source_context_sha = _load_pnvh(pnvh_path)
    anchor = genesis_anchor_path.read_bytes()
    if len(anchor) != 32:
        raise ValueError("genesis anchor file must contain exactly 32 bytes")

    crystal_id = derive_crystal_id(anchor)
    commitment = derive_genesis_anchor_commitment(anchor)
    origin = derive_origin_binding_sha256(
        crystal_id, vector_sha, source_context_sha, basis, pnr_binding
    )
    configuration = derive_configuration_sha256(
        vector_sha,
        basis,
        source_context_sha,
        pnrom_code_binding,
        pnr_binding,
        program_binding,
        scheduler_binding,
    )
    record = T36IdentityRecord(
        flags=flags,
        crystal_id=crystal_id,
        genesis_anchor_commitment=commitment,
        origin_binding_sha256=origin,
        pnvector_payload_sha256=vector_sha,
        source_context_sha256=source_context_sha,
        basis_binding=basis,
        configuration_sha256=configuration,
        phase_index=phase_index,
        boot_epoch=boot_epoch,
    )
    receipt = {
        "schema": "T36_IDENTITY_BUILD_RECEIPT_V0_1",
        "status": "PASS_HOST_DERIVATION",
        "pnvh_sha256": hashlib.sha256(pnvh_raw).hexdigest(),
        "pnvector_payload_sha256": vector_sha.hex(),
        "source_context_sha256": source_context_sha.hex(),
        "basis_binding_hex": basis.hex(),
        "genesis_anchor_commitment": commitment.hex(),
        "crystal_id": crystal_id.hex(),
        "origin_binding_sha256": origin.hex(),
        "configuration_sha256": configuration.hex(),
        "record_sha256": record_sha256(record),
        "record_bytes": 256,
        "phase_index": phase_index,
        "boot_epoch": boot_epoch,
        "flags": flags,
        "raw_genesis_anchor_recorded": False,
    }
    return record, receipt


def main() -> int:
    p = argparse.ArgumentParser(description="Build exact T36 identity record from admitted PNVH and provisioning bindings")
    p.add_argument("--pnvh", required=True, type=Path)
    p.add_argument("--genesis-anchor-file", required=True, type=Path)

    rom = p.add_mutually_exclusive_group(required=True)
    rom.add_argument("--pnrom-code-binding-hex")
    rom.add_argument("--pnrom-code-binding-file", type=Path)
    pnr = p.add_mutually_exclusive_group(required=True)
    pnr.add_argument("--pnr-binding-hex")
    pnr.add_argument("--pnr-binding-file", type=Path)

    p.add_argument("--program-binding-hex", required=True)
    p.add_argument("--scheduler-binding-hex", required=True)
    p.add_argument("--flags", default="0x7")
    p.add_argument("--phase-index", type=int, default=0)
    p.add_argument("--boot-epoch", type=int, default=0)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--receipt", type=Path)
    args = p.parse_args()

    rom_binding = (
        _file32(args.pnrom_code_binding_file, "pnrom_code_binding")
        if args.pnrom_code_binding_file
        else _hex32(args.pnrom_code_binding_hex, "pnrom_code_binding")
    )
    pnr_binding = (
        _file32(args.pnr_binding_file, "pnr_binding")
        if args.pnr_binding_file
        else _hex32(args.pnr_binding_hex, "pnr_binding")
    )

    record, receipt = build_record(
        pnvh_path=args.pnvh,
        genesis_anchor_path=args.genesis_anchor_file,
        pnrom_code_binding=rom_binding,
        pnr_binding=pnr_binding,
        program_binding=_hex32(args.program_binding_hex, "program_binding"),
        scheduler_binding=_hex32(args.scheduler_binding_hex, "scheduler_binding"),
        flags=int(args.flags, 0),
        phase_index=args.phase_index,
        boot_epoch=args.boot_epoch,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(record.pack())
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
