from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import time

from tools.dn36_fundamental_vector_commit_v01 import commit

PAYLOAD_BYTES = 288
TRIALS = 5
STD_ITERATIONS = 100_000
DN36_ITERATIONS = 100
AVALANCHE_BITS = 256
BIAS_POPULATION = 128
COLLISION_POPULATION = 512


def _payload(seed: int = 0) -> bytes:
    if seed < 0:
        raise ValueError("seed must be non-negative")
    return hashlib.shake_256(
        b"BIOOS/DN36/BENCH/PAYLOAD/V0.1|" + seed.to_bytes(8, "big")
    ).digest(PAYLOAD_BYTES)


def _bench(name: str, fn, iterations: int) -> dict[str, float | int | str]:
    samples = []
    sink = 0
    for _ in range(TRIALS):
        start = time.perf_counter_ns()
        for _ in range(iterations):
            sink ^= fn()[0]
        elapsed = time.perf_counter_ns() - start
        samples.append(elapsed / iterations)
    median_ns = statistics.median(samples)
    return {
        "name": name,
        "iterations_per_trial": iterations,
        "trials": TRIALS,
        "min_ns_per_op": min(samples),
        "median_ns_per_op": median_ns,
        "max_ns_per_op": max(samples),
        "median_us_per_op": median_ns / 1000.0,
        "ops_per_s_from_median": 1e9 / median_ns,
        "gb_per_s_288B_from_median": (PAYLOAD_BYTES / median_ns),
        "sink": sink,
    }


def _hamming(a: bytes, b: bytes) -> int:
    return sum((x ^ y).bit_count() for x, y in zip(a, b))


