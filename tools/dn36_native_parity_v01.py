from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from tools.dn36_fundamental_vector_commit_v01 import commit

SCHEMA = "BIOOS_DN36_NATIVE_PARITY_V0_1"


def _payloads() -> list[bytes]:
    return [
        b"",
        b"dn36-native-parity",
        bytes(range(256)),
        hashlib.shake_256(b"BIOOS/DN36/NATIVE/PARITY/288").digest(288),
        hashlib.shake_256(b"BIOOS/DN36/NATIVE/PARITY/289").digest(289),
        hashlib.shake_256(b"BIOOS/DN36/NATIVE/PARITY/577").digest(577),
    ]


def _native(binary: Path, payload: bytes) -> dict[str, object]:
    proc = subprocess.run(
        [str(binary), "--commit", payload.hex()],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"native DN36 failed rc={proc.returncode}: {proc.stderr.strip()}"
        )
    try:
        record = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"native DN36 emitted invalid JSON: {proc.stdout!r}") from exc
    if record.get("schema") != "BIOOS_DN36_NATIVE_COMMIT_V0_1":
        raise RuntimeError("native DN36 schema mismatch")
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("build/dn36/BIOOS_DN36_NATIVE_PARITY_V0_1.json"),
    )
    args = parser.parse_args()

    binary = args.binary.resolve()
    if not binary.is_file():
        raise SystemExit(f"native binary not found: {binary}")

    vectors: list[dict[str, object]] = []
    for index, payload in enumerate(_payloads()):
        reference = commit(payload)
        native = _native(binary, payload)
        native_state = bytes.fromhex(str(native["state2304_hex"]))
        native_fold = bytes.fromhex(str(native["fold256_hex"]))
        if native_state != reference.state2304:
            raise RuntimeError(f"state parity mismatch at vector {index}")
        if native_fold != reference.fold256:
            raise RuntimeError(f"fold parity mismatch at vector {index}")
        vectors.append(
            {
                "index": index,
                "payload_bytes": len(payload),
                "payload_sha256": hashlib.sha256(payload).hexdigest(),
                "state2304_sha256": hashlib.sha256(reference.state2304).hexdigest(),
                "fold256_hex": reference.fold256.hex(),
                "parity": "PASS",
            }
        )

    receipt: dict[str, object] = {
        "schema": SCHEMA,
        "status": "PASS_EXACT_SCALAR_C_PYTHON_PARITY",
        "vector_count": len(vectors),
        "vectors": vectors,
        "domain_profile": "BIOOS/DN36/V0.1_DEFAULT_ONLY",
        "security_claim": False,
        "canon_allowed": False,
        "claim_boundary": (
            "Exact byte parity of scalar C v0.1 against the Python reference over the "
            "listed deterministic vectors; not SIMD parity and not cryptographic validation"
        ),
    }
    raw = json.dumps(receipt, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    receipt["receipt_sha256"] = hashlib.sha256(raw).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
