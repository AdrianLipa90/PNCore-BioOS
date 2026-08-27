from __future__ import annotations

import math
from typing import Sequence

DIM = 36


class QHTRIPhaseLogicError(ValueError):
    pass


def _finite(x: float, name: str) -> float:
    v = float(x)
    if not math.isfinite(v):
        raise QHTRIPhaseLogicError(f"{name} must be finite")
    return v


def wrap_phase(theta: float) -> float:
    x = _finite(theta, "phase")
    return (x + math.pi) % (2.0 * math.pi) - math.pi


def coherence_truth(delta: float) -> float:
    """Continuous phase-coherence truth: cos^2(delta/2)."""
    d = wrap_phase(delta)
    return 0.5 * (1.0 + math.cos(d))


def phase_not(theta: float) -> float:
    return wrap_phase(theta + math.pi)


def phase_xnor(theta_a: float, theta_b: float) -> float:
    return coherence_truth(wrap_phase(theta_a - theta_b))


def phase_xor(theta_a: float, theta_b: float) -> float:
    return 1.0 - phase_xnor(theta_a, theta_b)


def coherence_and(a: float, b: float) -> float:
    aa = min(1.0, max(0.0, _finite(a, "a")))
    bb = min(1.0, max(0.0, _finite(b, "b")))
    return aa * bb


def coherence_or(a: float, b: float) -> float:
    aa = min(1.0, max(0.0, _finite(a, "a")))
    bb = min(1.0, max(0.0, _finite(b, "b")))
    return aa + bb - aa * bb


def boolean_phase(value: bool | int) -> float:
    if value in (1, True):
        return 0.0
    if value in (0, False):
        return math.pi
    raise QHTRIPhaseLogicError("boolean phase adapter accepts only 0/1")


def vector_phase_not(theta: Sequence[float]) -> tuple[float, ...]:
    if len(theta) != DIM:
        raise QHTRIPhaseLogicError("T36 phase logic requires exactly 36 lanes")
    return tuple(phase_not(v) for v in theta)


def vector_xnor(theta_a: Sequence[float], theta_b: Sequence[float]) -> tuple[float, ...]:
    if len(theta_a) != DIM or len(theta_b) != DIM:
        raise QHTRIPhaseLogicError("T36 phase logic requires exactly 36 lanes")
    return tuple(phase_xnor(a, b) for a, b in zip(theta_a, theta_b))


def vector_xor(theta_a: Sequence[float], theta_b: Sequence[float]) -> tuple[float, ...]:
    if len(theta_a) != DIM or len(theta_b) != DIM:
        raise QHTRIPhaseLogicError("T36 phase logic requires exactly 36 lanes")
    return tuple(phase_xor(a, b) for a, b in zip(theta_a, theta_b))


def equatorial_cp1_overlap_squared(theta_a: float, theta_b: float) -> float:
    """Squared overlap for |psi(theta)>=(|0>+e^{i theta}|1>)/sqrt(2)."""
    return coherence_truth(wrap_phase(theta_a - theta_b))
