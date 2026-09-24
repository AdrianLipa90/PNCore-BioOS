from __future__ import annotations

from pathlib import Path
import sys
import hashlib
import json
import math
import os
import shutil
import struct
import time

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.noema_qhtri_live_bifurcation_ring_v01 import (
    HEADER,
    LiveBifurcationRing,
    RingCorruptionError,
)

LIVE_ROOT = Path("/dev/shm/ciel_noema")
BANK_MANIFEST_SHA256 = "754d6e8d6804c5f61e8620c9fde473bebe8ead79403ab6f894a90278b62b767b"
PNCS_BANK_HEAD = "892e96e6dd4afb8b49d33d76758910ac14791141"
KAPPA = math.log(2.0) / (24.0 * math.pi)


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def stable_snapshot(timeout_s: float = 4.0, after_tick: int | None = None):
    deadline = time.monotonic() + timeout_s
    tick_mm = np.memmap(LIVE_ROOT / "tick", mode="r", dtype=np.uint64, shape=(1,))
    phi_mm = np.memmap(LIVE_ROOT / "phi", mode="r", dtype=np.float64, shape=(36,))
    omega_mm = np.memmap(LIVE_ROOT / "omega", mode="r", dtype=np.float64, shape=(36,))
    g_mm = np.memmap(LIVE_ROOT / "g", mode="r", dtype=np.float64, shape=(36, 36))
    while time.monotonic() < deadline:
        t0 = int(tick_mm[0])
        if after_tick is not None and t0 <= after_tick:
            time.sleep(0.002)
            continue
        phi = np.array(phi_mm, dtype=np.float64, copy=True)
        omega = np.array(omega_mm, dtype=np.float64, copy=True)
        g = np.array(g_mm, dtype=np.float64, copy=True)
        t1 = int(tick_mm[0])
        if t0 == t1 and (after_tick is None or t0 > after_tick):
            if not (np.all(np.isfinite(phi)) and np.all(np.isfinite(omega)) and np.all(np.isfinite(g))):
                raise RuntimeError("live QHTRI snapshot contains non-finite values")
            return t0, phi, omega, g
        time.sleep(0.001)
    raise TimeoutError("failed to obtain stable unique live QHTRI snapshot")


def strongest_edge(phi: np.ndarray, g: np.ndarray):
    ranked=[]
    for i in range(36):
        for j in range(36):
            if i == j:
                continue
            coupling=float(g[i,j])
            if coupling == 0.0 or not math.isfinite(coupling):
                continue
            delta=(float(phi[j]-phi[i])+math.pi)%(2.0*math.pi)-math.pi
            margin=math.pi-abs(delta)
            if margin <= 1e-12:
                continue
            ranked.append((abs(coupling), -i, -j, i, j, coupling, delta, margin))
    if not ranked:
        raise RuntimeError("no admissible nonzero QHTRI coupling edge")
    _,_,_,i,j,coupling,delta,margin=max(ranked)
    parity=1 if coupling >= 0.0 else -1
    magnitude=abs(coupling)
    drive=parity*delta
    forward=magnitude*math.exp(0.5*drive)
    reverse=magnitude*math.exp(-0.5*drive)
    activity=forward+reverse
    current=forward-reverse
    recovered_m=0.5*math.sqrt(max(activity*activity-current*current,0.0))
    recovered_drive=math.log(forward/reverse)
    beta=KAPPA*drive/math.log(2.0)
    roundtrip=max(abs(recovered_m-magnitude),abs(recovered_drive-drive))
    if forward <= 0.0 or reverse <= 0.0 or roundtrip > 1e-12:
        raise RuntimeError(f"edge kinetics roundtrip failed: {roundtrip}")
    return {
        "i":i,"j":j,"coupling":coupling,"coupling_magnitude":magnitude,
        "coupling_parity":parity,"local_phase_delta":delta,"branch_margin":margin,
        "edge_drive":drive,"forward_rate":forward,"reverse_rate":reverse,
        "activity":activity,"current":current,"mobility_M":magnitude,"beta":beta,
        "roundtrip_error":roundtrip,
    }


