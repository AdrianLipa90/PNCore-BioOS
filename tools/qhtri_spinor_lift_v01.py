from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

import numpy as np

SCHEMA = "BIOOS-QHTRI-SPINOR-LIFT/0.1"
TRACKER_ID = "QHTRI.SPINOR.LIFT.NEAREST_GENERATOR_V0_1"
ISOMORPHISM_ID = "ISO.NQ.04.SPINOR.SHEET.WITNESS"
TAU = 2.0 * math.pi


class QhtriSpinorLiftError(ValueError):
    pass


@dataclass(frozen=True)
class SpinorLiftStep:
    projected_phase: tuple[float, ...]
    turns: tuple[int, ...]
    sheet: tuple[int, ...]
    residual: tuple[float, ...]
    uniqueness_margin: tuple[float, ...]


def _finite_vector(value: Sequence[float], name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64).reshape(-1)
    if arr.size == 0 or not np.all(np.isfinite(arr)):
        raise QhtriSpinorLiftError(f"{name} must be a non-empty finite vector")
    return arr


def _turn_vector(value: Sequence[int], size: int) -> np.ndarray:
    arr = np.asarray(value)
    if arr.shape != (size,):
        raise QhtriSpinorLiftError(f"turn vector shape mismatch: {arr.shape} != {(size,)}")
    if arr.dtype.kind not in "iu":
        if not np.all(np.equal(arr, np.rint(arr))):
            raise QhtriSpinorLiftError("turn vector must contain integers")
    return arr.astype(np.int64, copy=False)


def canonical_projective_phase(value: Sequence[float]) -> np.ndarray:
    return np.mod(_finite_vector(value, "projective phase"), TAU)


def sheet_from_turns(turns: Sequence[int]) -> np.ndarray:
    arr = np.asarray(turns, dtype=np.int64).reshape(-1)
    return np.where(np.mod(arr, 2) == 0, 1, -1).astype(np.int8)


def exact_increment_step(
    projected_before: Sequence[float],
    turns_before: Sequence[int],
    increment: Sequence[float],
) -> SpinorLiftStep:
    phase = canonical_projective_phase(projected_before)
    turns = _turn_vector(turns_before, phase.size)
    delta = _finite_vector(increment, "phase increment")
    if delta.shape != phase.shape:
        raise QhtriSpinorLiftError("phase increment shape mismatch")

    raw_local = phase + delta
    delta_turns = np.floor(raw_local / TAU).astype(np.int64)
    projected_after = np.mod(raw_local, TAU)
    turns_after = turns + delta_turns
    sheet = sheet_from_turns(turns_after)
    zeros = np.zeros_like(projected_after)
    margins = np.full_like(projected_after, math.pi)
    return SpinorLiftStep(
        projected_phase=tuple(float(x) for x in projected_after),
        turns=tuple(int(x) for x in turns_after),
        sheet=tuple(int(x) for x in sheet),
        residual=tuple(float(x) for x in zeros),
        uniqueness_margin=tuple(float(x) for x in margins),
    )


def predicted_projected_step(
    projected_before: Sequence[float],
    turns_before: Sequence[int],
    predicted_increment: Sequence[float],
    projected_after: Sequence[float],
    *,
    ambiguity_tolerance: float = 1e-9,
) -> SpinorLiftStep:
    phase_before = canonical_projective_phase(projected_before)
    turns = _turn_vector(turns_before, phase_before.size)
    increment = _finite_vector(predicted_increment, "predicted increment")
    phase_after = canonical_projective_phase(projected_after)
    if increment.shape != phase_before.shape or phase_after.shape != phase_before.shape:
        raise QhtriSpinorLiftError("spinor lift vector shape mismatch")
    if not math.isfinite(ambiguity_tolerance) or ambiguity_tolerance < 0.0 or ambiguity_tolerance >= math.pi:
        raise QhtriSpinorLiftError("ambiguity_tolerance must lie in [0, pi)")

    lift_before = phase_before + TAU * turns.astype(np.float64)
    predicted_lift = lift_before + increment
    turns_after = np.rint((predicted_lift - phase_after) / TAU).astype(np.int64)
    selected_lift = phase_after + TAU * turns_after.astype(np.float64)
    residual = predicted_lift - selected_lift
    margin = math.pi - np.abs(residual)

    if np.any(margin <= ambiguity_tolerance):
        idx = int(np.argmin(margin))
        raise QhtriSpinorLiftError(
            f"spinor lift is ambiguous at index {idx}: uniqueness margin {margin[idx]:.17g}"
        )

    sheet = sheet_from_turns(turns_after)
    return SpinorLiftStep(
        projected_phase=tuple(float(x) for x in phase_after),
        turns=tuple(int(x) for x in turns_after),
        sheet=tuple(int(x) for x in sheet),
        residual=tuple(float(x) for x in residual),
        uniqueness_margin=tuple(float(x) for x in margin),
    )


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _hex64(value: Any, name: str) -> str:
    text = str(value)
    if len(text) != 64:
        raise QhtriSpinorLiftError(f"{name} must be 64 hex characters")
    try:
        bytes.fromhex(text)
    except ValueError as exc:
        raise QhtriSpinorLiftError(f"{name} must be hexadecimal") from exc
    return text.lower()


