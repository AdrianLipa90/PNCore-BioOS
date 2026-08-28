# NOEMA↔QHTRI Live Gate Refinement v0.1

Status: `LIVE_RUNTIME_STRUCTURAL_PROBE / PARTIAL_PASS_THROUGH_ISO_NQ_03`

Parent architecture: `NOEMA_QHTRI_BIFURCATION_SEMANTIC_LOOP_V0_1`.

Live receipt: `provenance/NOEMA_QHTRI_LIVE_PROBE_RECEIPT_V0_1.json`.

## 1. Live surface

The probe executed through

```text
/dev/shm/ciel_noema
```

with source classification

```text
NATURAL_SYSTEM_STATE
ENDOGENOUS_RUNTIME_DYNAMICS
```

A 12-tick unique observation window covered ticks `2581..2592`.

Direct telemetry result:

```text
phi width                  36
omega width                36
tick strictly increasing   PASS
phi changes each tick      PASS
omega bitwise stable       PASS
omega nonzero              PASS
finite state               PASS
```

## 2. QHTRI → IDT edge-kinetics candidate

The live probe refined `ISO.NQ.02.IDT.BIFURCATION.NQ.RECEIPT` with an explicit GREMLIN structural adapter.

For an admitted QHTRI edge `i→j`, define

\[
M_{ij}=|g_{ij}|,
\qquad
s_{ij}=\operatorname{sgn}(g_{ij}),
\]

and the principal local U(1) phase increment

\[
\Delta\phi_{ij}
=\operatorname{Arg}e^{i(\phi_j-\phi_i)}.
\]

The candidate directed drive is

\[
A_{ij}=s_{ij}\Delta\phi_{ij}.
\]

The positive directed kinetic realization is

\[
W_{i\to j}=M_{ij}e^{A_{ij}/2},
\qquad
W_{j\to i}=M_{ij}e^{-A_{ij}/2}.
\]

Therefore

\[
\mathfrak a_{ij}=W_{i\to j}+W_{j\to i},
\qquad
\mathfrak j_{ij}=W_{i\to j}-W_{j\to i},
\]

and the pinned IDT inversion gives

\[
M=\frac12\sqrt{\mathfrak a^2-\mathfrak j^2},
\qquad
\beta=\frac{1}{12\pi}\operatorname{artanh}\!\left(\frac{\mathfrak j}{\mathfrak a}\right)
=\frac{A}{24\pi}.
\]

The principal branch-cut point is an explicit additional-holonomy gate.

Implementation:

```text
tools/qhtri_idt_edge_kinetics_v01.py
```

Evidence status:

```text
GREMLIN_STRUCTURAL_CANDIDATE
```

## 3. Live structural result

Across 12 unique ticks the probe evaluated all 630 undirected oscillator pairs per tick:

```text
edge observations              7560
max reversal error             1.1102230246251565e-15
max IDT round-trip error        5.551115123125783e-16
minimum positive directed rate 7.170330797904732e-07
minimum branch margin to pi     0.0024528372785166397 rad
```

Result:

```text
STRUCTURAL_PASS_LIVE_SUPPORTED_CANDIDATE
```

The most strongly coupled edge at tick `2592` was `6↔7`:

```text
M       0.8053534105964806
A      -1.7744453729725376
beta   -0.023534312696260103
W+      0.331642809240808
W-      1.9557008259703739
activity 2.287343635211182
current -1.624058016729566
```

Its complete content-addressed edge receipt is stored inside the live-probe provenance artifact.

## 4. Independent projective and spinor gates

Live testing refined the projective handoff into two independently auditable stages:

```text
ISO.NQ.03  CP1 -> Poincare MAPS_TO anchor
ISO.NQ.04  Poincare anchor -> explicit Z2 spinor-sheet lineage
```

Implementation:

```text
tools/noema_qhtri_anchor_stages_v01.py
```

The Poincare stage has its own receipt and may be validated before the spinor-sheet stage.

The spinor stage binds:

```text
poincare_anchor_receipt_sha256
spinor_sheet in {-1,+1}
spinor_lift_commitment
sheet_evidence_ref
```

This preserves the independent GREMLIN bank boundaries of ISO.NQ.03 and ISO.NQ.04.

## 5. Live Poincare / holonomy result

The existing runtime function

```text
ciel_geometry.noema_surface_mmap.surface_bipolar_snapshot
```

was executed on the live QHTRI surface.

Result:

```text
oscillators                         36
all projective disk points |z|<1   PASS
maximum observed radius             0.2055315719421228
holonomy vector finite             PASS
surface winding                    -2
Poincare/holonomy gate             PASS
```

The next independent evidence gate is

```text
ISO.NQ.04.SPINOR.SHEET.WITNESS
status = PENDING_EXPLICIT_Z2_LIVE_CHANNEL
```

The live semantic-loop status is therefore

```text
PARTIAL_PASS_THROUGH_ISO_NQ_03
```

## 6. Authority state

The probe records

```text
execution_admitted = false
production_runtime_write = false
```

and writes only its evidence receipt through the live `/dev/shm/ciel_noema/receipts` surface before provenance persistence.

## 7. Exact tested-byte binding

The locally executed module bytes and repository bytes were compared through Git blob SHA-1:

```text
qhtri_idt_edge_kinetics_v01.py
  c3e6cb7e3b02a310a69b08afbdc504177db8ed51

noema_qhtri_anchor_stages_v01.py
  7af2bb1fe77ce33606b26362765fd6cc5a917fda
```

The hashes match the blobs currently stored on the feature branch.