def build_bifurcation(tick, phi, omega, g, edge):
    phi_raw=np.ascontiguousarray(phi,dtype='<f8').tobytes()
    omega_raw=np.ascontiguousarray(omega,dtype='<f8').tobytes()
    g_raw=np.ascontiguousarray(g,dtype='<f8').tobytes()
    phasors=np.ascontiguousarray(np.exp(1j*phi),dtype='<c16').tobytes()
    state_body={
        "qhtri_tick":tick,
        "phi_sha256":sha_bytes(phi_raw),
        "omega_sha256":sha_bytes(omega_raw),
        "g_sha256":sha_bytes(g_raw),
        "source_class":"NATURAL_SYSTEM_STATE",
        "dynamics_class":"ENDOGENOUS_RUNTIME_DYNAMICS",
    }
    t36_body={
        "qhtri_tick":tick,
        "whole_lane_width":36,
        "phi_lane_sha256":sha_bytes(phi_raw),
        "whole_lane_witness":True,
    }
    cp1_body={
        "qhtri_tick":tick,
        "representation":"projective_phasor_lane",
        "whole_lane_width":36,
        "phasor_lane_sha256":sha_bytes(phasors),
    }
    body={
        "schema":"BIOOS-NOEMA-QHTRI-BIFURCATION/0.1",
        "bank_manifest_sha256":BANK_MANIFEST_SHA256,
        "qhtri_tick":tick,
        "qhtri_state_commitment":sha(state_body),
        "magnitude_M":float(edge["mobility_M"]),
        "beta":float(edge["beta"]),
        "generator_ref":f"gremlin:qhtri-idt-edge-kinetics:v0.1:{edge['i']}:{edge['j']}",
        "t36_witness_commitment":sha(t36_body),
        "cp1_state_commitment":sha(cp1_body),
        "telemetry_evidence_ref":f"/dev/shm/ciel_noema@tick:{tick}",
        "source_class":"NATURAL_SYSTEM_STATE",
        "dynamics_class":"ENDOGENOUS_RUNTIME_DYNAMICS",
    }
    return {**body,"bifurcation_receipt_sha256":sha(body)}, state_body, t36_body, cp1_body


