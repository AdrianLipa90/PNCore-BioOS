from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

DOMAIN = b"PNR-T36-BINDING/v0.1"


def derive_pnr_binding(genesis_object: bytes, extension_object: bytes) -> bytes:
    h = hashlib.sha256()
    h.update(DOMAIN)
    h.update(len(genesis_object).to_bytes(8, "little"))
    h.update(genesis_object)
    h.update(len(extension_object).to_bytes(8, "little"))
    h.update(extension_object)
    return h.digest()


def main() -> int:
    p = argparse.ArgumentParser(description="Bind historical PNR1 object plus append-only T36 extension")
    p.add_argument("--pnr-genesis-object", type=Path, required=True)
    p.add_argument("--t36-extension-object", type=Path, required=True)
    p.add_argument("--out-binding", type=Path, required=True)
    p.add_argument("--receipt", type=Path)
    a = p.parse_args()
    g = a.pnr_genesis_object.read_bytes()
    x = a.t36_extension_object.read_bytes()
    binding = derive_pnr_binding(g, x)
    a.out_binding.parent.mkdir(parents=True, exist_ok=True)
    a.out_binding.write_bytes(binding)
    if a.receipt:
        payload = {
            "schema": "PNR_T36_BINDING_RECEIPT_V0_1",
            "status": "PASS_HOST_DERIVATION",
            "domain": DOMAIN.decode("ascii"),
            "pnr_genesis_object_sha256": hashlib.sha256(g).hexdigest(),
            "t36_extension_object_sha256": hashlib.sha256(x).hexdigest(),
            "binding_hex": binding.hex(),
            "binding_bytes": 32,
        }
        a.receipt.parent.mkdir(parents=True, exist_ok=True)
        a.receipt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
