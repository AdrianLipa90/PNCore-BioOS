from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence

import numpy as np

SCHEMA = "BIOOS_ZPE_NORMALIZED_COMPUTE_V0_1"
ZPE_REPOSITORY = "AdrianLipa90/Zero-Point-Energy"
ZPE_PIN = "43b981fc9f350ba6e8a8d6c846e4be52737f941d"
CONTROL_STATUS = "EXPERIMENTAL_CONTROL"


class ZPENormalizedComputeError(ValueError):
    pass


@dataclass(frozen=True)
class RelationalTolerance:
    overlap_min: float
    phase_rms_max: float
    phase_max_max: float
    coupling_direction_max: float
    coupling_log_scale_max: float
    require_winding_exact: bool

    def __post_init__(self) -> None:
        vals = (
            self.overlap_min,
            self.phase_rms_max,
            self.phase_max_max,
            self.coupling_direction_max,
            self.coupling_log_scale_max,
        )
        if not all(math.isfinite(float(v)) for v in vals):
            raise ZPENormalizedComputeError("relational tolerances must be finite")
        if not 0.0 <= self.overlap_min <= 1.0:
            raise ZPENormalizedComputeError("overlap_min must lie in [0,1]")
        if min(self.phase_rms_max, self.phase_max_max, self.coupling_direction_max, self.coupling_log_scale_max) < 0.0:
            raise ZPENormalizedComputeError("error tolerances must be non-negative")
        if not isinstance(self.require_winding_exact, bool):
            raise ZPENormalizedComputeError("require_winding_exact must be bool")


@dataclass(frozen=True)
class RelationalMetrics:
    normalized_overlap_sq: float
    phase_relation_rms: float
    phase_relation_max: float
    coupling_direction_error: float
    coupling_log_scale_error: float
    winding_ref: int
    winding_candidate: int

    @property
    def winding_equal(self) -> bool:
        return self.winding_ref == self.winding_candidate


@dataclass(frozen=True)
class EventGatePolicy:
    phase_rms_wake: float
    overlap_floor_wake: float
    max_silence_ticks: int

    def __post_init__(self) -> None:
        if not math.isfinite(float(self.phase_rms_wake)) or self.phase_rms_wake <= 0.0:
            raise ZPENormalizedComputeError("phase_rms_wake must be finite and > 0")
        if not math.isfinite(float(self.overlap_floor_wake)) or not 0.0 <= self.overlap_floor_wake <= 1.0:
            raise ZPENormalizedComputeError("overlap_floor_wake must lie in [0,1]")
        if isinstance(self.max_silence_ticks, bool) or int(self.max_silence_ticks) != self.max_silence_ticks or self.max_silence_ticks < 1:
            raise ZPENormalizedComputeError("max_silence_ticks must be a positive integer")


@dataclass(frozen=True)
class EventGateDecision:
    wake_noema: bool
    reasons: tuple[str, ...]
    silence_ticks: int
    phase_relation_rms: float
    normalized_overlap_sq: float


@dataclass(frozen=True)
class CandidateScore:
    candidate_id: str
    admitted: bool
    compute_work_proxy: float
    metrics: RelationalMetrics
    calls: int
    reference_calls: int

    @property
    def call_reduction_fraction(self) -> float:
        if self.reference_calls <= 0:
            raise ZPENormalizedComputeError("reference_calls must be positive")
        return 1.0 - self.calls / self.reference_calls


def _require_vector(name: str, values: Sequence[float]) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    if arr.ndim != 1 or arr.size == 0:
        raise ZPENormalizedComputeError(f"{name} must be a non-empty 1D vector")
    if not np.all(np.isfinite(arr)):
        raise ZPENormalizedComputeError(f"{name} must be finite")
    return arr