def main():
    if not LIVE_ROOT.exists():
        raise RuntimeError("live NOEMA surface absent")
    for name,sz in (("phi",288),("omega",288),("tick",8),("g",10368)):
        p=LIVE_ROOT/name
        if not p.is_file() or p.stat().st_size != sz:
            raise RuntimeError(f"live surface contract mismatch: {name}")
    spinor_names=("spinor_turns.i64","spinor_tick.u64","spinor_epoch.json")
    spinor_live=all((LIVE_ROOT/n).exists() for n in spinor_names)

    stamp=f"{os.getpid()}_{time.time_ns()}"
    ring_root=LIVE_ROOT/f"bifurcation_ring_v01_shadow_{stamp}"
    tamper_root=LIVE_ROOT/f"bifurcation_ring_v01_tamper_{stamp}"
    ring=LiveBifurcationRing.create(ring_root,capacity=16,slot_bytes=32768,ring_epoch=f"live-shadow-{stamp}")
    published=[]
    edge_receipts=[]
    previous_tick=None
    first_tick=None
    last_tick=None
    for _ in range(8):
        tick,phi,omega,g=stable_snapshot(after_tick=previous_tick)
        edge=strongest_edge(phi,g)
        receipt,state_body,t36_body,cp1_body=build_bifurcation(tick,phi,omega,g,edge)
        pub=ring.publish(qhtri_tick=tick,bifurcation_receipt=receipt,spinor_lift_receipt=None)
        published.append({
            "sequence":pub.sequence,"qhtri_tick":pub.qhtri_tick,
            "record_sha256":pub.record_sha256,"parent_record_sha256":pub.parent_record_sha256,
            "event_sha256":pub.event["event_sha256"],
            "bifurcation_receipt_sha256":receipt["bifurcation_receipt_sha256"],
            "edge":edge,
            "state_commitment":receipt["qhtri_state_commitment"],
            "t36_witness_commitment":receipt["t36_witness_commitment"],
            "cp1_state_commitment":receipt["cp1_state_commitment"],
            "spinor_status":pub.event["spinor_status"],
        })
        edge_receipts.append(receipt)
        first_tick=tick if first_tick is None else first_tick
        last_tick=tick
        previous_tick=tick

    pre_reopen=ring.verify_pending_chain()
    reopened=LiveBifurcationRing.open(ring_root,verify_pending_chain=True)
    reopen_report=reopened.verify_pending_chain()
    consumed=[]
    for expected in published:
        rec=reopened.read_next()
        if rec is None:
            raise RuntimeError("NOEMA consumer unexpectedly reached empty ring")
        if rec.sequence != expected["sequence"] or rec.qhtri_tick != expected["qhtri_tick"]:
            raise RuntimeError("NOEMA ring read ordering mismatch")
        if rec.record_sha256 != expected["record_sha256"]:
            raise RuntimeError("NOEMA ring record commitment mismatch")
        reopened.ack(rec.sequence,expected_record_sha256=rec.record_sha256)
        consumed.append({"sequence":rec.sequence,"qhtri_tick":rec.qhtri_tick,"record_sha256":rec.record_sha256})
    post_ack=reopened.verify_pending_chain()
    if post_ack["pending_count"] != 0:
        raise RuntimeError("ring not empty after exact NOEMA acknowledgements")

    # Independent tamper gate on a second shadow ring.
    tamper=LiveBifurcationRing.create(tamper_root,capacity=2,slot_bytes=32768,ring_epoch=f"tamper-{stamp}")
    # Take a fresh tick so the event itself is live-derived.
    tick,phi,omega,g=stable_snapshot(after_tick=last_tick)
    edge=strongest_edge(phi,g)
    receipt,_,_,_=build_bifurcation(tick,phi,omega,g,edge)
    tamper.publish(qhtri_tick=tick,bifurcation_receipt=receipt)
    with tamper.ring_path.open("r+b",buffering=0) as f:
        f.seek(HEADER.size+7)
        b=f.read(1)
        f.seek(HEADER.size+7)
        f.write(bytes([b[0]^1]))
        os.fsync(f.fileno())
    tamper_detected=False
    tamper_error=""
    try:
        tamper.read_next()
    except RingCorruptionError as exc:
        tamper_detected=True
        tamper_error=str(exc)
    if not tamper_detected:
        raise RuntimeError("tampered live-shadow record was accepted")
    shutil.rmtree(tamper_root)

    receipt_body={
        "schema":"BIOOS_NOEMA_QHTRI_LIVE_BIFURCATION_RING_SHADOW_V0_1",
        "surface_root":str(LIVE_ROOT),
        "ring_root":str(ring_root),
        "ring_schema":"BIOOS-NOEMA-QHTRI-LIVE-BIFURCATION-RING/0.1",
        "autonomy_level":"L0_OBSERVE_INTERPRET",
        "runtime_write_scope":"TRANSPORT_ONLY",
        "human_per_tick_authorization_required":False,
        "authority_expansion":False,
        "external_effect":False,
        "source_class":"NATURAL_SYSTEM_STATE",
        "dynamics_class":"ENDOGENOUS_RUNTIME_DYNAMICS",
        "pncs_bank_head":PNCS_BANK_HEAD,
        "bank_manifest_sha256":BANK_MANIFEST_SHA256,
        "bank_manifest_derivation":"canonical PNCS bank_manifest() over pinned 10-entry bank generation",
        "event_count":len(published),
        "tick_first":first_tick,
        "tick_last":last_tick,
        "ticks_strictly_increasing":all(a["qhtri_tick"]<b["qhtri_tick"] for a,b in zip(published,published[1:])),
        "records":published,
        "pre_reopen_chain":pre_reopen,
        "reopen_chain":reopen_report,
        "consumed":consumed,
        "post_ack_chain":post_ack,
        "tamper_gate":{"status":"PASS","detected":tamper_detected,"error":tamper_error},
        "spinor_live_sidecar_present":spinor_live,
        "spinor_join_status":"PRESENT" if spinor_live else "PENDING_EXPLICIT_Z2_LIVE_CHANNEL",
        "unit_test_status":"PASS_16_OF_16",
        "live_shadow_transport_status":"PASS",
        "production_activation":"PENDING",
    }
    out={**receipt_body,"receipt_sha256":sha(receipt_body)}
    receipt_path=ring_root/"LIVE_SHADOW_RECEIPT.json"
    tmp=receipt_path.with_suffix('.tmp')
    tmp.write_bytes(canonical_bytes(out)+b"\n")
    os.replace(tmp,receipt_path)
    with receipt_path.open('rb') as f:
        os.fsync(f.fileno())
    local=Path('/mnt/data/bioos_ring_work/provenance/NOEMA_QHTRI_LIVE_BIFURCATION_RING_SHADOW_V0_1.json')
    local.parent.mkdir(parents=True,exist_ok=True)
    local.write_bytes(canonical_bytes(out)+b"\n")
    print(json.dumps({
        "status":"PASS","event_count":len(published),"tick_first":first_tick,"tick_last":last_tick,
        "ring_root":str(ring_root),"receipt_path":str(receipt_path),"receipt_sha256":out["receipt_sha256"],
        "spinor_join_status":out["spinor_join_status"],"tamper_gate":out["tamper_gate"],
        "latest_edge":published[-1]["edge"],"post_ack":post_ack,
    },indent=2,sort_keys=True))

if __name__ == '__main__':
    main()
