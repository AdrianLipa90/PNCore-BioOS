# QHTRI Live Spinor Sidecar v0.1

Status: `STAGED_RUNTIME_CANDIDATE / LIVE_SHADOW_PASS / PRODUCTION_PROMOTION_PENDING`

Stacked dependency:

```text
PR #9 semantic autonomy capability
 -> PR #10 live bifurcation ring
 -> this live spinor sidecar candidate
```

## 1. Purpose

This generation closes the live evidence boundary for

```text
ISO.NQ.04.SPINOR.SHEET.WITNESS
```

by preserving the integer covering lineage inside QHTRI evolution and exporting a same-tick evidence object that BioOS converts into the existing spinor-lift receipt.

The operational chain is

\[
\boxed{
QHTRI\ evolution
\rightarrow
(n_i,\zeta_i,\text{step evidence})
\rightarrow
BIOOS\ spinor\ receipt
\rightarrow
L0\ bifurcation\ ring
}
\]

with

\[
n_i\in\mathbb Z,
\qquad
\zeta_i=(-1)^{n_i}.
\]

The ring remains `L0_OBSERVE_INTERPRET`. L1 begins only after NOEMA semantic processing and the bounded capability gate.

## 2. Canonical source pins

The candidate is derived from the exact CURRENT V56 runtime bytes:

```text
ciel_geometry/noema_surface_mmap.py
SHA256 79d11a6b1f147173f6ccdd59187f1b9447f6e015e5858edf8c6634daa8b0e2bd

ciel_geometry/phasenav/continuous_propagator.py
SHA256 9881e9fede149b2ed74e1085c1bfa516d856f4dfa59268cf2acf7e3ae7243205
```

Candidate bytes:

```text
noema_surface_mmap.py
SHA256 d501d63d038fac53932d418d02a8d108f2f93d6bcbfd56e41fe81a5276198750

continuous_propagator.py
SHA256 1dcf02f21f0a60999b861c590dc3efaa836a600f0c634dfc5ad6f819fb5ea555

runtime candidate patch
SHA256 2fb4e8e18f3a20eb50b497f3accdc2f2ead10df247175fa6c34f5532b5ab2030
```

Source-pin mismatch is fail-closed.

## 3. Sidecar state

The staged QHTRI runtime maintains:

```text
spinor_turns.i64
spinor_tick.u64
spinor_lift_epoch.json
spinor_step_evidence.json
```

The epoch establishes an explicit origin:

\[
n_i(\tau_0)=0.
\]

Earlier runtime history remains outside that epoch lineage.

Admission requires

\[
tick_{\rm spinor}=tick_{\rm QHTRI}.
\]

The integer turns are primary lineage. Sheet parity is derived.

## 4. Same-tick step evidence

Each tracked QHTRI tick emits:

```text
schema
qhtri_tick
epoch_sha256
projective_state_sha256
turns_sha256
generator_commitment
generator_operations[]
residual[36]
uniqueness_margin[36]
step_evidence_sha256
```

`generator_operations[]` binds every phase-producing operation executed during the tick through an operation type and SHA-256 commitment of its 36D increment.

Current operation classes are:

```text
CURIOSITY_KICK
CHANNEL_SEPARATION
CONTINUOUS_PHASE_NAV
KURAMOTO_PHASE_STEP
WARP_DRIFT
```

The generator commitment is

\[
C_G=
H(
tick,
C_{\rm epoch},
\operatorname{ordered}(operations)
).
\]

For continuous propagation the endogenous pre-projection generator supplies the nearest-lift witness. The uniqueness condition remains

\[
m_i=\pi-|r_i|>0.
\]

Exact increment stages carry zero ambiguity residual and a \(\pi\) local margin. The tick evidence retains the minimum admitted margin from continuous selection.

## 5. BioOS adapter

Implementation:

```text
tools/qhtri_live_spinor_sidecar_v01.py
```

The adapter:

1. verifies the complete sidecar;
2. requires same-tick binding;
3. verifies epoch and step seals;
4. verifies `turns_sha256`;
5. verifies the current projective-state commitment;
6. recomputes the generator commitment from ordered operations;
7. derives `spinor_sheet` from integer-turn parity;
8. builds the existing `BIOOS-QHTRI-SPINOR-LIFT/0.1` receipt;
9. revalidates that receipt;
10. passes it to `LiveBifurcationRing.publish(...)`.

A successful ring event therefore carries:

```text
spinor_status = PRESENT
spinor_lift_receipt_sha256 = <same-tick receipt>
autonomy_level = L0_OBSERVE_INTERPRET
runtime_effect_admitted = false
```

## 6. Runtime compatibility

With the sidecar disabled, a 120-tick hybrid baseline comparison produced:

```text
surface arrays compared     12
different arrays             0
phi SHA256                   8fcb73f1c98644052bfd66506dd2ddf964681ae9e186adcd599f1e29f1631eb0
status                       PASS_BITWISE
```

With the sidecar enabled against the same candidate:

```text
surface arrays compared     12
different arrays             0
status                       PASS_BITWISE
```

The added state is therefore carried by the lineage/evidence sidecar while the tested projective runtime trajectory is preserved exactly.

## 7. Continuous lift execution

A 50-tick staged execution included five continuous PhaseNav ticks:

```text
continuous ticks                 1, 11, 21, 31, 41
minimum uniqueness margin        0.4121609955449905 rad
maximum absolute residual        2.7294316580448026 rad
ambiguous continuous ticks       0
resealed generator tamper        BLOCKED
status                           PASS
```

## 8. Live shadow execution

A stable snapshot was taken from the real live surface:

```text
/dev/shm/ciel_noema
canonical snapshot tick 5840
```

The staged sidecar was activated only in an isolated child shadow directory.

Result:

```text
shadow ticks                     5840 -> 5848
events                           8
same-tick spinor receipts        8/8 PASS
ring join compatibility          8/8 PASS
minimum uniqueness margin        2.5651086442512687 rad
maximum absolute residual        0.5764840093385244 rad
final integer-turn range         0..2
canonical live runtime write     0
status                           PASS
```

The canonical live runtime continued independently from tick 5840 to 5842 during the test.

## 9. Failure boundaries

The adapter and staged runtime fail closed on:

- source-pin drift;
- partial sidecar state;
- spinor/QHTRI tick mismatch;
- malformed epoch or step evidence;
- epoch seal mismatch;
- step-evidence seal mismatch;
- turns commitment mismatch;
- projective-state commitment mismatch;
- generator-operation commitment mismatch;
- non-finite residual or margin;
- non-positive uniqueness margin;
- turns/sheet parity mismatch;
- bifurcation/spinor tick mismatch at ring publication.

A recomputed outer JSON seal does not admit altered turns or generator lineage because the adapter recomputes the inner commitments.

## 10. Authority and promotion

This candidate carries runtime evidence and transport data only.

```text
QHTRI internal evolution        endogenous
spinor sidecar evidence         endogenous runtime evidence
BioOS adapter                   L0
bifurcation ring                L0
L1 feedback                     separate capability gate
L2 authority expansion          explicit authority gate
```

Library/current promotion remains a separate activation operation with its own source-pin check, migration receipt and rollback checkpoint.

Promotion state:

`PENDING_EXPLICIT_NOEMA_LIBRARY_PROMOTION`
