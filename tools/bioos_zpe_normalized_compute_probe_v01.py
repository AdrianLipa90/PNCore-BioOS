from __future__ import annotations

import argparse
import hashlib
import json
import sys
import shutil
import statistics
import tempfile
import time
from pathlib import Path

import numpy as np

_THIS_ROOT = Path(__file__).resolve().parents[1]
if str(_THIS_ROOT) not in sys.path:
    sys.path.insert(0, str(_THIS_ROOT))

from tools.bioos_zpe_normalized_compute_v01 import (
    CandidateScore,
    RelationalTolerance,
    admit_relational_equivalence,
    relational_metrics,
    select_lowest_compute_work,
)


def stable_snapshot(ns, live_root: Path, dst_parent: Path) -> tuple[Path, int]:
    specs = ns.surface_specs()
    for _ in range(50):
        t0 = int(np.memmap(live_root / "tick", dtype="uint64", mode="r", shape=(1,))[0])
        dst = Path(tempfile.mkdtemp(prefix="bioos_zpe_snapshot_", dir=dst_parent))
        try:
            for spec in specs:
                shutil.copy2(live_root / spec.name, dst / spec.name)
            t1 = int(np.memmap(live_root / "tick", dtype="uint64", mode="r", shape=(1,))[0])
            tc = int(np.memmap(dst / "tick", dtype="uint64", mode="r", shape=(1,))[0])
            if t0 == t1 == tc:
                return dst, tc
        except Exception:
            shutil.rmtree(dst, ignore_errors=True)
            raise
        shutil.rmtree(dst, ignore_errors=True)
        time.sleep(0.01)
    raise RuntimeError("could not obtain a stable live surface snapshot")


def clone_surface(ns, src: Path, parent: Path) -> Path:
    dst = Path(tempfile.mkdtemp(prefix="bioos_zpe_run_", dir=parent))
    for spec in ns.surface_specs():
        shutil.copy2(src / spec.name, dst / spec.name)
    return dst


def reset_runtime(ns) -> None:
    ns._cont_counter = 0
    ns.evolve_surface._curious_idle = 0
    ns._HOLONOMY_CACHE = None


def capture(surface):
    return {
        "phi": np.array(surface["phi"], copy=True),
        "g": np.array(surface["g"], copy=True),
        "holonomy": np.array(surface["holonomy"], copy=True),
        "tick": int(surface["tick"][0]),
    }


def run_reference(ns, src: Path, parent: Path, *, ticks: int, dt: float, continuous: bool):
    dst = clone_surface(ns, src, parent)
    surface = ns.open_surface(dst)
    reset_runtime(ns)
    ns.sync_surface_holonomy(surface)  # cache warm-up outside proxy timing
    c0 = time.process_time()
    for _ in range(ticks):
        ns.evolve_surface(surface, dt=dt, flush=False, continuous=continuous, cont_every=10)
    cpu = time.process_time() - c0
    return dst, capture(surface), cpu, ticks


