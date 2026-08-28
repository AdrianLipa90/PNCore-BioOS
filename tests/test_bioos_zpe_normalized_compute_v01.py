import math
import numpy as np
import pytest

from tools.bioos_zpe_normalized_compute_v01 import (
    CandidateScore,
    EventGatePolicy,
    NoemaEventGate,
    RelationalMetrics,
    RelationalTolerance,
    ZPENormalizedComputeError,
    admit_relational_equivalence,
    normalized_generator_time_pair,
    normalized_overlap_sq,
    phase_relation_matrix,
    relational_metrics,
    select_lowest_compute_work,
)


def _g(n=36):
    rng=np.random.default_rng(7)
    x=rng.normal(size=(n,n)); np.fill_diagonal(x,0.0); return x


def test_zpe_overlap_and_phase_relations_ignore_global_phase_and_common_amplitude():
    rng=np.random.default_rng(1); phi=rng.uniform(-8,8,36); shift=2.345
    a=3.7*np.exp(1j*phi); b=0.23*np.exp(1j*(phi+shift))
    assert normalized_overlap_sq(a,b) == pytest.approx(1.0,abs=1e-14)
    assert np.max(np.abs(phase_relation_matrix(phi)-phase_relation_matrix(phi+shift))) < 1e-14


def test_relational_metrics_separate_coupling_direction_from_common_scale():
    rng=np.random.default_rng(2); phi=rng.uniform(0,2*np.pi,36); g=_g()
    m=relational_metrics(phi,g,phi+1.2,g*4.0)
    assert m.normalized_overlap_sq == pytest.approx(1.0,abs=1e-14)
    assert m.phase_relation_rms < 1e-14
    assert m.coupling_direction_error < 1e-14
    assert m.coupling_log_scale_error == pytest.approx(math.log(4.0))


def test_explicit_tolerance_admits_and_rejects_independently():
    tol=RelationalTolerance(0.999,0.02,0.05,0.03,0.01,True)
    good=RelationalMetrics(0.9999,0.01,0.03,0.02,0.005,1,1)
    bad=RelationalMetrics(0.9999,0.01,0.03,0.02,0.005,1,-1)
    assert admit_relational_equivalence(good,tol)==(True,())
    assert admit_relational_equivalence(bad,tol)==(False,("WINDING",))


def test_event_gate_is_genesis_then_suppression_then_threshold_wakeup():
    phi=np.linspace(0,2*np.pi,36,endpoint=False)
    gate=NoemaEventGate(EventGatePolicy(phase_rms_wake=0.05,overlap_floor_wake=0.999,max_silence_ticks=10))
    assert gate.observe(phi).reasons == ("GENESIS",)
    d=gate.observe(phi+0.3) # pure gauge shift
    assert d.wake_noema is False
    pert=phi.copy(); pert[0]+=0.2
    d=gate.observe(pert)
    assert d.wake_noema is True
    assert "PHASE_RMS" in d.reasons or "OVERLAP" in d.reasons


def test_event_gate_max_silence_is_explicit_control():
    phi=np.linspace(0,2*np.pi,36,endpoint=False)
    gate=NoemaEventGate(EventGatePolicy(phase_rms_wake=1.0,overlap_floor_wake=0.0,max_silence_ticks=3))
    assert gate.observe(phi).wake_noema
    assert not gate.observe(phi).wake_noema
    assert not gate.observe(phi).wake_noema
    d=gate.observe(phi)
    assert d.wake_noema and d.reasons == ("MAX_SILENCE",)


def test_generator_time_normalization_preserves_product():
    for scale in (0.125,0.25,0.5,1.0,2.0,8.0):
        s,physical_dt=normalized_generator_time_pair(scale,0.01)
        assert s*physical_dt == pytest.approx(0.01,rel=0,abs=1e-15)


def test_selector_never_chooses_failed_candidate_even_if_cheaper():
    m=RelationalMetrics(1.0,0,0,0,0,0,0)
    selected=select_lowest_compute_work([
        CandidateScore("failed",False,0.1,m,2,100),
        CandidateScore("pass-a",True,0.5,m,20,100),
        CandidateScore("pass-b",True,0.4,m,30,100),
    ])
    assert selected.candidate_id == "pass-b"


def test_no_hidden_degenerate_inputs():
    with pytest.raises(ZPENormalizedComputeError): normalized_overlap_sq([0j],[0j])
    with pytest.raises(ZPENormalizedComputeError): RelationalTolerance(1.1,0,0,0,0,True)
    with pytest.raises(ZPENormalizedComputeError): EventGatePolicy(0,0.5,1)
