from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from tools.qhtri_spinor_lift_v01 import (
    SpinorLiftStep,
    build_spinor_lift_receipt,
    validate_spinor_lift_receipt,
)

SCHEMA = "BIOOS-QHTRI-LIVE-SPINOR-SIDECAR-ADAPTER/0.1"
STEP_EVIDENCE_SCHEMA = "NOEMA-QHTRI-SPINOR-LIFT-STEP-EVIDENCE/0.1"
EPOCH_SCHEMA = "NOEMA-QHTRI-SPINOR-LIFT-EPOCH/0.3"

SOURCE_NOEMA_SURFACE_SHA256 = "79d11a6b1f147173f6ccdd59187f1b9447f6e015e5858edf8c6634daa8b0e2bd"
SOURCE_CONTINUOUS_PROPAGATOR_SHA256 = "9881e9fede149b2ed74e1085c1bfa516d856f4dfa59268cf2acf7e3ae7243205"
CANDIDATE_NOEMA_SURFACE_SHA256 = "d501d63d038fac53932d418d02a8d108f2f93d6bcbfd56e41fe81a5276198750"
CANDIDATE_CONTINUOUS_PROPAGATOR_SHA256 = "1dcf02f21f0a60999b861c590dc3efaa836a600f0c634dfc5ad6f819fb5ea555"
RUNTIME_PATCH_SHA256 = "2fb4e8e18f3a20eb50b497f3accdc2f2ead10df247175fa6c34f5532b5ab2030"

N_OSCILLATORS = 36
TAU = 2.0 * math.pi
TURNS_FILE = "spinor_turns.i64"
TICK_FILE = "spinor_tick.u64"
EPOCH_FILE = "spinor_lift_epoch.json"
STEP_EVIDENCE_FILE = "spinor_step_evidence.json"


