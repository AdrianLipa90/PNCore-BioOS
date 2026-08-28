from pathlib import Path

import pytest

from tools.bioos_dell_energy_probe_v01 import (
    BatteryState,
    DellEnergyProbeError,
    EnergyCounter,
    counter_delta_j,
    discover_batteries,
    discover_energy_counters,
    read_ac_online,
    read_live_tick,
)


def _write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_rapl_discovery_and_wrap_delta(tmp_path):
    d = tmp_path / "intel-rapl:0"
    _write(d / "name", "package-0\n")
    _write(d / "energy_uj", "950\n")
    _write(d / "max_energy_range_uj", "1000\n")
    found = discover_energy_counters(tmp_path)
    assert len(found) == 1
    assert found[0].counter_id == "package-0"
    before = found[0]
    after = EnergyCounter(before.counter_id, before.path, 25, 1000)
    assert counter_delta_j(before, after) == pytest.approx(75e-6)


def test_counter_identity_mismatch_fails():
    a = EnergyCounter("a", "/a", 1, 100)
    b = EnergyCounter("b", "/b", 2, 100)
    with pytest.raises(DellEnergyProbeError, match="identity mismatch"):
        counter_delta_j(a, b)


def test_battery_energy_now_and_power_now(tmp_path):
    b = tmp_path / "BAT0"
    _write(b / "type", "Battery\n")
    _write(b / "energy_now", "50000000\n")  # 50 Wh
    _write(b / "power_now", "20000000\n")    # 20 W
    _write(b / "status", "Discharging\n")
    found = discover_batteries(tmp_path)
    assert found == (BatteryState("BAT0", pytest.approx(180000.0), pytest.approx(20.0), "Discharging"),)


def test_battery_charge_voltage_fallback(tmp_path):
    b = tmp_path / "BAT0"
    _write(b / "type", "Battery\n")
    _write(b / "charge_now", "4000000\n")
    _write(b / "voltage_now", "12000000\n")
    _write(b / "current_now", "1000000\n")
    state = discover_batteries(tmp_path)[0]
    assert state.energy_j == pytest.approx(172800.0)  # 4 Ah * 12 V * 3600
    assert state.power_w == pytest.approx(12.0)


def test_ac_online(tmp_path):
    a = tmp_path / "AC"
    _write(a / "type", "Mains\n")
    _write(a / "online", "1\n")
    assert read_ac_online(tmp_path) == {"AC": 1}


def test_live_tick_reads_uint64(tmp_path):
    (tmp_path / "tick").write_bytes((123456789).to_bytes(8, "little"))
    assert read_live_tick(tmp_path) == 123456789


def test_live_tick_short_file_fails(tmp_path):
    (tmp_path / "tick").write_bytes(b"1234")
    with pytest.raises(DellEnergyProbeError, match="shorter"):
        read_live_tick(tmp_path)