def build_spinor_lift_receipt(
    *,
    qhtri_tick: int,
    projective_state_commitment: str,
    generator_commitment: str,
    step: SpinorLiftStep,
    source_evidence_ref: str,
) -> dict[str, Any]:
    tick = int(qhtri_tick)
    if tick < 0:
        raise QhtriSpinorLiftError("qhtri_tick must be non-negative")
    if len(step.projected_phase) != len(step.turns) or len(step.turns) != len(step.sheet):
        raise QhtriSpinorLiftError("spinor lift step cardinality mismatch")
    if tuple(int(x) for x in sheet_from_turns(step.turns)) != tuple(step.sheet):
        raise QhtriSpinorLiftError("spinor sheet/turn parity mismatch")
    if not str(source_evidence_ref).strip():
        raise QhtriSpinorLiftError("source_evidence_ref is required")

    body = {
        "schema": SCHEMA,
        "tracker_id": TRACKER_ID,
        "isomorphism_id": ISOMORPHISM_ID,
        "qhtri_tick": tick,
        "projective_state_commitment": _hex64(projective_state_commitment, "projective_state_commitment"),
        "generator_commitment": _hex64(generator_commitment, "generator_commitment"),
        "projected_phase": list(step.projected_phase),
        "turns": list(step.turns),
        "spinor_sheet": list(step.sheet),
        "residual": list(step.residual),
        "uniqueness_margin": list(step.uniqueness_margin),
        "source_evidence_ref": str(source_evidence_ref).strip(),
        "source_class": "NATURAL_SYSTEM_STATE",
        "dynamics_class": "ENDOGENOUS_RUNTIME_DYNAMICS",
        "evidence_status": "GREMLIN_STRUCTURAL_CANDIDATE",
    }
    seal = hashlib.sha256(_canonical_bytes(body)).hexdigest()
    return {**body, "spinor_lift_receipt_sha256": seal}


def validate_spinor_lift_receipt(receipt: Mapping[str, Any]) -> None:
    if receipt.get("schema") != SCHEMA or receipt.get("tracker_id") != TRACKER_ID:
        raise QhtriSpinorLiftError("spinor lift receipt schema/tracker mismatch")
    if receipt.get("isomorphism_id") != ISOMORPHISM_ID:
        raise QhtriSpinorLiftError("spinor lift receipt isomorphism mismatch")
    _hex64(receipt.get("projective_state_commitment"), "projective_state_commitment")
    _hex64(receipt.get("generator_commitment"), "generator_commitment")
    turns = tuple(int(x) for x in receipt.get("turns", ()))
    sheet = tuple(int(x) for x in receipt.get("spinor_sheet", ()))
    if not turns or sheet != tuple(int(x) for x in sheet_from_turns(turns)):
        raise QhtriSpinorLiftError("spinor sheet/turn parity mismatch")
    for key in ("projected_phase", "residual", "uniqueness_margin"):
        arr = _finite_vector(receipt.get(key, ()), key)
        if arr.size != len(turns):
            raise QhtriSpinorLiftError(f"{key} cardinality mismatch")
    if any(float(x) <= 0.0 for x in receipt.get("uniqueness_margin", ())):
        raise QhtriSpinorLiftError("non-positive spinor lift uniqueness margin")
    body = {key: value for key, value in receipt.items() if key != "spinor_lift_receipt_sha256"}
    expected = hashlib.sha256(_canonical_bytes(body)).hexdigest()
    if receipt.get("spinor_lift_receipt_sha256") != expected:
        raise QhtriSpinorLiftError("spinor lift receipt seal mismatch")
