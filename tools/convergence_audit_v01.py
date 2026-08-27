#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "PNCORE_PNR_CONVERGENCE_AUDIT_V0_1"

HEX64 = re.compile(r"^[0-9a-f]{64}$")

def canonical_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")

def sha256_obj(obj: Any) -> str:
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()

def require_file(root: Path, rel: str) -> Path:
    p = root / rel
    if not p.is_file():
        raise FileNotFoundError(rel)
    return p

def parse_kv_lines(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("END "):
            continue
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0].replace("_", "").isalnum():
            out[parts[0]] = parts[1]
    return out

def parse_program_unit(text: str) -> dict[str, Any]:
    kv = parse_kv_lines(text)
    ops = []
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith("OPERATOR "):
            parts = s.split()
            if len(parts) != 3:
                raise ValueError(f"invalid OPERATOR row: {s}")
            ops.append(parts[2])
    return {
        "program_id": kv["PROGRAM_ID"],
        "composition_id": kv["COMPOSITION_ID"],
        "operator_schedule_sha256": kv["OPERATOR_SCHEDULE_SHA256"],
        "operators": ops,
        "native_execution_opened": kv.get("NATIVE_EXECUTION_OPENED"),
        "return_execution_opened": kv.get("RETURN_EXECUTION_OPENED"),
        "external_effects": kv.get("EXTERNAL_EFFECTS"),
    }

def parse_raw_pnv_opcodes(text: str) -> list[str]:
    ops = []
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith("OP "):
            parts = s.split()
            if len(parts) >= 3:
                ops.append(parts[2])
    return ops

def parse_asm_bytes(text: str, label: str) -> str:
    m = re.search(rf"(?m)^{re.escape(label)}:\s*\n\s*\.byte\s+([^\n]+)", text)
    if not m:
        raise ValueError(f"missing assembly byte label {label}")
    vals = []
    for token in m.group(1).split(","):
        token = token.strip()
        if not token.startswith("0x"):
            raise ValueError(f"unexpected byte token at {label}: {token}")
        vals.append(int(token, 16))
    return bytes(vals).hex()

def check(name: str, condition: bool, actual: Any = None, expected: Any = None) -> dict[str, Any]:
    return {"name": name, "pass": bool(condition), "actual": actual, "expected": expected}

