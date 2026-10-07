# NOEMA ↔ QHTRI Spinor Lift Runtime Integration v0.2

Status: `STAGED_RUNTIME_CANDIDATE / LIVE_SNAPSHOT_SHADOW_PASS / PROMOTION_PENDING`

## Purpose

Provide the missing endogenous covering-space lineage required by the live bifurcation ring while preserving the existing projective QHTRI trajectory.

The primary covering coordinate is

\[
n_i\in\mathbb Z,
\qquad
\zeta_i=(-1)^{n_i}.
\]

The runtime keeps the existing `phi[36]` projective phase and adds a tick-bound sidecar:

```text
spinor_turns.i64      36 × signed int64
spinor_tick.u64       one uint64 tick
spinor_lift_epoch.json sealed activation epoch
```

The invariant is

\[
\texttt{spinor_tick}=\texttt{surface_tick}.
\]

Mismatch and partial sidecar state fail closed.

## Generation identity

v0.2 is a new candidate generation. The earlier v0.1 candidate source artifact was not present as recoverable bytes in Library, so v0.2 does not claim byte identity with v0.1.

The v0.2 patch is reproducible only from these exact source files:

```text
ciel_geometry/noema_surface_mmap.py
  source sha256 = 79d11a6b1f147173f6ccdd59187f1b9447f6e015e5858edf8c6634daa8b0e2bd

ciel_geometry/phasenav/continuous_propagator.py
  source sha256 = 9881e9fede149b2ed74e1085c1bfa516d856f4dfa59268cf2acf7e3ae7243205
```

Patch artifact:

```text
runtime_candidates/qhtri_spinor_v02/QHTRI_SPINOR_RUNTIME_V0_2.patch
sha256 = 449438aa38b019be1612342619edbb370c3e97e1562a22331be18f0ef8c729fa
```

Generated candidates:

```text
ciel_geometry/noema_surface_mmap.py
  candidate sha256 = ae1edfe99b929441c0d217f0af430b3721e6242149d0e91bcd54e83a2c3cda99

ciel_geometry/phasenav/continuous_propagator.py
  candidate sha256 = 1dcf02f21f0a60999b861c590dc3efaa836a600f0c634dfc5ad6f819fb5ea555
```

The candidate hash manifest is

```text
7abaadfa7fbea0abd0b1bd54f77150847e57e9851b5b69ece508a97eca9a00d9
```

`tools/qhtri_spinor_runtime_patch_v02.py` verifies source hash, patch hash and candidate hashes. Any mismatch aborts generation and removes the incomplete output tree.

## Activation epoch

Activation is explicit and begins at the current admitted QHTRI tick:

\[
n_i(\tau_0)=0.
\]

The epoch receipt binds the activation tick and SHA-256 of the exact little-endian `float64[36]` projective phase state. Earlier turns remain outside this epoch lineage.

Re-initialization over a complete existing epoch is blocked. A partial state unit is also blocked.

## Exact local increments

For runtime transformations exposing their local increment \(\Delta_i\), v0.2 updates covering turns before projective reduction:

\[
\bar\phi_i=\phi_i\bmod2\pi,
\]

\[
n'_i=n_i+\left\lfloor\frac{\bar\phi_i+\Delta_i}{2\pi}\right\rfloor.
\]

This path covers:

- curiosity kick;
- channel-separation push;
- ordinary Kuramoto phase step;
- WARP drift.

## Continuous PhaseNav path

The public API remains

```text
evolve_continuous(...) -> (phi_out, max_dphi, d2_norm)
```

v0.2 additionally retains an internal diagnostic derived from the endogenous pre-modulo dense target. It provides a 36D predicted lift increment without changing the public return tuple.

For projective output \(\bar\phi_i'\), the covering integer is selected by nearest lifted continuation:

\[
n_i'=\operatorname{round}\left(
\frac{(\bar\phi_i+2\pi n_i)+\Delta_i-\bar\phi_i'}{2\pi}
\right).
\]

Residual and uniqueness margin are

\[
r_i=(\bar\phi_i+2\pi n_i)+\Delta_i-(\bar\phi_i'+2\pi n_i'),
\]

\[
m_i=\pi-|r_i|.
\]

Admission requires all margins to remain strictly above the configured ambiguity tolerance. Boundary or non-finite values fail closed.

## Compatibility evidence

With spinor lineage disabled, v0.2 was compared against the exact pinned canonical V3 source:

```text
continuous propagator: 200/200 bitwise-identical
pure evolve_surface:   250/250 steps bitwise-identical
hybrid evolve_surface: 250/250 steps bitwise-identical
max measured difference: 0.0
```

The 250-step comparisons included the existing phase, coupling, gravity, holonomy and tick outputs.

With lineage enabled on the same v0.2 runtime:

```text
hybrid tracked vs untracked: 250/250 bitwise-identical
final tick: 250
turn range: 30..39
Z2 -1 axes: 17/36
max trajectory difference: 0.0
```

A separate integrity probe passed deterministic ±2π/±4π parity, reopen, tick-mismatch rejection and partial-state rejection.

## Current live-snapshot shadow gate

A stable snapshot was taken from the active `/dev/shm/ciel_noema` surface at tick `2652` after canonical AutoBoot V3 returned ACTIVE.

Baseline canonical V3 and v0.2 with spinor tracking were evolved for 80 equal hybrid steps from separate copies of that snapshot:

```text
trajectory equality: bitwise PASS
max difference: 0.0
final tick: 2732
turn range: 8..12
Z2 -1 axes: 19/36
```

This is a live-surface-anchored shadow result. The active QHTRI producer was not modified.

## Bifurcation-ring dependency

The live ring uses `require_spinor=true`. A real attachment probe under `/dev/shm/ciel_noema/bifurcation_ring_v01` correctly rejected publication while the canonical runtime lacked this native sidecar:

```text
expected rejection: spinor lift receipt required
next_sequence = 0
slots = 0
consumer cursor = -1
```

After production promotion of this runtime candidate, the next gate is native spinor receipt emission at the same QHTRI tick followed by positive ring publication and NOEMA L0 consumption.

## Promotion boundary

This branch contains a staged, reproducible candidate. It does not modify NOEMA Library CURRENT and does not replace the active `/dev/shm` runtime. Production promotion is a separate explicit step.
