from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import time
from typing import Iterable

SCHEMA = "BIOOS_DELL_ENERGY_PROBE_V0_1"


class DellEnergyProbeError(RuntimeError):
    pass


@dataclass(frozen=True)
class EnergyCounter:
    counter_id: str
    path: str
    energy_uj: int
    max_energy_range_uj: int | None


@dataclass(frozen=True)
class BatteryState:
    name: str
    energy_j: float | None
    power_w: float | None
    status: str | None


@dataclass(frozen=True)
class NvidiaState:
    power_w: float
    temperature_c: float
    utilization_percent: float
    sm_clock_mhz: float
    mem_clock_mhz: float


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    except PermissionError as exc:
        raise DellEnergyProbeError(f"permission denied reading {path}") from exc


def _read_int(path: Path) -> int | None:
    text = _read_text(path)
    if text in (None, ""):
        return None
    try:
        return int(text)
    except ValueError as exc:
        raise DellEnergyProbeError(f"expected integer in {path}, got {text!r}") from exc


def discover_energy_counters(powercap_root: Path = Path("/sys/class/powercap")) -> tuple[EnergyCounter, ...]:
    if not powercap_root.exists():
        return ()
    counters: list[EnergyCounter] = []
    for energy_path in sorted(powercap_root.rglob("energy_uj")):
        directory = energy_path.parent
        energy = _read_int(energy_path)
        if energy is None:
            continue
        name = _read_text(directory / "name") or directory.name
        max_range = _read_int(directory / "max_energy_range_uj")
        counters.append(EnergyCounter(name, str(directory), energy, max_range))
    return tuple(counters)


def counter_delta_j(before: EnergyCounter, after: EnergyCounter) -> float:
    if before.counter_id != after.counter_id or before.path != after.path:
        raise DellEnergyProbeError("energy counter identity mismatch")
    delta = after.energy_uj - before.energy_uj
    if delta < 0:
        max_range = after.max_energy_range_uj or before.max_energy_range_uj
        if max_range is None or max_range <= 0:
            raise DellEnergyProbeError(f"counter wrapped without max range: {after.counter_id}")
        delta += max_range
    if delta < 0:
        raise DellEnergyProbeError(f"invalid negative counter delta: {after.counter_id}")
    return delta / 1_000_000.0


def _micro_units_to_joules(value: int, quantity: str, voltage_uv: int | None = None) -> float | None:
    if quantity == "energy":
        return value * 3600.0 / 1_000_000.0  # micro-Wh -> J
    if quantity == "charge":
        if voltage_uv is None:
            return None
        # micro-Ah * micro-V = 1e-12 Ah*V = 1e-12 Wh; *3600 -> J
        return value * voltage_uv * 3600.0 / 1_000_000_000_000.0
    raise DellEnergyProbeError(f"unknown battery quantity {quantity}")


def _micro_units_to_watts(value: int, quantity: str, voltage_uv: int | None = None) -> float | None:
    if quantity == "power":
        return value / 1_000_000.0
    if quantity == "current":
        if voltage_uv is None:
            return None
        return value * voltage_uv / 1_000_000_000_000.0
    raise DellEnergyProbeError(f"unknown battery power quantity {quantity}")


def discover_batteries(power_supply_root: Path = Path("/sys/class/power_supply")) -> tuple[BatteryState, ...]:
    if not power_supply_root.exists():
        return ()
    out: list[BatteryState] = []
    for directory in sorted(power_supply_root.iterdir()):
        typ = _read_text(directory / "type")
        if typ != "Battery":
            continue
        voltage = _read_int(directory / "voltage_now")
        energy_now = _read_int(directory / "energy_now")
        charge_now = _read_int(directory / "charge_now")
        power_now = _read_int(directory / "power_now")
        current_now = _read_int(directory / "current_now")
        energy_j = None
        if energy_now is not None:
            energy_j = _micro_units_to_joules(energy_now, "energy")
        elif charge_now is not None:
            energy_j = _micro_units_to_joules(charge_now, "charge", voltage)
        power_w = None
        if power_now is not None:
            power_w = _micro_units_to_watts(power_now, "power")
        elif current_now is not None:
            power_w = _micro_units_to_watts(current_now, "current", voltage)
        out.append(BatteryState(directory.name, energy_j, power_w, _read_text(directory / "status")))
    return tuple(out)


def read_ac_online(power_supply_root: Path = Path("/sys/class/power_supply")) -> dict[str, int]:
    if not power_supply_root.exists():
        return {}
    values: dict[str, int] = {}
    for directory in sorted(power_supply_root.iterdir()):
        typ = _read_text(directory / "type")
        if typ in {"Mains", "USB", "USB_C"}:
            online = _read_int(directory / "online")
            if online is not None:
                values[directory.name] = online
    return values