def run_pure_macro(ns, src: Path, parent: Path, *, ticks: int, dt: float, stride: int):
    if ticks % stride:
        raise ValueError("pure macro test requires ticks divisible by stride")
    dst = clone_surface(ns, src, parent)
    surface = ns.open_surface(dst)
    reset_runtime(ns)
    ns.sync_surface_holonomy(surface)
    calls = 0
    c0 = time.process_time()
    for _ in range(ticks // stride):
        ns.evolve_surface(surface, dt=dt * stride, flush=False, continuous=False, cont_every=10)
        if stride > 1:
            ns._cont_counter += stride - 1
            surface["tick"][0] = int(surface["tick"][0]) + stride - 1
        calls += 1
    cpu = time.process_time() - c0
    return dst, capture(surface), cpu, calls


def run_hybrid_anchor_macro(ns, src: Path, parent: Path, *, ticks: int, dt: float, stride: int):
    dst = clone_surface(ns, src, parent)
    surface = ns.open_surface(dst)
    reset_runtime(ns)
    ns.sync_surface_holonomy(surface)
    calls = 0
    semantic_tick = 0
    c0 = time.process_time()
    while semantic_tick < ticks:
        if ns._cont_counter % 10 == 0:
            ns.evolve_surface(surface, dt=dt, flush=False, continuous=True, cont_every=10)
            semantic_tick += 1
            calls += 1
            continue
        until_anchor = 10 - (ns._cont_counter % 10)
        k = min(stride, until_anchor, ticks - semantic_tick)
        ns.evolve_surface(surface, dt=dt * k, flush=False, continuous=False, cont_every=10)
        if k > 1:
            ns._cont_counter += k - 1
            surface["tick"][0] = int(surface["tick"][0]) + k - 1
        semantic_tick += k
        calls += 1
    cpu = time.process_time() - c0
    return dst, capture(surface), cpu, calls


def score(reference, candidate, tolerance: RelationalTolerance):
    m = relational_metrics(reference["phi"], reference["g"], candidate["phi"], candidate["g"])
    admitted, failures = admit_relational_equivalence(m, tolerance)
    return m, admitted, failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime-root", required=True)
    ap.add_argument("--surface-root", default="/dev/shm/ciel_noema")
    ap.add_argument("--work-root", default="/mnt/data")
    ap.add_argument("--ticks", type=int, default=120)
    ap.add_argument("--dt", type=float, default=0.01)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    sys.path.insert(0, args.runtime_root)
    import ciel_geometry.noema_surface_mmap as ns

    tolerance = RelationalTolerance(
        overlap_min=0.9999,
        phase_rms_max=0.015,
        phase_max_max=0.05,
        coupling_direction_max=0.03,
        coupling_log_scale_max=0.005,
        require_winding_exact=True,
    )
    work_root = Path(args.work_root)
    src, source_tick = stable_snapshot(ns, Path(args.surface_root), work_root)
    created = [src]
    try:
        # Three reference repeats; first state is deterministic and used for metrics.
        pure_refs=[]; pure_cpu=[]
        for _ in range(3):
            d,state,cpu,calls=run_reference(ns,src,work_root,ticks=args.ticks,dt=args.dt,continuous=False); created.append(d); pure_refs.append(state); pure_cpu.append(cpu)
        pure_ref=pure_refs[0]; pure_ref_cpu=statistics.median(pure_cpu)

        hybrid_refs=[]; hybrid_cpu=[]
        for _ in range(3):
            d,state,cpu,calls=run_reference(ns,src,work_root,ticks=args.ticks,dt=args.dt,continuous=True); created.append(d); hybrid_refs.append(state); hybrid_cpu.append(cpu)
        hybrid_ref=hybrid_refs[0]; hybrid_ref_cpu=statistics.median(hybrid_cpu)

        pure_rows=[]; pure_scores=[]
        for stride in (2,3,4,5,6,8,10,12,15,20,30,40,60):
            if args.ticks % stride: continue
            reps=[]
            first=None
            for _ in range(3):
                d,state,cpu,calls=run_pure_macro(ns,src,work_root,ticks=args.ticks,dt=args.dt,stride=stride); created.append(d); reps.append(cpu); first=(state,calls)
            state,calls=first
            m,admitted,failures=score(pure_ref,state,tolerance)
            cpu=statistics.median(reps)
            cs=CandidateScore(f"PURE_STRIDE_{stride}",admitted,cpu,m,calls,args.ticks)
            pure_scores.append(cs)
            pure_rows.append({
                "stride":stride,"calls":calls,"call_reduction_fraction":cs.call_reduction_fraction,
                "cpu_seconds_proxy_median":cpu,"cpu_proxy_ratio":cpu/pure_ref_cpu if pure_ref_cpu else None,
                "admitted":admitted,"failures":list(failures),"metrics":m.__dict__,
            })

        hybrid_rows=[]
        for stride in (2,3,4,5,6,8,9):
            reps=[]; first=None
            for _ in range(3):
                d,state,cpu,calls=run_hybrid_anchor_macro(ns,src,work_root,ticks=args.ticks,dt=args.dt,stride=stride); created.append(d); reps.append(cpu); first=(state,calls)
            state,calls=first
            m,admitted,failures=score(hybrid_ref,state,tolerance)
            cpu=statistics.median(reps)
            hybrid_rows.append({
                "stride":stride,"calls":calls,"call_reduction_fraction":1-calls/args.ticks,
                "cpu_seconds_proxy_median":cpu,"cpu_proxy_ratio":cpu/hybrid_ref_cpu if hybrid_ref_cpu else None,
                "admitted":admitted,"failures":list(failures),"metrics":m.__dict__,
            })

        best=select_lowest_compute_work(pure_scores)
        module_path = _THIS_ROOT / "tools" / "bioos_zpe_normalized_compute_v01.py"
        probe_path = Path(__file__).resolve()
        runtime_surface_path = Path(args.runtime_root) / "ciel_geometry" / "noema_surface_mmap.py"
        runtime_continuous_path = Path(args.runtime_root) / "ciel_geometry" / "phasenav" / "continuous_propagator.py"
        def _file_sha256(path: Path) -> str:
            return hashlib.sha256(path.read_bytes()).hexdigest()

        receipt={
            "schema":"BIOOS_ZPE_NORMALIZED_COMPUTE_CONFIRMATORY_SHADOW_V0_1",
            "source_live_tick":source_tick,
            "ticks":args.ticks,"semantic_dt":args.dt,
            "zpe_pin":"43b981fc9f350ba6e8a8d6c846e4be52737f941d",
            "control_status":"EXPERIMENTAL_CONTROL",
            "tolerance":tolerance.__dict__,
            "physical_energy_measurement":"UNAVAILABLE_IN_THIS_CONTAINER",
            "cost_metric":"PROCESS_CPU_SECONDS_PROXY + CALL_COUNT",
            "pure_reference_cpu_seconds_proxy_median":pure_ref_cpu,
            "hybrid_reference_cpu_seconds_proxy_median":hybrid_ref_cpu,
            "pure_kuramoto_candidates":pure_rows,
            "hybrid_anchor_preserving_candidates":hybrid_rows,
            "selected_pure_candidate":best.candidate_id,
            "selected_pure_call_reduction_fraction":best.call_reduction_fraction,
            "hybrid_any_admitted":any(row["admitted"] for row in hybrid_rows),
            "module_sha256": _file_sha256(module_path),
            "probe_sha256": _file_sha256(probe_path),
            "runtime_source_sha256": {
                "noema_surface_mmap.py": _file_sha256(runtime_surface_path),
                "continuous_propagator.py": _file_sha256(runtime_continuous_path),
            },
            "execution_authority":False,
            "canon_promotion":False,
        }
        canonical=json.dumps(receipt,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
        receipt["receipt_sha256"]=hashlib.sha256(canonical).hexdigest()
        Path(args.output).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps({"source_tick":source_tick,"selected":best.candidate_id,"call_reduction":best.call_reduction_fraction,"hybrid_any_admitted":receipt["hybrid_any_admitted"],"pure_pass":[r["stride"] for r in pure_rows if r["admitted"]],"hybrid_pass":[r["stride"] for r in hybrid_rows if r["admitted"]]},indent=2))
    finally:
        for d in created:
            shutil.rmtree(d, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
