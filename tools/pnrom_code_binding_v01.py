from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

DOMAIN = b"PNROM-CODE-BINDING/v0.1"


def compute_binding(inputs: list[tuple[str, Path]]) -> tuple[bytes, list[dict[str, object]]]:
    h = hashlib.sha256()
    h.update(DOMAIN)
    evidence: list[dict[str, object]] = []
    seen: set[str] = set()
    for label, path in inputs:
        if not label or label in seen:
            raise ValueError("binding labels must be non-empty and unique")
        seen.add(label)
        raw = path.read_bytes()
        lb = label.encode("utf-8")
        if len(lb) > 0xFFFF:
            raise ValueError("binding label too long")
        h.update(len(lb).to_bytes(2, "little"))
        h.update(lb)
        h.update(len(raw).to_bytes(8, "little"))
        h.update(raw)
        evidence.append({
            "label": label,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    return h.digest(), evidence


def main() -> int:
    p = argparse.ArgumentParser(description="Create non-circular PNROM code/build-input binding")
    p.add_argument(
        "--input",
        action="append",
        required=True,
        help="ordered LABEL=PATH entry; exclude PNVH and T36 identity templates",
    )
    p.add_argument("--out-binding", type=Path, required=True)
    p.add_argument("--receipt", type=Path)
    args = p.parse_args()

    inputs: list[tuple[str, Path]] = []
    for item in args.input:
        if "=" not in item:
            raise ValueError("--input must be LABEL=PATH")
        label, path = item.split("=", 1)
        inputs.append((label, Path(path)))
    binding, evidence = compute_binding(inputs)
    args.out_binding.parent.mkdir(parents=True, exist_ok=True)
    args.out_binding.write_bytes(binding)
    if args.receipt:
        receipt = {
            "schema": "PNROM_CODE_BINDING_RECEIPT_V0_1",
            "status": "PASS_HOST_DERIVATION",
            "domain": DOMAIN.decode("ascii"),
            "input_order": evidence,
            "binding_sha256_hex": binding.hex(),
            "binding_bytes": 32,
            "excludes": ["PNVH_TEMPLATE", "T36_IDENTITY_TEMPLATE"],
        }
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
