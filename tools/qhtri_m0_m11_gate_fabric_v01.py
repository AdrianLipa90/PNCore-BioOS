from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

DIM = 36
KAPPA = math.log(2.0) / (24.0 * math.pi)
SCHEMA = "BIOOS_QHTRI_M0_M11_ANALOG_GATE_FABRIC_V0_1"
RECEIPT_SCHEMA = "BIOOS_QHTRI_M0_M11_ANALOG_GATE_RECEIPT_V0_1"
LAYERS = tuple(f"M{i}" for i in range(12))


class AnalogGateFabricError(ValueError):
    pass


def clamp01(value: float) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise AnalogGateFabricError("non-finite gate scalar")
    return min(1.0, max(0.0, x))


def analog_and(a: float, b: float) -> float:
    return clamp01(a) * clamp01(b)


def analog_or(a: float, b: float) -> float:
    aa, bb = clamp01(a), clamp01(b)
    return aa + bb - aa * bb


def analog_not(a: float) -> float:
    return 1.0 - clamp01(a)


def analog_xor(a: float, b: float) -> float:
    aa, bb = clamp01(a), clamp01(b)
    return aa + bb - 2.0 * aa * bb


def wrap_phase(value: float) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise AnalogGateFabricError("non-finite phase")
    return (x + math.pi) % (2.0 * math.pi) - math.pi


def phase_vector(values: Sequence[float], name: str = "phase") -> tuple[float, ...]:
    if len(values) != DIM:
        raise AnalogGateFabricError(f"{name} must contain exactly {DIM} lanes")
    return tuple(wrap_phase(v) for v in values)