def _require_square(name: str, values: Sequence[Sequence[float]], n: int) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    if arr.shape != (n, n):
        raise ZPENormalizedComputeError(f"{name} must have shape {(n,n)}, got {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ZPENormalizedComputeError(f"{name} must be finite")
    return arr


def normalized_overlap_sq(S: Sequence[complex], I: Sequence[complex]) -> float:
    """Pinned ZPE relation R(S,I)=|<S|I>|^2/(||S||^2 ||I||^2)."""
    a = np.asarray(S, dtype=np.complex128)
    b = np.asarray(I, dtype=np.complex128)
    if a.ndim != 1 or b.ndim != 1 or a.shape != b.shape or a.size == 0:
        raise ZPENormalizedComputeError("S and I must have equal non-zero 1D shape")
    if not np.all(np.isfinite(a.real)) or not np.all(np.isfinite(a.imag)) or not np.all(np.isfinite(b.real)) or not np.all(np.isfinite(b.imag)):
        raise ZPENormalizedComputeError("S and I must be finite")
    na = float(np.vdot(a, a).real)
    nb = float(np.vdot(b, b).real)
    if na <= 0.0 or nb <= 0.0:
        raise ZPENormalizedComputeError("S and I must have non-zero norm")
    return float(abs(np.vdot(a, b)) ** 2 / (na * nb))


def phase_relation_matrix(phi: Sequence[float]) -> np.ndarray:
    """Gauge-invariant U_ij=exp(i(phi_j-phi_i))."""
    p = _require_vector("phi", phi)
    return np.exp(1j * (p[None, :] - p[:, None]))


def surface_winding(phi: Sequence[float]) -> int:
    p = _require_vector("phi", phi)
    d = np.empty_like(p)
    np.subtract(p[1:], p[:-1], out=d[:-1])
    d[-1] = p[0] - p[-1]
    d = (d + np.pi) % (2.0 * np.pi) - np.pi
    return int(round(float(np.sum(d)) / (2.0 * np.pi)))


def relational_metrics(
    phi_ref: Sequence[float],
    g_ref: Sequence[Sequence[float]],
    phi_candidate: Sequence[float],
    g_candidate: Sequence[Sequence[float]],
) -> RelationalMetrics:
    pr = _require_vector("phi_ref", phi_ref)
    pc = _require_vector("phi_candidate", phi_candidate)
    if pr.shape != pc.shape:
        raise ZPENormalizedComputeError("phase vectors must have equal shape")
    n = pr.size
    gr = _require_square("g_ref", g_ref, n).copy()
    gc = _require_square("g_candidate", g_candidate, n).copy()

    zr = np.exp(1j * pr)
    zc = np.exp(1j * pc)
    overlap = normalized_overlap_sq(zr, zc)

    ur = phase_relation_matrix(pr)
    uc = phase_relation_matrix(pc)
    phase_err = np.angle(uc * np.conjugate(ur))
    mask = ~np.eye(n, dtype=bool)
    phase_rms = float(np.sqrt(np.mean(phase_err[mask] ** 2)))
    phase_max = float(np.max(np.abs(phase_err[mask])))

    np.fill_diagonal(gr, 0.0)
    np.fill_diagonal(gc, 0.0)
    nr = float(np.linalg.norm(gr))
    nc = float(np.linalg.norm(gc))
    if nr <= 0.0 or nc <= 0.0:
        raise ZPENormalizedComputeError("off-diagonal coupling norm must be positive")
    coupling_direction = float(np.linalg.norm(gr / nr - gc / nc))
    coupling_log_scale = abs(math.log(nc / nr))

    return RelationalMetrics(
        normalized_overlap_sq=overlap,
        phase_relation_rms=phase_rms,
        phase_relation_max=phase_max,
        coupling_direction_error=coupling_direction,
        coupling_log_scale_error=coupling_log_scale,
        winding_ref=surface_winding(pr),
        winding_candidate=surface_winding(pc),
    )


def admit_relational_equivalence(metrics: RelationalMetrics, tolerance: RelationalTolerance) -> tuple[bool, tuple[str, ...]]:
    failures: list[str] = []
    if metrics.normalized_overlap_sq < tolerance.overlap_min:
        failures.append("OVERLAP")
    if metrics.phase_relation_rms > tolerance.phase_rms_max:
        failures.append("PHASE_RMS")
    if metrics.phase_relation_max > tolerance.phase_max_max:
        failures.append("PHASE_MAX")
    if metrics.coupling_direction_error > tolerance.coupling_direction_max:
        failures.append("COUPLING_DIRECTION")
    if metrics.coupling_log_scale_error > tolerance.coupling_log_scale_max:
        failures.append("COUPLING_SCALE")
    if tolerance.require_winding_exact and not metrics.winding_equal:
        failures.append("WINDING")
    return (not failures, tuple(failures))


class NoemaEventGate:
    """Suppress NOEMA wakeups while QHTRI remains inside explicit relational controls."""

    def __init__(self, policy: EventGatePolicy) -> None:
        self.policy = policy
        self._last_phi: np.ndarray | None = None
        self._silence_ticks = 0

    def reset(self) -> None:
        self._last_phi = None
        self._silence_ticks = 0

    def observe(self, phi: Sequence[float]) -> EventGateDecision:
        p = _require_vector("phi", phi)
        if self._last_phi is None:
            self._last_phi = p.copy()
            self._silence_ticks = 0
            return EventGateDecision(True, ("GENESIS",), 0, 0.0, 1.0)

        ur = phase_relation_matrix(self._last_phi)
        uc = phase_relation_matrix(p)
        err = np.angle(uc * np.conjugate(ur))
        mask = ~np.eye(p.size, dtype=bool)
        phase_rms = float(np.sqrt(np.mean(err[mask] ** 2)))
        overlap = normalized_overlap_sq(np.exp(1j * self._last_phi), np.exp(1j * p))
        next_silence = self._silence_ticks + 1
        reasons: list[str] = []
        if phase_rms >= self.policy.phase_rms_wake:
            reasons.append("PHASE_RMS")
        if overlap <= self.policy.overlap_floor_wake:
            reasons.append("OVERLAP")
        if next_silence >= self.policy.max_silence_ticks:
            reasons.append("MAX_SILENCE")
        wake = bool(reasons)
        if wake:
            self._last_phi = p.copy()
            self._silence_ticks = 0
        else:
            self._silence_ticks = next_silence
        return EventGateDecision(wake, tuple(reasons), self._silence_ticks, phase_rms, overlap)


def normalized_generator_time_pair(scale: float, semantic_dt: float) -> tuple[float, float]:
    """Return (generator_scale, physical_interval) with invariant scale*interval=semantic_dt.

    This is a structural normalization identity. It does not claim a physical power law.
    """
    s = float(scale)
    dt = float(semantic_dt)
    if not math.isfinite(s) or s <= 0.0 or not math.isfinite(dt) or dt <= 0.0:
        raise ZPENormalizedComputeError("scale and semantic_dt must be finite and > 0")
    return s, dt / s


def select_lowest_compute_work(candidates: Iterable[CandidateScore]) -> CandidateScore:
    admitted = [c for c in candidates if c.admitted]
    if not admitted:
        raise ZPENormalizedComputeError("no admitted normalized-compute candidate")
    for c in admitted:
        if not math.isfinite(float(c.compute_work_proxy)) or c.compute_work_proxy < 0.0:
            raise ZPENormalizedComputeError("compute_work_proxy must be finite and non-negative")
        if c.calls < 1 or c.reference_calls < 1 or c.calls > c.reference_calls:
            raise ZPENormalizedComputeError("invalid call counts")
    return min(admitted, key=lambda c: (c.compute_work_proxy, c.calls, c.candidate_id))
