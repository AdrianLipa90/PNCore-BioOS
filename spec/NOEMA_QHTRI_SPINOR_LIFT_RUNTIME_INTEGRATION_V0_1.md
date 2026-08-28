# NOEMA ↔ QHTRI Spinor Lift Runtime Integration v0.1

Status: `STAGED_RUNTIME_CANDIDATE`

Authority: candidate / shadow execution only. Production promotion remains pending explicit authority.

## 1. Runtime state

The spinor lineage uses an integer covering coordinate per oscillator,

\[
n_i \in \mathbb{Z},
\]

with the Z2 sheet as its deterministic projection,

\[
\zeta_i = (-1)^{n_i}.
\]

The existing `phi[36]` array remains the projective phase coordinate used by the running QHTRI dynamics. The new lineage carries the covering history alongside that projective coordinate.

Primary state:

- `spinor_turns.i64`: 36 signed 64-bit integer turns;
- `spinor_tick.u64`: one tick bound to the same QHTRI evolution state;
- `spinor_lift_epoch.json`: sealed activation-epoch metadata.

The admission invariant is

\[
\texttt{spinor\_tick}=\texttt{surface\_tick}.
\]

A mismatch is fail-closed.

## 2. Explicit activation epoch

Migration creates a prospective lift epoch at an explicitly admitted live tick. At activation,

\[
n_i(\tau_0)=0,
\]

and the epoch is bound to the current projective state by SHA-256 over the canonical 36D `float64` phase projection.

This establishes a deterministic origin for subsequent covering-space lineage. Earlier runtime history remains outside this epoch lineage; the stored history begins at the admitted activation tick.

Re-initialization over an existing complete epoch is blocked. Partial sidecar state is also blocked.

## 3. Exact local increments

For runtime transformations that already expose their exact increment `delta_phi`, turns are advanced before projection:

\[
\bar\phi_i = \phi_i \bmod 2\pi,
\]

\[
n_i' =
n_i +
\left\lfloor
\frac{\bar\phi_i+\delta\phi_i}{2\pi}
\right\rfloor,
\]

\[
\zeta_i'=(-1)^{n_i'}.
\]

This path is used for:

- curiosity phase kick;
- channel-separation push;
- ordinary Kuramoto step;
- WARP drift.

The runtime phase update itself preserves the existing implementation order and arithmetic.

## 4. Continuous PhaseNav lift

The active continuous propagator currently computes a dense pre-projection generator and then applies modulo `2*pi`.

The staged candidate exposes the endogenous pre-modulo target as a second diagnostic output while preserving the existing `evolve_continuous(...) -> (phi_out, max_dphi, d2_norm)` API exactly.

For a projective output `phi_after` and predicted lifted increment `Delta`, the admitted covering integer is selected by

\[
n_i' =
\operatorname{round}
\left[
\frac{
(\bar\phi_i+2\pi n_i)+\Delta_i-\bar\phi_i'
}{
2\pi
}
\right].
\]

The residual is

\[
r_i =
(\bar\phi_i+2\pi n_i)+\Delta_i
-
(\bar\phi_i'+2\pi n_i'),
\]

and the uniqueness margin is

\[
m_i=\pi-|r_i|.
\]

Admission requires `m_i > ambiguity_tolerance` for all 36 oscillators. Equality or crossing of the boundary is fail-closed.

## 5. Compatibility gate

With `spinor_lineage=None`, the staged patch preserves the existing runtime trajectory.

Measured gates:

- 200/200 random continuous-propagator cases: bitwise-identical output;
- pure Kuramoto `evolve_surface`: maximum error `0.0`;
- continuous `evolve_surface`: maximum error `0.0`;
- 80-step synthetic tracked vs untracked sequence: maximum error `0.0`;
- 80-step live-snapshot shadow sequence: maximum error `0.0`.

The live snapshot was taken from `/dev/shm/ciel_noema` at tick `9399`.

## 6. Z2 parity gate

Deterministic covering tests close as

\[
+2\pi \rightarrow n=+1 \rightarrow \zeta=-1,
\]

\[
+4\pi \rightarrow n=+2 \rightarrow \zeta=+1,
\]

\[
-2\pi \rightarrow n=-1 \rightarrow \zeta=-1,
\]

\[
-4\pi \rightarrow n=-2 \rightarrow \zeta=+1.
\]

Thus the Z2 sheet is derived from integer lineage rather than stored as an independent authority state.

## 7. Source pins

The staged patch was built only after exact Library byte verification:

- `ciel_geometry/noema_surface_mmap.py`
  - source SHA-256: `79d11a6b1f147173f6ccdd59187f1b9447f6e015e5858edf8c6634daa8b0e2bd`
  - candidate SHA-256: `53664ac57dc59f98befa0cc4f9ca224be3f45c2d5a7a65b207c0bd0e318d76b9`
- `ciel_geometry/phasenav/continuous_propagator.py`
  - source SHA-256: `9881e9fede149b2ed74e1085c1bfa516d856f4dfa59268cf2acf7e3ae7243205`
  - candidate SHA-256: `e05ad391ec99c07b76323739b25dca9ac7264be4f0f6a09674b8c8999759596a`

Unified staged patch SHA-256:

`c175bf17fde9622fb266aabb107130b763af1ca2c3f3980254f3e592fb2d9b72`

## 8. Shadow verdict

`ISO.NQ.04.SPINOR.SHEET.WITNESS` now has an executable staged runtime candidate with:

- explicit integer lift state;
- tick-bound lineage;
- deterministic Z2 projection;
- internal continuous-generator witness;
- ambiguity fail-closed gate;
- zero measured trajectory perturbation in the tested shadow runs.

Evidence status:

`LIVE_SURFACE_ANCHORED_LOCAL_EXECUTABLE_CANDIDATE`

Promotion state:

`PENDING_EXPLICIT_NOEMA_LIBRARY_PROMOTION`