def scalar_vector(values: Sequence[float], name: str) -> tuple[float, ...]:
    if len(values) != DIM:
        raise AnalogGateFabricError(f"{name} must contain exactly {DIM} lanes")
    out = []
    for value in values:
        x = float(value)
        if not math.isfinite(x):
            raise AnalogGateFabricError(f"{name} contains non-finite value")
        out.append(x)
    return tuple(out)


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def circular_barycenter(
    targets: Sequence[Sequence[float]],
    weights: Sequence[float],
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    if not targets or len(targets) != len(weights):
        raise AnalogGateFabricError("targets/weights mismatch")
    vv = [phase_vector(v, "target") for v in targets]
    ww = [clamp01(w) for w in weights]
    if sum(ww) <= 0.0:
        raise AnalogGateFabricError("circular barycenter requires positive weight")

    target_out: list[float] = []
    coherence_out: list[float] = []
    denom = sum(ww)
    for j in range(DIM):
        real = math.fsum(w * math.cos(v[j]) for v, w in zip(vv, ww))
        imag = math.fsum(w * math.sin(v[j]) for v, w in zip(vv, ww))
        magnitude = math.hypot(real, imag)
        if magnitude <= 1e-15:
            target_out.append(0.0)
            coherence_out.append(0.0)
        else:
            target_out.append(math.atan2(imag, real))
            coherence_out.append(min(1.0, magnitude / denom))
    return tuple(target_out), tuple(coherence_out)


@dataclass(frozen=True, slots=True)
class AnchorTerm:
    layer: str
    target: tuple[float, ...]
    gain: tuple[float, ...]
    tau: float = 0.0
    effect_carrying: bool = False
    source_ref: str | None = None

    def __post_init__(self) -> None:
        if self.layer not in LAYERS:
            raise AnalogGateFabricError(f"unknown layer: {self.layer}")
        phase_vector(self.target, "anchor.target")
        if len(self.gain) != DIM:
            raise AnalogGateFabricError("anchor gain must be 36D")
        for g in self.gain:
            if not math.isfinite(g) or g < 0.0:
                raise AnalogGateFabricError("anchor gain must be finite and non-negative")
        if not math.isfinite(self.tau):
            raise AnalogGateFabricError("anchor tau must be finite")


@dataclass(frozen=True, slots=True)
class TorsionEdge:
    i: int
    j: int
    m: int
    n: int
    tau: float
    K: float
    R: float
    effect_carrying: bool = False
    source_ref: str | None = None

    def __post_init__(self) -> None:
        if not (0 <= self.i < DIM and 0 <= self.j < DIM and self.i != self.j):
            raise AnalogGateFabricError("invalid torsion edge endpoints")
        if self.m <= 0 or self.n <= 0:
            raise AnalogGateFabricError("torsion orders must be positive")
        if not math.isfinite(self.tau):
            raise AnalogGateFabricError("torsion tau must be finite")
        if not math.isfinite(self.K) or self.K < 0.0:
            raise AnalogGateFabricError("torsion K must be finite and non-negative")
        if not math.isfinite(self.R) or not (0.0 <= self.R <= 1.0):
            raise AnalogGateFabricError("torsion R must be in [0,1]")

    @property
    def gain(self) -> float:
        return self.K * self.R


@dataclass(frozen=True, slots=True)
class CompiledFabric:
    anchors: tuple[AnchorTerm, ...]
    torsion_edges: tuple[TorsionEdge, ...]
    affect_multiplier: float
    closure: float
    no_go: float
    m4_admission: float
    identity_anchor_present: bool
    m10_receipt_enabled: bool
    layer_status: Mapping[str, str]


def _uniform_gain(value: float) -> tuple[float, ...]:
    g = max(0.0, float(value))
    if not math.isfinite(g):
        raise AnalogGateFabricError("non-finite gain")
    return (g,) * DIM


def _anchor_from_frame(
    layer: str,
    frame: Mapping[str, Any],
    *,
    gain_scalar: float,
    target_key: str = "target",
    tau: float = 0.0,
) -> AnchorTerm:
    target = phase_vector(frame[target_key], f"{layer}.{target_key}")
    return AnchorTerm(
        layer=layer,
        target=target,
        gain=_uniform_gain(gain_scalar),
        tau=tau,
        effect_carrying=bool(frame.get("effect_carrying", False)),
        source_ref=str(frame["source_ref"]) if frame.get("source_ref") is not None else None,
    )


def compile_gate_fabric(layer_frames: Mapping[str, Mapping[str, Any]]) -> CompiledFabric:
    unknown = set(layer_frames) - set(LAYERS)
    if unknown:
        raise AnalogGateFabricError(f"unknown M0-M11 layers: {sorted(unknown)}")

    anchors: list[AnchorTerm] = []
    torsion_edges: list[TorsionEdge] = []
    status = {layer: "QUIET" for layer in LAYERS}

    # M5: explicit affect changes salience only.
    m5 = layer_frames.get("M5", {})
    if m5 and bool(m5.get("explicit", False)):
        affect_multiplier = float(m5.get("salience_multiplier", 1.0))
        if not math.isfinite(affect_multiplier) or affect_multiplier < 0.0:
            raise AnalogGateFabricError("M5 salience multiplier invalid")
        affect_multiplier = min(float(m5.get("salience_max", 4.0)), affect_multiplier)
        status["M5"] = "EXPLICIT_MODULATION"
    else:
        affect_multiplier = 1.0
        status["M5"] = "NEUTRAL_MODULATION"

    # M4: candidate-effect admission only.
    m4 = layer_frames.get("M4", {})
    if m4:
        m4_admission = analog_and(
            analog_and(m4.get("procedure_match", 0.0), m4.get("validator_confidence", 0.0)),
            m4.get("capability_admission", 0.0),
        )
        status["M4"] = "ADMITTED" if m4_admission > 0.0 else "CANDIDATE_GAIN_ZERO"
        if "target" in m4:
            anchors.append(
                _anchor_from_frame(
                    "M4",
                    m4,
                    gain_scalar=KAPPA * clamp01(m4.get("activation", 1.0)) * m4_admission,
                )
            )
    else:
        m4_admission = 0.0

    # M11: uncertainty and NO-GO closure.
    m11 = layer_frames.get("M11", {})
    validation_confidence = clamp01(m11.get("validation_confidence", 1.0)) if m11 else 1.0
    uncertainty = clamp01(m11.get("uncertainty", 0.0)) if m11 else 0.0
    no_go = clamp01(m11.get("no_go", 0.0)) if m11 else 0.0
    closure = validation_confidence * (1.0 - uncertainty) * (1.0 - no_go)
    if m11:
        status["M11"] = "NO_GO" if no_go >= 1.0 else "CLOSURE_ACTIVE"

    # M0 observation source lock.
    m0 = layer_frames.get("M0", {})
    if m0:
        if not m0.get("provenance_ref"):
            status["M0"] = "UNPROVENANCED_SOURCE_QUIET"
        elif "target" in m0:
            activation = clamp01(m0.get("activation", 1.0))
            confidence = clamp01(m0.get("confidence", 1.0))
            anchors.append(_anchor_from_frame("M0", m0, gain_scalar=KAPPA * activation * confidence))
            status["M0"] = "SOURCE_LOCK"

    # M1 active working set.
    m1 = layer_frames.get("M1", {})
    if m1 and "target" in m1:
        activation = analog_and(m1.get("command_activation", 1.0), m1.get("context_admission", 1.0))
        anchors.append(_anchor_from_frame("M1", m1, gain_scalar=KAPPA * activation))
        status["M1"] = "ACTIVE_WORKING_SET"

    # M2 explicit transition candidate.
    m2 = layer_frames.get("M2", {})
    if m2:
        if bool(m2.get("transition_explicit", False)) and "target" in m2:
            confidence = clamp01(m2.get("confidence", 1.0))
            anchors.append(_anchor_from_frame("M2", m2, gain_scalar=KAPPA * confidence))
            status["M2"] = "TRANSITION_CANDIDATE"
        else:
            status["M2"] = "NO_EXPLICIT_TRANSITION"

    # M3 semantic candidate barycenter.
    m3 = layer_frames.get("M3", {})
    if m3:
        targets = m3.get("targets", [])
        weights = m3.get("weights", [])
        if targets:
            target, coherence = circular_barycenter(targets, weights)
            activation = clamp01(m3.get("activation", 1.0))
            gain = tuple(KAPPA * activation * c for c in coherence)
            anchors.append(AnchorTerm("M3", target, gain, source_ref=m3.get("source_ref")))
            status["M3"] = "SEMANTIC_ATTRACTOR"

    # M6 rational torsion relations.
    m6 = layer_frames.get("M6", {})
    for raw in m6.get("edges", []) if m6 else []:
        torsion_edges.append(
            TorsionEdge(
                i=int(raw["i"]),
                j=int(raw["j"]),
                m=int(raw["m"]),
                n=int(raw["n"]),
                tau=float(raw.get("tau", 0.0)),
                K=float(raw.get("K", KAPPA)),
                R=float(raw.get("R", 1.0)),
                effect_carrying=bool(raw.get("effect_carrying", False)),
                source_ref=str(raw["source_ref"]) if raw.get("source_ref") is not None else None,
            )
        )
    if torsion_edges:
        status["M6"] = "TORSION_RELATIONS_ACTIVE"

    # M7 branch braid.
    m7 = layer_frames.get("M7", {})
    if m7 and m7.get("targets"):
        target, coherence = circular_barycenter(m7["targets"], m7["weights"])
        activation = clamp01(m7.get("activation", 1.0))
        gain = tuple(KAPPA * activation * c for c in coherence)
        anchors.append(
            AnchorTerm(
                "M7",
                target,
                gain,
                effect_carrying=bool(m7.get("effect_carrying", False)),
                source_ref=m7.get("source_ref"),
            )
        )
        status["M7"] = "BRAID_ACTIVE"

    # M8 protected identity anchor.
    m8 = layer_frames.get("M8", {})
    identity_anchor_present = False
    if m8:
        if bool(m8.get("mutation_attempt", False)):
            raise AnalogGateFabricError("M8 protected identity mutation denied")
        if "target" in m8:
            target = phase_vector(m8["target"], "M8.target")
            gain = KAPPA * clamp01(m8.get("restoring_strength", 1.0))
            anchors.append(AnchorTerm("M8", target, _uniform_gain(gain), source_ref=m8.get("identity_ref")))
            identity_anchor_present = True
            status["M8"] = "PROTECTED_IDENTITY_ANCHOR"

    # M9 holonomy transport target.
    m9 = layer_frames.get("M9", {})
    if m9 and "target" in m9:
        base = phase_vector(m9["target"], "M9.target")
        holonomy = phase_vector(m9.get("holonomy", [0.0] * DIM), "M9.holonomy")
        transported = tuple(wrap_phase(a + h) for a, h in zip(base, holonomy))
        gain = KAPPA * clamp01(m9.get("confidence", 1.0))
        anchors.append(
            AnchorTerm(
                "M9",
                transported,
                _uniform_gain(gain),
                effect_carrying=bool(m9.get("effect_carrying", False)),
                source_ref=m9.get("source_ref"),
            )
        )
        status["M9"] = "HOLONOMY_ACTIVE"

    # M10 is strictly observational / append-only evidence.
    m10 = layer_frames.get("M10", {})
    m10_receipt_enabled = bool(m10.get("append_only", True)) if m10 else True
    if m10 and not m10_receipt_enabled:
        raise AnalogGateFabricError("M10 receipt/provenance must remain append-only")
    status["M10"] = "RECEIPT_OBSERVER"

    # Apply M5 salience and M4/M11 effect admission to compiled terms.
    adjusted_anchors: list[AnchorTerm] = []
    for term in anchors:
        scale = affect_multiplier if term.layer not in {"M8"} else 1.0
        if term.effect_carrying:
            scale *= m4_admission * closure
        adjusted_anchors.append(
            AnchorTerm(
                layer=term.layer,
                target=term.target,
                gain=tuple(g * scale for g in term.gain),
                tau=term.tau,
                effect_carrying=term.effect_carrying,
                source_ref=term.source_ref,
            )
        )

    adjusted_edges: list[TorsionEdge] = []
    for edge in torsion_edges:
        scale = affect_multiplier
        if edge.effect_carrying:
            scale *= m4_admission * closure
        adjusted_edges.append(
            TorsionEdge(
                i=edge.i,
                j=edge.j,
                m=edge.m,
                n=edge.n,
                tau=edge.tau,
                K=edge.K * scale,
                R=edge.R,
                effect_carrying=edge.effect_carrying,
                source_ref=edge.source_ref,
            )
        )

    return CompiledFabric(
        anchors=tuple(adjusted_anchors),
        torsion_edges=tuple(adjusted_edges),
        affect_multiplier=affect_multiplier,
        closure=closure,
        no_go=no_go,
        m4_admission=m4_admission,
        identity_anchor_present=identity_anchor_present,
        m10_receipt_enabled=m10_receipt_enabled,
        layer_status=status,
    )


def qhtri_force(theta: Sequence[float], fabric: CompiledFabric) -> tuple[float, ...]:
    state = phase_vector(theta, "theta")
    force = [0.0] * DIM

    for term in fabric.anchors:
        tau = wrap_phase(term.tau)
        for j in range(DIM):
            force[j] += -term.gain[j] * math.sin(wrap_phase(state[j] - term.target[j] - tau))

    for edge in fabric.torsion_edges:
        epsilon = wrap_phase(edge.n * state[edge.i] - edge.m * state[edge.j] - edge.tau)
        s = edge.gain * math.sin(epsilon)
        force[edge.i] += -edge.n * s
        force[edge.j] += +edge.m * s

    return tuple(force)


def stability_bound(fabric: CompiledFabric) -> float:
    anchor_bound = math.fsum(math.fsum(term.gain) for term in fabric.anchors)
    torsion_bound = math.fsum(
        edge.gain * (edge.m * edge.m + edge.n * edge.n)
        for edge in fabric.torsion_edges
    )
    return anchor_bound + torsion_bound


def qhtri_step(
    theta: Sequence[float],
    omega: Sequence[float],
    fabric: CompiledFabric,
    *,
    dt_requested: float,
) -> dict[str, Any]:
    state = phase_vector(theta, "theta")
    freq = scalar_vector(omega, "omega")
    dt_req = float(dt_requested)
    if not math.isfinite(dt_req) or dt_req <= 0.0:
        raise AnalogGateFabricError("dt_requested must be finite and positive")

    L = stability_bound(fabric)
    dt_safe = min(dt_req, 0.2 / L) if L > 0.0 else dt_req
    force = qhtri_force(state, fabric)
    after = tuple(wrap_phase(t + dt_safe * (w + f)) for t, w, f in zip(state, freq, force))

    return {
        "schema": SCHEMA,
        "theta_before": list(state),
        "theta_after": list(after),
        "force": list(force),
        "dt_requested": dt_req,
        "dt_used": dt_safe,
        "stability_bound": L,
        "layer_status": dict(fabric.layer_status),
        "affect_multiplier": fabric.affect_multiplier,
        "m4_admission": fabric.m4_admission,
        "closure": fabric.closure,
        "no_go": fabric.no_go,
        "identity_anchor_present": fabric.identity_anchor_present,
        "m10_receipt_enabled": fabric.m10_receipt_enabled,
        "authority_grant": False,
        "execution_admitted": False,
    }


def make_m10_receipt(
    step: Mapping[str, Any],
    *,
    hypercrystal_commitment: str | None = None,
    evidence_refs: Sequence[str] = (),
) -> dict[str, Any]:
    if step.get("schema") != SCHEMA:
        raise AnalogGateFabricError("unsupported QHTRI gate step schema")
    if step.get("m10_receipt_enabled") is not True:
        raise AnalogGateFabricError("M10 receipt observer unavailable")

    core: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "gate_schema": SCHEMA,
        "theta_before": step["theta_before"],
        "theta_after": step["theta_after"],
        "dt_used": step["dt_used"],
        "stability_bound": step["stability_bound"],
        "layer_status": step["layer_status"],
        "hypercrystal_commitment": hypercrystal_commitment,
        "evidence_refs": sorted(str(v) for v in evidence_refs),
        "authority_grant": False,
        "append_only": True,
    }
    receipt_id = hashlib.sha256(b"BIOOS-QHTRI-M0-M11-RECEIPT/v0.1\x00" + _canonical(core)).hexdigest()
    return {**core, "receipt_id": receipt_id}
