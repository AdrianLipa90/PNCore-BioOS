from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import time
from typing import Any


SCHEMA = "CQCL-LIVE-HTRI-BINDING/0.1"
SOURCE_CLASS = "NATURAL_SYSTEM_STATE"
RUNTIME_DYNAMICS = "ENDOGENOUS_RUNTIME_DYNAMICS"
SOURCE_CONTRACT = "NOEMA_QHTRI_DIRECT_TELEMETRY_BIND_V0_1"
DIM = 36
FRAME_BYTES = DIM * 8
DOMAIN = b"CQCL-LIVE-HTRI-BINDING/v0.1\x00"


class QHTRICQCLBridgeError(ValueError):
    pass


def _read_f64x36(path: Path, name: str) -> tuple[bytes, tuple[float, ...]]:
    raw = path.read_bytes()
    if len(raw) != FRAME_BYTES:
        raise QHTRICQCLBridgeError(f"{name} must be exactly {FRAME_BYTES} bytes")
    values = struct.unpack("<36d", raw)
    if not all(math.isfinite(x) for x in values):
        raise QHTRICQCLBridgeError(f"{name} contains non-finite values")
    return raw, values


def _read_tick(path: Path) -> int:
    raw = path.read_bytes()
    if len(raw) != 8:
        raise QHTRICQCLBridgeError("tick must be exactly uint64-le")
    return struct.unpack("<Q", raw)[0]


