#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

HEADER_BYTES = 128
VECTOR_DIM = 36
SCALAR_BYTES = 8
TOTAL_BYTES = HEADER_BYTES + VECTOR_DIM * SCALAR_BYTES
MAGIC0 = b"PNVH"
MAGIC1 = b"36\x00\x00"
ENDIAN_MARKER = 0x01020304
DEFAULT_FLAGS = 0x7
SCHEMA = "PNVECTOR_HANDOFF_BUILD_RECEIPT_V0_1"

def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def shahex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def parse_hex32(value: str, name: str) -> bytes:
    try:
        out = bytes.fromhex(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be hex") from exc
    if len(out) != 32:
        raise ValueError(f"{name} must encode exactly 32 bytes")
    return out

def validate_vector_bytes(data: bytes) -> None:
    if len(data) != VECTOR_DIM * SCALAR_BYTES:
        raise ValueError(f"vector must be exactly {VECTOR_DIM * SCALAR_BYTES} bytes")
    values = struct.unpack("<36d", data)
    if not all(math.isfinite(v) for v in values):
        raise ValueError("vector contains non-finite float64")

def build(vector: bytes, basis_binding: bytes, source_context_sha: bytes, flags: int) -> bytes:
    validate_vector_bytes(vector)
    if len(basis_binding) != 32 or len(source_context_sha) != 32:
        raise ValueError("basis binding and source context must be 32 bytes")
    if flags < 0 or flags > 0xffffffff:
        raise ValueError("flags must fit uint32")
    header = bytearray(HEADER_BYTES)
    header[0:4] = MAGIC0
    header[4:8] = MAGIC1
    struct.pack_into("<HHIIHHII", header, 8, 1, 0, HEADER_BYTES, TOTAL_BYTES, VECTOR_DIM, SCALAR_BYTES, ENDIAN_MARKER, flags)
    header[32:64] = basis_binding
    header[64:96] = sha256(vector)
    header[96:128] = source_context_sha
    result = bytes(header) + vector
    if len(result) != TOTAL_BYTES:
        raise AssertionError("internal length error")
    return result

def verify(block: bytes) -> dict:
    if len(block) != TOTAL_BYTES:
        raise ValueError(f"handoff must be exactly {TOTAL_BYTES} bytes")
    if block[0:4] != MAGIC0 or block[4:8] != MAGIC1:
        raise ValueError("magic mismatch")
    major, minor, header_bytes, total_bytes, dim, width, endian, flags = struct.unpack_from("<HHIIHHII", block, 8)
    if (major, minor) != (1, 0):
        raise ValueError("version mismatch")
    if (header_bytes, total_bytes, dim, width, endian) != (HEADER_BYTES, TOTAL_BYTES, VECTOR_DIM, SCALAR_BYTES, ENDIAN_MARKER):
        raise ValueError("geometry mismatch")
    vector = block[HEADER_BYTES:]
    validate_vector_bytes(vector)
    vector_sha = sha256(vector)
    if block[64:96] != vector_sha:
        raise ValueError("embedded vector SHA-256 mismatch")
    return {
        "major": major,
        "minor": minor,
        "flags": flags,
        "basis_binding_hex": block[32:64].hex(),
        "vector_sha256": vector_sha.hex(),
        "source_context_sha256": block[96:128].hex(),
        "handoff_sha256": shahex(block),
        "total_bytes": len(block),
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--vector", type=Path, required=True, help="exact 288-byte little-endian float64 vector")
    b.add_argument("--basis-binding-hex", required=True, help="exact opaque 32-byte basis binding")
    b.add_argument("--source-context-sha256", required=True)
    b.add_argument("--flags", type=lambda x: int(x, 0), default=DEFAULT_FLAGS)
    b.add_argument("--out", type=Path, required=True)
    b.add_argument("--expected-handoff-sha256", default=None)
    b.add_argument("--receipt", type=Path, default=None)
    v = sub.add_parser("verify")
    v.add_argument("handoff", type=Path)
    args = ap.parse_args()

    if args.cmd == "verify":
        info = verify(args.handoff.read_bytes())
        print(json.dumps(info, indent=2, sort_keys=True))
        return 0

    vector = args.vector.read_bytes()
    basis = parse_hex32(args.basis_binding_hex, "basis binding")
    source_sha = parse_hex32(args.source_context_sha256, "source context SHA-256")
    block = build(vector, basis, source_sha, args.flags)
    info = verify(block)
    if args.expected_handoff_sha256 is not None and info["handoff_sha256"] != args.expected_handoff_sha256.lower():
        raise SystemExit(f"FAIL_CLOSED expected handoff SHA-256 {args.expected_handoff_sha256}, got {info['handoff_sha256']}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(block)
    receipt_payload = {
        "schema": SCHEMA,
        "status": "PASS",
        "output": str(args.out),
        **info,
        "finite_float64": True,
        "canon_allowed": False,
        "epistemic": "CHYBA",
    }
    canonical = json.dumps(receipt_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    receipt = {**receipt_payload, "receipt_sha256": hashlib.sha256(canonical).hexdigest()}
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
