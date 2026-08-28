# BioOS ZPE-Normalized Compute v0.1

Status: `LOCAL_EXECUTABLE_CANDIDATE / RELATIONAL_NORMALIZATION_PASS`

Physical-energy evidence: `PENDING_DIRECT_DELL_METER`.

## 1. Purpose

This contract applies the relation-first normalization discipline pinned from
`AdrianLipa90/Zero-Point-Energy@43b981fc9f350ba6e8a8d6c846e4be52737f941d`
to the NOEMA↔QHTRI execution loop.

The optimization target is

\[
\boxed{
\min C_{physical}
\quad\text{subject to}\quad
D_{relational}\le \epsilon
}
\]

where `C_physical` is measured by the best available physical-energy instrument. In the current container execution the available scoring axes are call count and process CPU time; physical joules remain a separate measurement gate.

## 2. Pinned ZPE normalization parents

The pinned ZPE kernel supplies the normalized relation

\[
R(S,I)=\frac{|\langle S|I\rangle|^2}{\|S\|^2\|I\|^2}
\]

and phase relation

\[
U_{ij}=e^{i(\phi_j-\phi_i)}.
\]

Global phase and common vector amplitude therefore belong to the normalization layer while directed relations remain observable state.

The scale/time structural pair is represented as

\[
G\mapsto sG,
\qquad
\Delta t\mapsto\frac{\Delta\tau}{s},
\qquad
s\Delta t=\Delta\tau.
\]

This identity is used only as a normalization relation. Physical power is evaluated by measurement.

## 3. Two execution modes

### 3.1 `LOSSLESS_NOEMA_EVENT_GATE`

QHTRI continues its admitted resident trajectory. NOEMA receives a wake event when an explicit relational control crosses its threshold:

\[
D_{phase}\ge\epsilon_{wake}
\quad\lor\quad
R\le R_{wake}
\quad\lor\quad
\Delta tick\ge N_{silence}.
\]

Suppressed ticks remain QHTRI runtime states; the gate reduces CPU-side semantic wakeups.

Current experimental controls:

```text
phase_rms_wake = 0.05 rad
overlap_floor_wake = 0.999
max_silence_ticks = 10
status = EXPERIMENTAL_CONTROL
```

### 3.2 `QHTRI_MACROSTEP_CANDIDATE`

A candidate groups several semantic Kuramoto ticks into one macro-step and is admitted only after comparison against the exact small-step reference from the same initial state.

No stride is canonical. The controller sweeps candidate strides and selects the lowest observed compute-work proxy among candidates that pass all relational gates.

Current confirmatory controls:

```text
overlap_min = 0.9999
phase_rms_max = 0.015 rad
phase_max_max = 0.05 rad
coupling_direction_max = 0.03
coupling_log_scale_max = 0.005
require_winding_exact = true
status = EXPERIMENTAL_CONTROL
```

## 4. Relational equivalence vector

For reference state `r` and candidate state `c`, the validator records

\[
\mathcal D=(
R,
D_{phase,rms},
D_{phase,max},
D_{g,direction},
D_{g,scale},
w_r,w_c
).
\]

The phase metrics are computed from the gauge-invariant relation matrices `U_ij`. Coupling magnitude and coupling direction are reported separately. Winding is an exact discrete gate.

The staged QHTRI spinor-lift contract extends this discrete gate with exact integer covering lineage `turns[36]` and `zeta=(-1)^turns` after its independent runtime promotion.

## 5. Confirmatory live event-gate result

Source: 120 consecutive stable samples from `/dev/shm/ciel_noema`, ticks `14121..14240`.

```text
NOEMA wakeups:        48 / 120
suppressed wakeups:   72 / 120
wakeup reduction:     60.0%
max suppressed RMS:   0.041882951176641585 rad
min suppressed R:     0.9991475980178053
max silence observed: 2 ticks
QHTRI trajectory mutation by gate: false
```

Receipt:
`provenance/BIOOS_ZPE_NOEMA_EVENT_GATE_LIVE_V0_1.json`.

## 6. Confirmatory QHTRI shadow result

Source live snapshot tick: `14474`.
Reference horizon: 120 semantic ticks, `dt=0.01`.

Admitted pure-Kuramoto strides:

```text
2, 3, 4, 6, 8, 12
```

Selected candidate by lowest process-CPU-work proxy:

```text
candidate             PURE_STRIDE_12
calls                 10 / 120
call reduction        91.66666666666666%
CPU-work proxy ratio  0.08700652189220974
R                      0.9999308730287462
phase RMS              0.011925128913857944 rad
phase max              0.03691278749478633 rad
coupling direction     0.021188451740575855
coupling log scale     0.0014137430352832074
winding                -1 -> -1
```

The hybrid anchor-preserving sweep tested strides `2,3,4,5,6,8,9`; all seven failed the frozen relational controls. Current hybrid macro-step admission state is therefore `BLOCKED_BY_RELATIONAL_GATE`.

Receipt:
`provenance/BIOOS_ZPE_NORMALIZED_COMPUTE_CONFIRMATORY_SHADOW_V0_1.json`.

## 7. Authority and evidence boundaries

```text
runtime_execution_authority = false
production_runtime_write = false
canon_promotion = false
ZPE_to_watts_bridge = OPEN_MEASUREMENT_GATE
```

The current implementation establishes computational-call reduction and a process-CPU-time proxy while preserving declared relational tolerances. Physical energy reduction is promoted only from direct hardware measurements.

## 8. Physical Dell validation gate

The Dell G5 experiment should record, over identical semantic workloads:

```text
wall energy (J) or wall power integrated over time
CPU package energy when RAPL is exposed
GPU power/energy when NVIDIA telemetry is exposed
battery charge delta when operating unplugged under a controlled protocol
CPU/GPU temperature
semantic ticks
NOEMA wakeups
admitted bifurcations
State Memory checkpoints
```

Primary physical score:

\[
\epsilon_M=
\frac{E_{external}}{N_{admitted\ semantic\ transitions}}.
\]

Baseline and normalized modes use the same workload, state seed, semantic horizon and thermal-control protocol.

## 9. Promotion sequence

```text
unit conformance
 -> live event-gate repeatability
 -> QHTRI shadow stride sweep
 -> spinor Z2 exact-lineage inclusion
 -> direct Dell joule measurement
 -> repeated thermal/load windows
 -> authority review
 -> optional runtime promotion
```