def run(repo_root: Path) -> dict[str, Any]:
    files = {
        "program_unit": "native/program_units/GENESIS_PROGRAM_UNIT_V0_24.pnv",
        "raw_genesis": "native/GENESIS_V0_1.pnv",
        "pnr": "realizations/x86_64/GENESIS_X86_64_V0_1.pnr",
        "pnr_asm": "arch/x86_64/pncore/pnr_genesis.S",
        "entry_asm": "arch/x86_64/pncore/pncore_entry.S",
        "rom_receipt": "provenance/PNSTORE_MEDIA_BUILD_RECEIPT_V0_1.json",
    }
    paths = {k: require_file(repo_root, v) for k, v in files.items()}

    program = parse_program_unit(paths["program_unit"].read_text(encoding="utf-8"))
    raw_ops = parse_raw_pnv_opcodes(paths["raw_genesis"].read_text(encoding="utf-8"))
    pnr = parse_kv_lines(paths["pnr"].read_text(encoding="utf-8"))
    pnr_asm_text = paths["pnr_asm"].read_text(encoding="utf-8")
    entry_asm_text = paths["entry_asm"].read_text(encoding="utf-8")
    rom_receipt = json.loads(paths["rom_receipt"].read_text(encoding="utf-8"))

    program_digest = program["program_id"].rsplit(":", 1)[-1]
    schedule_digest = program["operator_schedule_sha256"]

    checks = [
        check("program_id_digest_shape", bool(HEX64.match(program_digest)), program_digest, "64 lowercase hex"),
        check("schedule_digest_shape", bool(HEX64.match(schedule_digest)), schedule_digest, "64 lowercase hex"),
        check("pnr_program_id_exact", pnr.get("SOURCE_PROGRAM_ID") == program["program_id"], pnr.get("SOURCE_PROGRAM_ID"), program["program_id"]),
        check("pnr_composition_id_exact", pnr.get("SOURCE_COMPOSITION_ID") == program["composition_id"], pnr.get("SOURCE_COMPOSITION_ID"), program["composition_id"]),
        check("pnr_schedule_exact", pnr.get("SOURCE_OPERATOR_SCHEDULE_SHA256") == schedule_digest, pnr.get("SOURCE_OPERATOR_SCHEDULE_SHA256"), schedule_digest),
        check("pnr_asm_program_digest_exact", parse_asm_bytes(pnr_asm_text, "pnr_genesis_program_digest") == program_digest, parse_asm_bytes(pnr_asm_text, "pnr_genesis_program_digest"), program_digest),
        check("pnr_asm_schedule_digest_exact", parse_asm_bytes(pnr_asm_text, "pnr_genesis_schedule_digest") == schedule_digest, parse_asm_bytes(pnr_asm_text, "pnr_genesis_schedule_digest"), schedule_digest),
        check("entry_expected_program_digest_exact", parse_asm_bytes(entry_asm_text, "expected_genesis_program_digest") == program_digest, parse_asm_bytes(entry_asm_text, "expected_genesis_program_digest"), program_digest),
        check("entry_expected_schedule_digest_exact", parse_asm_bytes(entry_asm_text, "expected_genesis_schedule_digest") == schedule_digest, parse_asm_bytes(entry_asm_text, "expected_genesis_schedule_digest"), schedule_digest),
        check("rom_sha_exact", pnr.get("ROM_SHA256") == rom_receipt.get("rom_sha256"), pnr.get("ROM_SHA256"), rom_receipt.get("rom_sha256")),
        check("rom_size_exact", int(pnr.get("ROM_SIZE_BYTES", "-1")) == int(rom_receipt.get("rom_size_bytes", -2)), pnr.get("ROM_SIZE_BYTES"), rom_receipt.get("rom_size_bytes")),
        check("pnr_realization_exact", pnr.get("REALIZATION_ID") == rom_receipt.get("pnr_realization_id"), pnr.get("REALIZATION_ID"), rom_receipt.get("pnr_realization_id")),
        check("reset_vector_linear", pnr.get("RESET_VECTOR", "").lower() == "0x000ffff0", pnr.get("RESET_VECTOR"), "0x000ffff0"),
        check("program_effects_closed", program["external_effects"] == "FALSE", program["external_effects"], "FALSE"),
        check("program_native_execution_closed", program["native_execution_opened"] == "FALSE", program["native_execution_opened"], "FALSE"),
        check("program_return_execution_closed", program["return_execution_opened"] == "FALSE", program["return_execution_opened"], "FALSE"),
    ]

    canonical_ops = program["operators"]
    raw_genesis_relation = {
        "raw_path": files["raw_genesis"],
        "raw_opcodes": raw_ops,
        "canonical_program_unit_opcodes": canonical_ops,
        "exact_schedule_equal": raw_ops == canonical_ops,
        "classification": "DIVERGENT_LEGACY_OR_DESIGN_CANDIDATE" if raw_ops != canonical_ops else "SCHEDULE_EQUAL",
        "authority_used_by_pnr": files["program_unit"],
    }

    binding_pass = all(x["pass"] for x in checks)
    qemu_tested = bool(rom_receipt.get("qemu_execution_tested"))
    physical_tested = bool(rom_receipt.get("physical_machine_execution_tested"))

    payload = {
        "schema": SCHEMA,
        "repo_root": str(repo_root.resolve()),
        "files": files,
        "checks": checks,
        "raw_genesis_relation": raw_genesis_relation,
        "binding_gate": "PASS" if binding_pass else "FAIL",
        "qemu_execution_tested": qemu_tested,
        "physical_machine_execution_tested": physical_tested,
        "status": "PASS_BINDING_EXECUTION_EVIDENCE_PENDING" if binding_pass and not qemu_tested else "PASS_BINDING_QEMU_REPORTED" if binding_pass and qemu_tested else "FAIL_BINDING",
        "canon_allowed": False,
        "epistemic": "CHYBA",
    }
    return {**payload, "receipt_sha256": sha256_obj(payload)}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo_root", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    try:
        receipt = run(args.repo_root)
    except Exception as exc:
        fail = {"schema": SCHEMA, "status": "FAIL_CLOSED", "error_type": type(exc).__name__, "error": str(exc), "canon_allowed": False, "epistemic": "CHYBA"}
        fail["receipt_sha256"] = sha256_obj(fail)
        print(json.dumps(fail, indent=2, sort_keys=True))
        return 2

    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if receipt["binding_gate"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
