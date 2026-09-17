#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "BIOOS_EMULATION_REFERENCE_RECEIPT_V0_1"


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON object required: {path}")
    return data


def command_value(cmd: list[str], flag: str) -> str:
    try:
        idx = cmd.index(flag)
    except ValueError as exc:
        raise ValueError(f"missing QEMU flag: {flag}") from exc
    if idx + 1 >= len(cmd):
        raise ValueError(f"QEMU flag missing value: {flag}")
    return cmd[idx + 1]


def require_flag(cmd: list[str], flag: str) -> None:
    if flag not in cmd:
        raise ValueError(f"missing QEMU boolean flag: {flag}")


def parse_drive(value: str) -> dict[str, str]:
    parts = value.split(",")
    parsed: dict[str, str] = {}
    for part in parts:
        if "=" not in part:
            raise ValueError(f"unkeyed drive token: {part}")
        k, v = part.split("=", 1)
        if k in parsed:
            raise ValueError(f"duplicate drive token: {k}")
        parsed[k] = v
    return parsed


def validate_command(cmd: list[str], hard: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(cmd, list) or not all(isinstance(x, str) for x in cmd):
        raise ValueError("QEMU command must be list[str]")
    if not cmd:
        raise ValueError("empty QEMU command")

    checks: dict[str, bool] = {}
    checks["machine"] = command_value(cmd, "-machine") == hard["machine"]
    checks["cpu"] = command_value(cmd, "-cpu") == hard["cpu"]
    checks["memory"] = command_value(cmd, "-m") == hard["memory"]
    checks["bios_basename"] = Path(command_value(cmd, "-bios")).name == hard["bios_basename"]
    checks["display"] = command_value(cmd, "-display") == hard["display"]
    checks["serial"] = command_value(cmd, "-serial") == hard["serial"]
    checks["monitor"] = command_value(cmd, "-monitor") == hard["monitor"]
    checks["debugcon"] = command_value(cmd, "-debugcon") == hard["debugcon"]
    checks["debugcon_iobase"] = command_value(cmd, "-global") == f"isa-debugcon.iobase={hard['debugcon_iobase']}"
    require_flag(cmd, "-no-reboot")
    require_flag(cmd, "-no-shutdown")
    checks["no_reboot"] = bool(hard["no_reboot"])
    checks["no_shutdown"] = bool(hard["no_shutdown"])

    drive = parse_drive(command_value(cmd, "-drive"))
    expected_drive = dict(hard["drive"])
    checks["drive_file_present"] = bool(drive.get("file"))
    checks["drive_exact_semantics"] = {k: drive.get(k) for k in expected_drive} == expected_drive
    checks["drive_no_unknown_semantic_tokens"] = set(drive) == set(expected_drive) | {"file"}

    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError(f"QEMU semantic command drift: {failed}")

    return {
        "qemu_executable": cmd[0],
        "machine": command_value(cmd, "-machine"),
        "cpu": command_value(cmd, "-cpu"),
        "memory": command_value(cmd, "-m"),
        "bios_basename": Path(command_value(cmd, "-bios")).name,
        "drive_semantics": {k: drive[k] for k in sorted(expected_drive)},
        "display": command_value(cmd, "-display"),
        "serial": command_value(cmd, "-serial"),
        "monitor": command_value(cmd, "-monitor"),
        "debugcon": command_value(cmd, "-debugcon"),
        "debugcon_iobase": hard["debugcon_iobase"],
        "no_reboot": True,
        "no_shutdown": True,
        "checks": checks,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate BioOS QEMU emulation reference semantics")
    ap.add_argument("--spec", type=Path, default=Path("spec/EMULATION_REFERENCE_SPEC_V0_1.json"))
    ap.add_argument("--build", type=Path, default=Path("provenance/PNSTORE_DNCRYPT_QEMU_BUILD_V0_1.json"))
    ap.add_argument("--conformance", type=Path, default=Path("provenance/PNSTORE_DNCRYPT_QEMU_CONFORMANCE_V0_1.json"))
    ap.add_argument("--adversarial", type=Path, default=Path("provenance/PNSTORE_DNCRYPT_QEMU_ADVERSARIAL_V0_1.json"))
    ap.add_argument("--out", type=Path, default=Path("provenance/EMULATION_REFERENCE_RECEIPT_V0_1.json"))
    args = ap.parse_args()

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "FAIL_CLOSED",
        "canon_allowed": False,
        "physical_machine_claim": False,
        "physical_power_loss_claim": False,
    }

    try:
        spec = load_json(args.spec)
        build = load_json(args.build)
        conf = load_json(args.conformance)
        adv = load_json(args.adversarial)

        if spec.get("schema") != "BIOOS_EMULATION_REFERENCE_SPEC_V0_1":
            raise ValueError("unexpected emulation reference spec schema")
        if spec.get("canon_allowed") is not False:
            raise ValueError("reference spec canon boundary open")
        hard = spec.get("hard_pins")
        if not isinstance(hard, dict):
            raise ValueError("hard_pins missing")

        if build.get("status") != "PASS_HOST_BUILD":
            raise ValueError("PNStore DNCrypt build did not pass")
        if conf.get("status") != "PASS_QEMU_PNSTORE_EXACT_DNCRYPT_ENVELOPE_PERSISTENCE":
            raise ValueError("DNCrypt PNStore conformance did not pass")
        if adv.get("status") != "PASS_QEMU_IDE_ADVERSARIAL_FAIL_CLOSED":
            raise ValueError("PNStore adversarial gate did not pass")

        if int(build.get("pnstore_media_bytes", -1)) != int(hard["pnstore_media_bytes"]):
            raise ValueError("PNStore media geometry drift")
        if int(build.get("pnstore_sector_bytes", -1)) != int(hard["pnstore_sector_bytes"]):
            raise ValueError("PNStore sector geometry drift")
        if build.get("backend") != hard["pnstore_backend"]:
            raise ValueError("PNStore backend drift")

        witnesses: list[dict[str, Any]] = []
        first = conf.get("first_boot")
        second = conf.get("second_boot")
        if not isinstance(first, dict) or not isinstance(second, dict):
            raise ValueError("missing two-boot conformance witnesses")
        witnesses.append({"name": "conformance_first_boot", "semantic": validate_command(first["command"], hard)})
        witnesses.append({"name": "conformance_second_boot", "semantic": validate_command(second["command"], hard)})

        cases = adv.get("cases")
        if not isinstance(cases, list) or not cases:
            raise ValueError("missing adversarial witnesses")
        for case in cases:
            if not isinstance(case, dict) or not isinstance(case.get("boot"), dict):
                raise ValueError("malformed adversarial witness")
            witnesses.append({
                "name": f"adversarial:{case.get('name', 'unnamed')}",
                "semantic": validate_command(case["boot"]["command"], hard),
            })

        conf_qemu = (conf.get("qemu_version"), conf.get("qemu_binary_sha256"), conf.get("qemu_binary"))
        adv_qemu = (adv.get("qemu_version"), adv.get("qemu_binary_sha256"), adv.get("qemu_binary"))
        if conf_qemu != adv_qemu:
            raise ValueError("QEMU provenance differs between conformance and adversarial gates")
        if not all(isinstance(v, str) and v for v in conf_qemu):
            raise ValueError("QEMU provenance incomplete")

        if conf.get("qemu_binary_pinned") is not False or adv.get("qemu_binary_pinned") is not False:
            raise ValueError("unexpected QEMU binary pin-state; update reference policy deliberately")
        record_only = spec.get("record_only")
        if not isinstance(record_only, dict) or record_only.get("qemu_binary_sha256") is not True or record_only.get("qemu_version") is not True:
            raise ValueError("record-only QEMU provenance policy missing")

        payload.update(
            status="PASS_EMULATION_REFERENCE_SEMANTICS",
            spec_schema=spec["schema"],
            spec_sha256=hashlib.sha256(canonical_bytes(spec)).hexdigest(),
            hard_pins=hard,
            record_only_policy=record_only,
            drift_policy=spec.get("drift_policy"),
            witness_count=len(witnesses),
            witnesses=witnesses,
            observed_qemu={
                "version": conf_qemu[0],
                "binary_sha256": conf_qemu[1],
                "binary_path": conf_qemu[2],
                "binary_pin_mode": "RECORD_ONLY",
            },
            observed_toolchain=build.get("tool_versions"),
            source_receipts={
                "build_receipt_sha256": build.get("receipt_sha256"),
                "conformance_receipt_sha256": conf.get("receipt_sha256"),
                "adversarial_receipt_sha256": adv.get("receipt_sha256"),
            },
            claim_boundary=spec.get("claim_boundary"),
            epistemic=spec.get("epistemic", "CHYBA"),
        )
        code = 0
    except Exception as exc:
        payload.update(error_type=type(exc).__name__, error=str(exc))
        code = 2

    core = dict(payload)
    core.pop("receipt_sha256", None)
    payload["receipt_sha256"] = hashlib.sha256(canonical_bytes(core)).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