def _read_json(path: Path, name: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QHTRICQCLBridgeError(f"cannot read {name}") from exc
    if not isinstance(value, dict):
        raise QHTRICQCLBridgeError(f"{name} root must be object")
    return value


def _hex32(value: str, name: str) -> str:
    v = str(value).lower()
    if len(v) != 64:
        raise QHTRICQCLBridgeError(f"{name} must encode 32 bytes")
    try:
        bytes.fromhex(v)
    except ValueError as exc:
        raise QHTRICQCLBridgeError(f"{name} must be hex") from exc
    return v


def _kuramoto_coherence(phi: tuple[float, ...]) -> float:
    c = math.fsum(math.cos(x) for x in phi) / DIM
    s = math.fsum(math.sin(x) for x in phi) / DIM
    r = math.hypot(c, s)
    return min(1.0, max(0.0, r))


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _stable_frame(phi_path: Path, omega_path: Path, tick_path: Path) -> tuple[int, bytes, tuple[float, ...], bytes, tuple[float, ...]]:
    for _ in range(16):
        t0 = _read_tick(tick_path)
        phi_raw, phi = _read_f64x36(phi_path, "phi")
        omega_raw, omega = _read_f64x36(omega_path, "omega")
        t1 = _read_tick(tick_path)
        if t0 == t1:
            return t1, phi_raw, phi, omega_raw, omega
    raise QHTRICQCLBridgeError("could not acquire a stable QHTRI frame")


def observe_live_qhtri(
    root: str | Path = "/dev/shm/ciel_noema",
    *,
    samples: int = 4,
    poll_interval_s: float = 0.01,
    max_wait_s: float = 2.0,
    max_heartbeat_age_ms: float = 1000.0,
    now_ns: int | None = None,
) -> dict[str, Any]:
    if samples < 2:
        raise QHTRICQCLBridgeError("at least two distinct tick samples are required")
    if poll_interval_s < 0 or not math.isfinite(poll_interval_s):
        raise QHTRICQCLBridgeError("poll_interval_s must be finite and non-negative")
    if max_wait_s <= 0 or not math.isfinite(max_wait_s):
        raise QHTRICQCLBridgeError("max_wait_s must be finite and positive")
    if max_heartbeat_age_ms <= 0 or not math.isfinite(max_heartbeat_age_ms):
        raise QHTRICQCLBridgeError("max heartbeat age must be finite and positive")

    surface = Path(root)
    phi_path = surface / "phi"
    omega_path = surface / "omega"
    tick_path = surface / "tick"
    tether_path = surface / "tether_runtime_status.json"

    observations: list[tuple[int, bytes, tuple[float, ...], bytes, tuple[float, ...]]] = []
    last_tick: int | None = None
    deadline = time.monotonic() + max_wait_s
    while len(observations) < samples:
        frame = _stable_frame(phi_path, omega_path, tick_path)
        tick = frame[0]
        if last_tick is None or tick > last_tick:
            observations.append(frame)
            last_tick = tick
        elif tick < last_tick:
            raise QHTRICQCLBridgeError("QHTRI tick regressed")
        if len(observations) >= samples:
            break
        if time.monotonic() >= deadline:
            raise QHTRICQCLBridgeError("timed out waiting for distinct QHTRI ticks")
        if poll_interval_s:
            time.sleep(poll_interval_s)

    ticks = [x[0] for x in observations]
    if any(b <= a for a, b in zip(ticks, ticks[1:])):
        raise QHTRICQCLBridgeError("QHTRI tick did not increase strictly")
    phi_hashes = [hashlib.sha256(x[1]).hexdigest() for x in observations]
    if len(set(phi_hashes)) < 2:
        raise QHTRICQCLBridgeError("QHTRI phi did not change over observation window")
    omega_hashes = [hashlib.sha256(x[3]).hexdigest() for x in observations]
    if len(set(omega_hashes)) != 1:
        raise QHTRICQCLBridgeError("QHTRI omega changed over observation window")

    final_tick, final_phi_raw, final_phi, final_omega_raw, final_omega = observations[-1]
    if not any(x != 0.0 for x in final_omega):
        raise QHTRICQCLBridgeError("QHTRI omega must be nonzero")

    tether = _read_json(tether_path, "tether runtime status")
    if tether.get("schema") != "noema.tether-runtime-status/v1" or tether.get("status") != "ACTIVE":
        raise QHTRICQCLBridgeError("tether is not ACTIVE")
    heartbeat_ns = int(tether.get("heartbeat_ns", 0))
    observed_ns = time.time_ns() if now_ns is None else int(now_ns)
    heartbeat_age_ms = max(0.0, (observed_ns - heartbeat_ns) / 1_000_000.0)
    if heartbeat_ns <= 0 or heartbeat_age_ms > max_heartbeat_age_ms:
        raise QHTRICQCLBridgeError("tether heartbeat is stale")
    tether_receipt = _hex32(tether.get("receipt_sha256", ""), "tether receipt")

    identity_evidence = {
        "source_contract": SOURCE_CONTRACT,
        "tick_start": ticks[0],
        "tick_end": final_tick,
        "sample_count": samples,
        "phi_sha256": hashlib.sha256(final_phi_raw).hexdigest(),
        "omega_sha256": hashlib.sha256(final_omega_raw).hexdigest(),
        "tether_receipt_sha256": tether_receipt,
        "tether_seq": int(tether.get("seq", 0)),
    }
    generation_id = hashlib.sha256(DOMAIN + _canonical(identity_evidence)).hexdigest()
    return {
        "schema": SCHEMA,
        "source_class": SOURCE_CLASS,
        "runtime_dynamics": RUNTIME_DYNAMICS,
        "generation_id": generation_id,
        "coherence": _kuramoto_coherence(final_phi),
        "heartbeat_age_ms": heartbeat_age_ms,
        "max_heartbeat_age_ms": float(max_heartbeat_age_ms),
        "live": True,
        "authority_grant": False,
        "evidence": {
            **identity_evidence,
            "source_root_view": str(surface),
            "identity_depends_on_path": False,
        },
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="/dev/shm/ciel_noema")
    p.add_argument("--samples", type=int, default=4)
    p.add_argument("--poll-ms", type=float, default=10.0)
    p.add_argument("--max-wait-ms", type=float, default=2000.0)
    p.add_argument("--max-heartbeat-age-ms", type=float, default=1000.0)
    p.add_argument("--out")
    args = p.parse_args()
    result = observe_live_qhtri(
        args.root,
        samples=args.samples,
        poll_interval_s=args.poll_ms / 1000.0,
        max_wait_s=args.max_wait_ms / 1000.0,
        max_heartbeat_age_ms=args.max_heartbeat_age_ms,
    )
    raw = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        Path(args.out).write_text(raw, encoding="utf-8")
    else:
        print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
