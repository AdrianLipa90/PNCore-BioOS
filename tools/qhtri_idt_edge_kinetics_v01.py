from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Mapping

SCHEMA = "BIOOS-QHTRI-IDT-EDGE-KINETICS/0.1"
ADAPTER_ID = "GREMLIN.QHTRI.IDT.EDGE_KINETICS.V0_1"
ISOMORPHISM_ID = "ISO.NQ.02.IDT.BIFURCATION.NQ.RECEIPT"
SOURCE_CLASS = "NATURAL_SYSTEM_STATE"
DYNAMICS_CLASS = "ENDOGENOUS_RUNTIME_DYNAMICS"
EVIDENCE_STATUS = "GREMLIN_STRUCTURAL_CANDIDATE"
KAPPA = math.log(2.0) / (24.0 * math.pi)
BRANCH_CUT_EPS = 1e-12


class QhtriIdtEdgeKineticsError(ValueError):
    pass


@dataclass(frozen=True)
class EdgeKinetics:
    coupling: float
    coupling_magnitude: float
    coupling_parity: int
    local_phase_delta: float
    edge_drive: float
    forward_rate: float
    reverse_rate: float
    activity: float
    current: float
    mobility_M: float
    beta: float


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _hex64(value: Any, name: str) -> str:
    text = str(value)
    if len(text) != 64:
        raise QhtriIdtEdgeKineticsError(f"{name} must be 64 hex characters")
    try:
        bytes.fromhex(text)
    except ValueError as exc:
        raise QhtriIdtEdgeKineticsError(f"{name} must be hexadecimal") from exc
    return text.lower()