def read_nvidia_state(executable: str = "nvidia-smi") -> NvidiaState | None:
    path = shutil.which(executable)
    if path is None:
        return None
    cmd = [
        path,
        "--query-gpu=power.draw,temperature.gpu,utilization.gpu,clocks.sm,clocks.mem",
        "--format=csv,noheader,nounits",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3.0, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DellEnergyProbeError(f"nvidia telemetry invocation failed: {exc}") from exc
    if proc.returncode != 0:
        return None
    line = proc.stdout.strip().splitlines()
    if not line:
        return None
    parts = [x.strip() for x in line[0].split(",")]
    if len(parts) != 5:
        raise DellEnergyProbeError(f"unexpected nvidia-smi output: {line[0]!r}")
    try:
        vals = [float(x) for x in parts]
    except ValueError as exc:
        raise DellEnergyProbeError(f"non-numeric nvidia-smi output: {line[0]!r}") from exc
    if not all(math.isfinite(x) for x in vals):
        raise DellEnergyProbeError("non-finite nvidia telemetry")
    return NvidiaState(vals[0], vals[1], vals[2], vals[3], vals[4])


def read_live_tick(surface_root: Path = Path("/dev/shm/ciel_noema")) -> int | None:
    tick_path = surface_root / "tick"
    if not tick_path.exists():
        return None
    raw = tick_path.read_bytes()
    if len(raw) < 8:
        raise DellEnergyProbeError("live tick file is shorter than uint64")
    return int.from_bytes(raw[:8], "little", signed=False)


def _index_counters(counters: Iterable[EnergyCounter]) -> dict[tuple[str, str], EnergyCounter]:
    return {(c.counter_id, c.path): c for c in counters}


def sample_session(
    *,
    duration_s: float,
    interval_s: float,
    powercap_root: Path = Path("/sys/class/powercap"),
    power_supply_root: Path = Path("/sys/class/power_supply"),
    surface_root: Path = Path("/dev/shm/ciel_noema"),
) -> dict[str, object]:
    if not math.isfinite(duration_s) or duration_s <= 0.0:
        raise DellEnergyProbeError("duration_s must be finite and > 0")
    if not math.isfinite(interval_s) or interval_s <= 0.0 or interval_s > duration_s:
        raise DellEnergyProbeError("interval_s must be finite, > 0 and <= duration_s")

    counter_before = discover_energy_counters(powercap_root)
    batteries_before = discover_batteries(power_supply_root)
    ac_before = read_ac_online(power_supply_root)
    tick_before = read_live_tick(surface_root)

    nvidia_samples: list[tuple[float, NvidiaState]] = []
    battery_power_samples: list[float] = []
    started = time.monotonic()
    deadline = started + duration_s
    while True:
        now = time.monotonic()
        nv = read_nvidia_state()
        if nv is not None:
            nvidia_samples.append((now, nv))
        for battery in discover_batteries(power_supply_root):
            if battery.power_w is not None:
                battery_power_samples.append(battery.power_w)
        remaining = deadline - time.monotonic()
        if remaining <= 0.0:
            break
        time.sleep(min(interval_s, remaining))
    ended = time.monotonic()

    counter_after = discover_energy_counters(powercap_root)
    batteries_after = discover_batteries(power_supply_root)
    ac_after = read_ac_online(power_supply_root)
    tick_after = read_live_tick(surface_root)

    before_map = _index_counters(counter_before)
    after_map = _index_counters(counter_after)
    rapl_j: dict[str, float] = {}
    for key in sorted(before_map.keys() & after_map.keys()):
        rapl_j[f"{key[0]}@{key[1]}"] = counter_delta_j(before_map[key], after_map[key])

    nvidia_energy_j = None
    if len(nvidia_samples) >= 2:
        total = 0.0
        for (t0, s0), (t1, s1) in zip(nvidia_samples[:-1], nvidia_samples[1:]):
            total += 0.5 * (s0.power_w + s1.power_w) * (t1 - t0)
        nvidia_energy_j = total

    bat_before = {b.name: b for b in batteries_before}
    bat_after = {b.name: b for b in batteries_after}
    battery_delta_j: dict[str, float] = {}
    for name in sorted(bat_before.keys() & bat_after.keys()):
        a = bat_before[name].energy_j
        b = bat_after[name].energy_j
        if a is not None and b is not None:
            battery_delta_j[name] = a - b  # positive means battery energy decreased

    elapsed = ended - started
    return {
        "schema": SCHEMA,
        "elapsed_s": elapsed,
        "tick_start": tick_before,
        "tick_end": tick_after,
        "tick_delta": None if tick_before is None or tick_after is None else tick_after - tick_before,
        "rapl_energy_j": rapl_j,
        "nvidia_energy_j_integrated": nvidia_energy_j,
        "nvidia_sample_count": len(nvidia_samples),
        "battery_energy_delta_j": battery_delta_j,
        "battery_power_w_mean": None if not battery_power_samples else sum(battery_power_samples) / len(battery_power_samples),
        "ac_online_start": ac_before,
        "ac_online_end": ac_after,
        "read_only_hardware_control": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--interval", type=float, default=0.25)
    parser.add_argument("--label", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--surface-root", default="/dev/shm/ciel_noema")
    args = parser.parse_args()

    body = {
        "label": args.label,
        "measurement": sample_session(
            duration_s=args.duration,
            interval_s=args.interval,
            surface_root=Path(args.surface_root),
        ),
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    body["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()
    Path(args.output).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(body, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