class LiveSpinorSidecarError(ValueError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256(value: Any) -> str:
    return _sha256_bytes(_canonical_bytes(value))


def _hex64(value: Any, name: str) -> str:
    text = str(value)
    if len(text) != 64:
        raise LiveSpinorSidecarError(f"{name} must be 64 hex characters")
    try:
        bytes.fromhex(text)
    except ValueError as exc:
        raise LiveSpinorSidecarError(f"{name} must be hexadecimal") from exc
    return text.lower()


def _finite_vector(value: Sequence[float], name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64).reshape(-1)
    if arr.shape != (N_OSCILLATORS,) or not np.all(np.isfinite(arr)):
        raise LiveSpinorSidecarError(f"{name} must be exactly 36 finite values")
    return arr


def _turns(value: Sequence[int]) -> np.ndarray:
    raw = np.asarray(value)
    if raw.shape != (N_OSCILLATORS,):
        raise LiveSpinorSidecarError("turns must contain exactly 36 values")
    if raw.dtype.kind not in "iu" and not np.all(np.equal(raw, np.rint(raw))):
        raise LiveSpinorSidecarError("turns must be integers")
    return raw.astype(np.int64, copy=False)


def _projected_phase(phi: Sequence[float]) -> np.ndarray:
    return np.mod(_finite_vector(phi, "projective phase"), TAU)


def _phase_commitment(phi: Sequence[float]) -> str:
    arr = np.asarray(_projected_phase(phi), dtype="<f8")
    return _sha256_bytes(arr.tobytes(order="C"))


def _turns_commitment(turns: Sequence[int]) -> str:
    arr = np.asarray(_turns(turns), dtype="<i8")
    return _sha256_bytes(arr.tobytes(order="C"))


def _sheet(turns: Sequence[int]) -> np.ndarray:
    arr = _turns(turns)
    return np.where(np.mod(arr, 2) == 0, 1, -1).astype(np.int8)


def _read_json(path: Path, name: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LiveSpinorSidecarError(f"{name} is unreadable") from exc
    if not isinstance(value, dict):
        raise LiveSpinorSidecarError(f"{name} must be a JSON object")
    return value


def verify_runtime_source_pins(
    *,
    source_noema_surface: str | Path,
    source_continuous_propagator: str | Path,
    candidate_noema_surface: str | Path | None = None,
    candidate_continuous_propagator: str | Path | None = None,
    runtime_patch: str | Path | None = None,
) -> dict[str, str]:
    paths = {
        "source_noema_surface": (Path(source_noema_surface), SOURCE_NOEMA_SURFACE_SHA256),
        "source_continuous_propagator": (
            Path(source_continuous_propagator),
            SOURCE_CONTINUOUS_PROPAGATOR_SHA256,
        ),
    }
    if candidate_noema_surface is not None:
        paths["candidate_noema_surface"] = (
            Path(candidate_noema_surface),
            CANDIDATE_NOEMA_SURFACE_SHA256,
        )
    if candidate_continuous_propagator is not None:
        paths["candidate_continuous_propagator"] = (
            Path(candidate_continuous_propagator),
            CANDIDATE_CONTINUOUS_PROPAGATOR_SHA256,
        )
    if runtime_patch is not None:
        paths["runtime_patch"] = (Path(runtime_patch), RUNTIME_PATCH_SHA256)

    result: dict[str, str] = {}
    for name, (path, expected) in paths.items():
        try:
            actual = _sha256_bytes(path.read_bytes())
        except OSError as exc:
            raise LiveSpinorSidecarError(f"{name} cannot be read") from exc
        if actual != expected:
            raise LiveSpinorSidecarError(
                f"{name} source pin mismatch: {actual} != {expected}"
            )
        result[name] = actual
    return result


def read_same_tick_sidecar(
    *,
    sidecar_root: str | Path,
    qhtri_tick: int,
    projected_phase: Sequence[float],
) -> dict[str, Any]:
    root = Path(sidecar_root)
    turns_path = root / TURNS_FILE
    tick_path = root / TICK_FILE
    epoch_path = root / EPOCH_FILE
    evidence_path = root / STEP_EVIDENCE_FILE

    for path in (turns_path, tick_path, epoch_path, evidence_path):
        if not path.is_file():
            raise LiveSpinorSidecarError(f"missing sidecar file: {path.name}")
    if turns_path.stat().st_size != N_OSCILLATORS * 8:
        raise LiveSpinorSidecarError("spinor turns file size mismatch")
    if tick_path.stat().st_size != 8:
        raise LiveSpinorSidecarError("spinor tick file size mismatch")

    sidecar_tick = int(np.fromfile(tick_path, dtype="<u8", count=1)[0])
    tick = int(qhtri_tick)
    if tick < 0 or sidecar_tick != tick:
        raise LiveSpinorSidecarError(
            f"same-tick sidecar mismatch: {sidecar_tick} != {tick}"
        )
    turns_arr = np.fromfile(turns_path, dtype="<i8", count=N_OSCILLATORS)
    if turns_arr.shape != (N_OSCILLATORS,):
        raise LiveSpinorSidecarError("spinor turns cardinality mismatch")

    epoch = _read_json(epoch_path, "spinor epoch")
    if epoch.get("schema") != EPOCH_SCHEMA:
        raise LiveSpinorSidecarError("spinor epoch schema mismatch")
    epoch_seal = _hex64(epoch.get("epoch_sha256"), "epoch_sha256")
    epoch_body = {k: v for k, v in epoch.items() if k != "epoch_sha256"}
    if epoch_seal != _sha256(epoch_body):
        raise LiveSpinorSidecarError("spinor epoch seal mismatch")

    evidence = _read_json(evidence_path, "spinor step evidence")
    if evidence.get("schema") != STEP_EVIDENCE_SCHEMA:
        raise LiveSpinorSidecarError("spinor step evidence schema mismatch")
    evidence_seal = _hex64(evidence.get("step_evidence_sha256"), "step_evidence_sha256")
    evidence_body = {k: v for k, v in evidence.items() if k != "step_evidence_sha256"}
    if evidence_seal != _sha256(evidence_body):
        raise LiveSpinorSidecarError("spinor step evidence seal mismatch")
    if int(evidence.get("qhtri_tick", -1)) != tick:
        raise LiveSpinorSidecarError("spinor step evidence tick mismatch")
    if evidence.get("epoch_sha256") != epoch_seal:
        raise LiveSpinorSidecarError("spinor step evidence epoch mismatch")
    if evidence.get("turns_sha256") != _turns_commitment(turns_arr):
        raise LiveSpinorSidecarError("spinor step evidence turns mismatch")
    phase = _projected_phase(projected_phase)
    if evidence.get("projective_state_sha256") != _phase_commitment(phase):
        raise LiveSpinorSidecarError("spinor step evidence projective-state mismatch")

    residual = _finite_vector(evidence.get("residual", ()), "residual")
    margin = _finite_vector(evidence.get("uniqueness_margin", ()), "uniqueness_margin")
    if np.any(margin <= 0.0):
        raise LiveSpinorSidecarError("spinor uniqueness margin must be positive")
    operations = evidence.get("generator_operations")
    if not isinstance(operations, list) or not operations:
        raise LiveSpinorSidecarError("spinor generator operations are required")
    for op in operations:
        if not isinstance(op, Mapping) or not str(op.get("kind", "")).strip():
            raise LiveSpinorSidecarError("invalid spinor generator operation")
        _hex64(op.get("increment_sha256"), "increment_sha256")
    expected_generator = _sha256(
        {
            "qhtri_tick": tick,
            "epoch_sha256": epoch_seal,
            "operations": operations,
        }
    )
    if evidence.get("generator_commitment") != expected_generator:
        raise LiveSpinorSidecarError("spinor generator commitment mismatch")

    sheet = _sheet(turns_arr)
    return {
        "schema": SCHEMA,
        "qhtri_tick": tick,
        "epoch_sha256": epoch_seal,
        "step_evidence_sha256": evidence_seal,
        "projected_phase": tuple(float(x) for x in phase),
        "turns": tuple(int(x) for x in turns_arr),
        "spinor_sheet": tuple(int(x) for x in sheet),
        "residual": tuple(float(x) for x in residual),
        "uniqueness_margin": tuple(float(x) for x in margin),
        "generator_commitment": _hex64(
            evidence.get("generator_commitment"), "generator_commitment"
        ),
        "generator_operations": tuple(
            (str(op["kind"]), str(op["increment_sha256"])) for op in operations
        ),
    }


def build_same_tick_spinor_receipt(
    *,
    sidecar_root: str | Path,
    qhtri_tick: int,
    projected_phase: Sequence[float],
    source_evidence_ref: str,
) -> dict[str, Any]:
    state = read_same_tick_sidecar(
        sidecar_root=sidecar_root,
        qhtri_tick=qhtri_tick,
        projected_phase=projected_phase,
    )
    step = SpinorLiftStep(
        projected_phase=state["projected_phase"],
        turns=state["turns"],
        sheet=state["spinor_sheet"],
        residual=state["residual"],
        uniqueness_margin=state["uniqueness_margin"],
    )
    receipt = build_spinor_lift_receipt(
        qhtri_tick=state["qhtri_tick"],
        projective_state_commitment=_phase_commitment(state["projected_phase"]),
        generator_commitment=state["generator_commitment"],
        step=step,
        source_evidence_ref=str(source_evidence_ref).strip(),
    )
    validate_spinor_lift_receipt(receipt)
    return receipt


def publish_same_tick_bifurcation(
    ring: Any,
    *,
    bifurcation_receipt: Mapping[str, Any],
    sidecar_root: str | Path,
    projected_phase: Sequence[float],
    source_evidence_ref: str,
):
    try:
        tick = int(bifurcation_receipt["qhtri_tick"])
    except (KeyError, TypeError, ValueError) as exc:
        raise LiveSpinorSidecarError("bifurcation receipt requires qhtri_tick") from exc
    spinor_receipt = build_same_tick_spinor_receipt(
        sidecar_root=sidecar_root,
        qhtri_tick=tick,
        projected_phase=projected_phase,
        source_evidence_ref=source_evidence_ref,
    )
    record = ring.publish(
        qhtri_tick=tick,
        bifurcation_receipt=bifurcation_receipt,
        spinor_lift_receipt=spinor_receipt,
    )
    if record.event.get("spinor_status") != "PRESENT":
        raise LiveSpinorSidecarError("ring did not preserve PRESENT spinor status")
    if record.event.get("spinor_lift_receipt_sha256") != spinor_receipt["spinor_lift_receipt_sha256"]:
        raise LiveSpinorSidecarError("ring spinor child commitment mismatch")
    return record