def _finite(value: Any, name: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise QhtriIdtEdgeKineticsError(f"{name} must be numeric") from exc
    if not math.isfinite(out):
        raise QhtriIdtEdgeKineticsError(f"{name} must be finite")
    return out


def wrap_phase_delta(delta: float) -> float:
    value = _finite(delta, "phase delta")
    wrapped = (value + math.pi) % (2.0 * math.pi) - math.pi
    if math.pi - abs(wrapped) <= BRANCH_CUT_EPS:
        raise QhtriIdtEdgeKineticsError("local U(1) phase difference lies on the principal branch cut")
    return wrapped


def edge_kinetics_from_qhtri(phi_i: float, phi_j: float, coupling: float) -> EdgeKinetics:
    left = _finite(phi_i, "phi_i")
    right = _finite(phi_j, "phi_j")
    gij = _finite(coupling, "coupling")
    if gij == 0.0:
        raise QhtriIdtEdgeKineticsError("positive kinetic realization requires non-zero coupling magnitude")

    magnitude = abs(gij)
    parity = 1 if gij > 0.0 else -1
    local_delta = wrap_phase_delta(right - left)
    drive = float(parity) * local_delta

    forward = magnitude * math.exp(0.5 * drive)
    reverse = magnitude * math.exp(-0.5 * drive)
    activity = forward + reverse
    current = forward - reverse
    beta = KAPPA * drive / math.log(2.0)

    if not (forward > 0.0 and reverse > 0.0 and activity > 0.0 and abs(current) < activity):
        raise QhtriIdtEdgeKineticsError("constructed directed kinetic pair failed positivity/admissibility")

    result = EdgeKinetics(
        coupling=gij,
        coupling_magnitude=magnitude,
        coupling_parity=parity,
        local_phase_delta=local_delta,
        edge_drive=drive,
        forward_rate=forward,
        reverse_rate=reverse,
        activity=activity,
        current=current,
        mobility_M=magnitude,
        beta=beta,
    )
    validate_edge_kinetics(result)
    return result


def validate_edge_kinetics(edge: EdgeKinetics, *, atol: float = 2e-12) -> None:
    values = asdict(edge)
    for key, value in values.items():
        if key == "coupling_parity":
            continue
        _finite(value, key)
    if edge.coupling_parity not in (-1, 1):
        raise QhtriIdtEdgeKineticsError("coupling_parity must be -1 or +1")
    if edge.coupling == 0.0 or abs(abs(edge.coupling) - edge.coupling_magnitude) > atol:
        raise QhtriIdtEdgeKineticsError("coupling magnitude mismatch")
    if (1 if edge.coupling > 0.0 else -1) != edge.coupling_parity:
        raise QhtriIdtEdgeKineticsError("coupling parity mismatch")
    if abs(edge.edge_drive - edge.coupling_parity * edge.local_phase_delta) > atol:
        raise QhtriIdtEdgeKineticsError("edge drive mismatch")
    if edge.forward_rate <= 0.0 or edge.reverse_rate <= 0.0:
        raise QhtriIdtEdgeKineticsError("directed rates must be strictly positive")
    if abs(edge.activity - (edge.forward_rate + edge.reverse_rate)) > atol:
        raise QhtriIdtEdgeKineticsError("activity mismatch")
    if abs(edge.current - (edge.forward_rate - edge.reverse_rate)) > atol:
        raise QhtriIdtEdgeKineticsError("current mismatch")
    if abs(edge.current) >= edge.activity:
        raise QhtriIdtEdgeKineticsError("positive kinetic pair requires |current| < activity")

    mobility = 0.5 * math.sqrt(edge.activity * edge.activity - edge.current * edge.current)
    drive = 2.0 * math.atanh(edge.current / edge.activity)
    beta = KAPPA * drive / math.log(2.0)
    if abs(mobility - edge.mobility_M) > atol:
        raise QhtriIdtEdgeKineticsError("IDT mobility round-trip mismatch")
    if abs(drive - edge.edge_drive) > atol:
        raise QhtriIdtEdgeKineticsError("IDT drive round-trip mismatch")
    if abs(beta - edge.beta) > atol:
        raise QhtriIdtEdgeKineticsError("IDT beta round-trip mismatch")


def validate_edge_reversal(phi_i: float, phi_j: float, coupling: float, *, atol: float = 2e-12) -> tuple[EdgeKinetics, EdgeKinetics]:
    forward = edge_kinetics_from_qhtri(phi_i, phi_j, coupling)
    reverse = edge_kinetics_from_qhtri(phi_j, phi_i, coupling)
    if abs(forward.mobility_M - reverse.mobility_M) > atol:
        raise QhtriIdtEdgeKineticsError("mobility is not invariant under edge reversal")
    if abs(forward.edge_drive + reverse.edge_drive) > atol:
        raise QhtriIdtEdgeKineticsError("edge drive is not antisymmetric under reversal")
    if abs(forward.beta + reverse.beta) > atol:
        raise QhtriIdtEdgeKineticsError("beta is not antisymmetric under reversal")
    if abs(forward.activity - reverse.activity) > atol:
        raise QhtriIdtEdgeKineticsError("activity is not invariant under reversal")
    if abs(forward.current + reverse.current) > atol:
        raise QhtriIdtEdgeKineticsError("current is not antisymmetric under reversal")
    return forward, reverse


def build_edge_kinetics_receipt(
    *,
    qhtri_tick: int,
    oscillator_i: int,
    oscillator_j: int,
    phi_lane_commitment: str,
    coupling_matrix_commitment: str,
    edge: EdgeKinetics,
) -> dict[str, Any]:
    validate_edge_kinetics(edge)
    tick = int(qhtri_tick)
    i = int(oscillator_i)
    j = int(oscillator_j)
    if tick < 0 or i < 0 or j < 0 or i == j:
        raise QhtriIdtEdgeKineticsError("tick and distinct oscillator ids must be non-negative")
    body = {
        "schema": SCHEMA,
        "adapter_id": ADAPTER_ID,
        "isomorphism_id": ISOMORPHISM_ID,
        "source_class": SOURCE_CLASS,
        "dynamics_class": DYNAMICS_CLASS,
        "evidence_status": EVIDENCE_STATUS,
        "qhtri_tick": tick,
        "oscillator_i": i,
        "oscillator_j": j,
        "phi_lane_commitment": _hex64(phi_lane_commitment, "phi_lane_commitment"),
        "coupling_matrix_commitment": _hex64(coupling_matrix_commitment, "coupling_matrix_commitment"),
        "kinetics": asdict(edge),
    }
    return {**body, "edge_kinetics_receipt_sha256": _sha256(body)}


def validate_edge_kinetics_receipt(receipt: Mapping[str, Any]) -> None:
    if receipt.get("schema") != SCHEMA or receipt.get("adapter_id") != ADAPTER_ID:
        raise QhtriIdtEdgeKineticsError("edge kinetics receipt schema/adapter mismatch")
    if receipt.get("isomorphism_id") != ISOMORPHISM_ID:
        raise QhtriIdtEdgeKineticsError("edge kinetics receipt isomorphism mismatch")
    if receipt.get("source_class") != SOURCE_CLASS or receipt.get("dynamics_class") != DYNAMICS_CLASS:
        raise QhtriIdtEdgeKineticsError("edge kinetics source classification mismatch")
    if receipt.get("evidence_status") != EVIDENCE_STATUS:
        raise QhtriIdtEdgeKineticsError("edge kinetics evidence status mismatch")
    _hex64(receipt.get("phi_lane_commitment"), "phi_lane_commitment")
    _hex64(receipt.get("coupling_matrix_commitment"), "coupling_matrix_commitment")
    edge = EdgeKinetics(**dict(receipt.get("kinetics", {})))
    validate_edge_kinetics(edge)
    body = {key: value for key, value in receipt.items() if key != "edge_kinetics_receipt_sha256"}
    if receipt.get("edge_kinetics_receipt_sha256") != _sha256(body):
        raise QhtriIdtEdgeKineticsError("edge kinetics receipt seal mismatch")
