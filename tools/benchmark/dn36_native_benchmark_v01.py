from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess

from tools.benchmark.dn36_head_to_head_v01 import _payload

SCHEMA = "BIOOS_DN36_NATIVE_SCALAR_BENCH_V0_1"
DEFAULT_ITERATIONS = 5000


def _row(receipt: dict[str, object], name: str) -> dict[str, object]:
    rows = receipt.get("performance")
    if not isinstance(rows, list):
        raise RuntimeError("reference benchmark performance rows missing")
    for row in rows:
        if isinstance(row, dict) and row.get("name") == name:
            return row
    raise RuntimeError(f"reference benchmark row missing: {name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument(
        "--reference",
        type=Path,
        default=Path("build/dn36/BIOOS_DN36_HEAD_TO_HEAD_V0_1.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("build/dn36/BIOOS_DN36_NATIVE_SCALAR_BENCH_V0_1.json"),
    )
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    args = parser.parse_args()

    if args.iterations <= 0:
        raise SystemExit("iterations must be positive")
    binary = args.binary.resolve()
    if not binary.is_file():
        raise SystemExit(f"native binary not found: {binary}")
    if not args.reference.is_file():
        raise SystemExit(f"reference receipt not found: {args.reference}")

    payload = _payload(0)
    payload_sha = hashlib.sha256(payload).hexdigest()
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    if reference.get("payload_sha256") != payload_sha:
        raise RuntimeError("native/reference payload mismatch")

    proc = subprocess.run(
        [str(binary), "--bench", str(args.iterations), payload.hex()],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"native benchmark failed rc={proc.returncode}: {proc.stderr.strip()}"
        )
    native = json.loads(proc.stdout)
    if native.get("schema") != "BIOOS_DN36_NATIVE_BENCH_V0_1":
        raise RuntimeError("native benchmark schema mismatch")

    python_dn36 = _row(reference, "dn36_fold256_reference")
    native_ns = float(native["median_ns_per_op"])
    python_ns = float(python_dn36["median_ns_per_op"])
    if native_ns <= 0.0 or python_ns <= 0.0:
        raise RuntimeError("non-positive benchmark latency")

    receipt: dict[str, object] = {
        "schema": SCHEMA,
        "status": "PASS_MEASURED_NATIVE_SCALAR_REFERENCE",
        "payload_bytes": len(payload),
        "payload_sha256": payload_sha,
        "host": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "native": native,
        "python_reference": {
            "name": python_dn36["name"],
            "median_ns_per_op": python_ns,
            "ops_per_s_from_median": python_dn36["ops_per_s_from_median"],
        },
        "native_speedup_vs_python_reference": python_ns / native_ns,
        "security_claim": False,
        "simd_claim": False,
        "canon_allowed": False,
        "claim_boundary": (
            "Same DN36 algorithm and payload on one CI host, comparing scalar C internal-loop "
            "measurement against the Python reference measurement. This is not a SIMD result, "
            "not a standard-hash replacement claim, and not cryptographic validation."
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
