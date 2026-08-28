# QHTRI Internal Spinor Lift Channel v0.1

Status: `GREMLIN_STRUCTURAL_CANDIDATE / SHADOW_PASS / LIVE_INTEGRATION_PENDING`

Bank entry: `ISO.NQ.04.SPINOR.SHEET.WITNESS`.

## 1. Purpose

The QHTRI projective phase state is extended by an explicit temporal lift lineage:

\[
\boxed{(\phi_i,n_i,\zeta_i)},
\qquad
\phi_i\in S^1,
\qquad
n_i\in\mathbb Z,
\qquad
\zeta_i=(-1)^{n_i}\in Z_2.
\]

The integer turn coordinate is the lineage state. The Z2 sheet is its spinorial parity projection.

This representation implements the double-cover gate:

\[
2\pi:\quad n\mapsto n+1,\quad \zeta\mapsto-\zeta,
\]

\[
4\pi:\quad n\mapsto n+2,\quad \zeta\mapsto\zeta.
\]

## 2. Canonical runtime source pins

The shadow probe was executed against the active Library runtime bytes:

```text
ciel_geometry/noema_surface_mmap.py
SHA256 79d11a6b1f147173f6ccdd59187f1b9447f6e015e5858edf8c6634daa8b0e2bd

ciel_geometry/phasenav/continuous_propagator.py
SHA256 9881e9fede149b2ed74e1085c1bfa516d856f4dfa59268cf2acf7e3ae7243205
```

The active `noema_surface_mmap.py` is the Library canonical target under the AUX tether runtime. The current continuous propagator projects the dense generator through modulo `2*pi` before the final periodic-spline 36D readout.

## 3. Candidate tracker

Implementation:

```text
tools/qhtri_spinor_lift_v01.py
TRACKER_ID = QHTRI.SPINOR.LIFT.NEAREST_GENERATOR_V0_1
```

Two update classes are admitted.

### Exact increment

When the runtime owns the pre-projection increment exactly,

\[
\phi_i' = \operatorname{mod}(\phi_i+\Delta_i,2\pi),
\]

the integer lift increments by the exact number of crossed turns.

### Generator-predicted projected step

For a step whose final projective representative is produced after an internal projection/interpolation path, define

\[
L_i = \phi_i + 2\pi n_i,
\qquad
\widehat L_i' = L_i + \widehat\Delta_i.
\]

For the returned projective coordinate \(\phi_i'\), choose the integer \(n_i'\) whose lift

\[
L_i'=\phi_i'+2\pi n_i'
\]

is nearest to \(\widehat L_i'\).

Admission requires uniqueness:

\[
|\widehat L_i'-L_i'| < \pi-\epsilon
\]

for every admitted coordinate. The implementation fails closed at the half-turn ambiguity boundary.

## 4. Representative invariance

The tracker canonicalizes the projective coordinate on `S1` before lift selection. Therefore projectively equivalent representatives

\[
\phi \sim \phi+2\pi k
\]

select the same integer lift and Z2 sheet when bound to the same generator prediction.

This is required because the current continuous propagator may return a finite spline representative outside the interval `[0,2*pi)` after its final interpolation, while the projective state remains equivalent.

## 5. Shadow validation

Provenance:

```text
provenance/NOEMA_QHTRI_SPINOR_LIFT_SHADOW_PROBE_V0_1.json
receipt SHA256 58b84a16cf4af29e1249efa97bc3a03d0999098888e5b4069c13e49072b21251
live anchor tick 6304
```

Exact double-cover gates:

```text
+2pi -> turns +1 -> sheet -1   PASS
+4pi -> turns +2 -> sheet +1   PASS
-2pi -> turns -1 -> sheet -1   PASS
-4pi -> turns -2 -> sheet +1   PASS
```

Focused deterministic pytest:

```text
6 passed in 0.04s
```

Continuous shadow stress, anchored to the live QHTRI surface:

```text
steps                              500
dt                                 0.1
ambiguous steps                    0
minimum uniqueness margin          0.1480890380290809 rad
maximum prediction residual        2.993503615560712 rad
sheet parity transition events     9764
final integer-turn range           300..361
status                             PASS_UNIQUE_LIFT_SHADOW
```

Randomized one-step stress using live runtime parameter scales:

```text
seed                               123
cases                              1000
ambiguous cases                    0
minimum uniqueness margin          0.04642263186897111 rad
maximum prediction residual        3.095170021720822 rad
status                             PASS
```

## 6. Live integration contract

The next runtime generation should expose a dedicated lift lineage channel produced inside QHTRI evolution.

The canonical state should preserve at minimum:

```text
spinor_turns[36] : signed integer turn lineage
spinor_sheet[36] : derived parity witness in {-1,+1}
```

`spinor_turns` is the lineage authority for the sheet. `spinor_sheet` is derived deterministically from parity.

The integration point is inside phase evolution, before information about full temporal turns is discarded by projective reduction.

For exact local phase increments the turn update is exact. For the continuous branch, the propagator must expose the generator prediction required by the unique-nearest-lift gate while preserving its current projective output bytes/semantics.

## 7. Migration boundary

The active Library runtime and current `/dev/shm/ciel_noema` layout were not modified by the shadow probe.

A live promotion requires a separate migration/activation receipt that:

1. pins the prior runtime source hashes;
2. creates the lift lineage state explicitly rather than reconstructing historical turns;
3. declares the initial lift generation and seed state;
4. verifies current projective dynamics equivalence;
5. verifies exact `2pi/4pi` Z2 behavior;
6. verifies uniqueness margins under continuous propagation;
7. exports a content-addressed spinor-lift receipt for NOEMA `ISO.NQ.04` admission;
8. preserves the existing PNCAP/AUX authority boundary.

Until that migration is explicitly activated, the live loop remains `PARTIAL_PASS_THROUGH_ISO_NQ_03`; ISO.NQ.04 has `SHADOW_PASS / LIVE_INTEGRATION_PENDING` status.