def _avalanche() -> dict[str, object]:
    base = bytearray(_payload(3))
    reference = commit(bytes(base)).fold256
    fractions = []
    for bit_index in range(AVALANCHE_BITS):
        mutated = bytearray(base)
        mutated[bit_index // 8] ^= 1 << (bit_index % 8)
        fractions.append(_hamming(reference, commit(bytes(mutated)).fold256) / 256.0)
    return {
        "input_bit_flips": AVALANCHE_BITS,
        "mean_changed_fraction": statistics.mean(fractions),
        "median_changed_fraction": statistics.median(fractions),
        "min_changed_fraction": min(fractions),
        "max_changed_fraction": max(fractions),
        "mean_changed_bits": statistics.mean(fractions) * 256.0,
    }


def _output_bit_bias() -> dict[str, object]:
    counts = [0] * 256
    for index in range(BIAS_POPULATION):
        digest = commit(_payload(index)).fold256
        for bit in range(256):
            counts[bit] += (digest[bit // 8] >> (bit % 8)) & 1
    fractions = [value / BIAS_POPULATION for value in counts]
    biases = [abs(value - 0.5) for value in fractions]
    return {
        "population": BIAS_POPULATION,
        "mean_one_fraction": statistics.mean(fractions),
        "mean_abs_bias_from_half": statistics.mean(biases),
        "max_abs_bias_from_half": max(biases),
    }


def _duplicate_search() -> dict[str, object]:
    seen_inputs: set[bytes] = set()
    seen_state: dict[bytes, int] = {}
    seen_fold: dict[bytes, int] = {}
    seen_anchor: dict[bytes, int] = {}
    duplicate_state = 0
    duplicate_fold = 0
    duplicate_anchor = 0
    first_state_pairs: list[list[int]] = []
    first_fold_pairs: list[list[int]] = []
    first_anchor_pairs: list[list[int]] = []

    for index in range(COLLISION_POPULATION):
        seed = index + 1000
        payload = _payload(seed)
        if payload in seen_inputs:
            raise RuntimeError("benchmark payload generator produced a duplicate input")
        seen_inputs.add(payload)
        result = commit(payload)

        for output, seen, pairs, kind in (
            (result.state2304, seen_state, first_state_pairs, "state"),
            (result.fold256, seen_fold, first_fold_pairs, "fold"),
            (result.anchor256, seen_anchor, first_anchor_pairs, "anchor"),
        ):
            previous = seen.get(output)
            if previous is not None:
                if kind == "state":
                    duplicate_state += 1
                elif kind == "fold":
                    duplicate_fold += 1
                else:
                    duplicate_anchor += 1
                if len(pairs) < 16:
                    pairs.append([previous, seed])
            else:
                seen[output] = seed

    return {
        "population": COLLISION_POPULATION,
        "unique_input_count": len(seen_inputs),
        "unique_state2304_count": len(seen_state),
        "duplicate_state2304_count": duplicate_state,
        "unique_fold256_count": len(seen_fold),
        "duplicate_fold256_count": duplicate_fold,
        "unique_anchor256_count": len(seen_anchor),
        "duplicate_anchor256_count": duplicate_anchor,
        "first_state_collision_seed_pairs": first_state_pairs,
        "first_fold_collision_seed_pairs": first_fold_pairs,
        "first_anchor_collision_seed_pairs": first_anchor_pairs,
        "claim": "SMALL_POPULATION_DUPLICATE_SEARCH_ONLY_NOT_COLLISION_SECURITY",
    }


def main() -> int:
    payload = _payload()
    rows = [
        _bench("sha256_python_openssl", lambda: hashlib.sha256(payload).digest(), STD_ITERATIONS),
        _bench("blake2b256_python", lambda: hashlib.blake2b(payload, digest_size=32).digest(), STD_ITERATIONS),
        _bench("sha3_256_python", lambda: hashlib.sha3_256(payload).digest(), STD_ITERATIONS),
        _bench("dn36_fold256_reference", lambda: commit(payload).fold256, DN36_ITERATIONS),
        _bench("dn36_anchor256_reference", lambda: commit(payload).anchor256, DN36_ITERATIONS),
    ]
    reference = next(row for row in rows if row["name"] == "sha256_python_openssl")
    sha_ns = float(reference["median_ns_per_op"])
    for row in rows:
        row["latency_ratio_vs_sha256"] = float(row["median_ns_per_op"]) / sha_ns
        row["speed_ratio_vs_sha256"] = sha_ns / float(row["median_ns_per_op"])

    duplicate_search = _duplicate_search()
    duplicate_gate_pass = (
        duplicate_search["unique_input_count"] == COLLISION_POPULATION
        and duplicate_search["unique_state2304_count"] == COLLISION_POPULATION
        and duplicate_search["unique_fold256_count"] == COLLISION_POPULATION
        and duplicate_search["unique_anchor256_count"] == COLLISION_POPULATION
        and duplicate_search["duplicate_state2304_count"] == 0
        and duplicate_search["duplicate_fold256_count"] == 0
        and duplicate_search["duplicate_anchor256_count"] == 0
    )

    receipt = {
        "schema": "BIOOS_DN36_HEAD_TO_HEAD_V0_1",
        "status": "MEASURED_EXPERIMENTAL_REFERENCE" if duplicate_gate_pass else "FAIL_DUPLICATE_GATE",
        "epistemic": "CHYBA",
        "canon_allowed": False,
        "security_claim": False,
        "replacement_for_standard_hash": False,
        "payload_bytes": PAYLOAD_BYTES,
        "payload_generator": "SHAKE256(domain || uint64_be(seed)) -> 288 bytes",
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "host": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "source_pins": {
            "dncrypt_commit": "20f53a9b297b6208d74841aee7c3bb4b8b17ce2a",
            "tir_commit": "45b54c0c8aa60ec92607e6132b69aca9ab766d75",
            "resonant_chemistry_commit": "6a9f21678ba4f07e5bdbb1a98a0cafe5c4838697",
        },
        "performance": rows,
        "avalanche_sample": _avalanche(),
        "output_bit_bias_sample": _output_bit_bias(),
        "duplicate_search": duplicate_search,
        "duplicate_gate_pass": duplicate_gate_pass,
        "claim_boundary": (
            "Python reference implementation benchmark and small statistical probes only; "
            "not native/SIMD performance, not cryptanalytic validation, not a secure-hash claim"
        ),
    }
    raw = json.dumps(receipt, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    receipt["receipt_sha256"] = hashlib.sha256(raw).hexdigest()

    out = Path(os.environ.get("DN36_BENCHMARK_OUT", "build/dn36/BIOOS_DN36_HEAD_TO_HEAD_V0_1.json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if duplicate_gate_pass else 5


if __name__ == "__main__":
    raise SystemExit(main())
