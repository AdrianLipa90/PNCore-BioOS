# BioOS GREMLIN Canon Binding v0.6

Status: `IMPLEMENTED CANDIDATE / HOST-CONFORMANCE PASS / CI INFRASTRUCTURE GATE`

Parent BioOS line: `feat/bioos-v0.5-qhtri-m0-m11-analog-gates`

Pinned BioOS parent commit:

`9e7724a481a90845485854ad28a3866be0e2caf5`

Pinned GREMLIN canonical authority commit:

`76a2d6b46e485723eeaa0a97badd2dae6b9b3b14`

Pinned GREMLIN ledger:

`spec/GREMLIN_NEUTRINO_CANON_LEDGER_V2_4.md`

Pinned ledger blob SHA:

`13c058b095ff734512dab1de8455eb73eeb637e2`

Machine-readable BioOS canon pin:

`provenance/BIOOS_GREMLIN_CANON_PIN_V0_6.json`

Pin manifest commitment:

`58d435575368c6fedc794d5d620c2b1adeec71f37b369773ad340c0c854e2ea8`

## Purpose

v0.6 binds GREMLIN canonical neutrino knowledge to the BioOS M0-M11 semantic/execution architecture. GREMLIN remains the pinned canon authority, while BioOS carries typed claim identity, provenance, validation frontiers, M11 firewalls and M10 receipts.

The flow is

```text
GREMLIN canonical ledger
 -> exact provenance pin
 -> machine-readable canon manifest
 -> BioOS Canon Binding IR
 -> M0-M11 semantic/enforcement mapping
 -> M4/M11 runtime validation frontier
 -> M10 append-only receipt
```

The canon source is consumed in `PINNED_READ_ONLY_CANON_SOURCE` mode.

## Canon claims

### C-Nu-1 — complex-overlap frame bridge

Canonical relation:

\[
(C_\nu I)_\alpha=\langle S_{\nu_\alpha}|I\rangle,
\qquad
J_m=U_{\rm PMNS}^\dagger C_\nu.
\]

BioOS binding:

```text
semantic:    M3, M6, M9
enforcement: M4, M10, M11
```

The binding requires both:

```text
SOURCE_BOUND_ORTHONORMAL_NEUTRINO_FRAME
PMNS_ORIENTATION_BOUND
```

When both are present the candidate becomes `READY_FOR_SEPARATE_M4_RUNTIME_VALIDATION`. Runtime execution remains a separate validation/admission step.

### C-Nu-2 — probability-shadow firewall

\[
R_\alpha=|\langle S_{\nu_\alpha}|I\rangle|^2
\]

is carried as a relational probability shadow while the complex overlap retains relative phase.

BioOS binding:

```text
semantic:    M6
enforcement: M10, M11
effect:      KNOWLEDGE_FIREWALL_NO_DIRECT_EFFECT
```

### C-Nu-3 — cross-framework spectrum holonomy firewall

The current exact branch marker is

\[
2\ne\sqrt{7/6}.
\]

BioOS binding:

```text
semantic:    M9, M11
enforcement: M4, M10, M11
```

A request that treats the two branch-local absolute spectra as one shared-authority spectrum activates:

```text
M11_NO_GO = true
M4_CANDIDATE_ADMITTED = false
EXECUTION_ADMITTED = false
```

Branch-local evidence is retained for both graded-projection and TIR/Metatime tetrahedron branches.

## Machine-readable canon pin

The JSON manifest binds in one deterministic object:

```text
GREMLIN canon commit
GREMLIN ledger blob SHA
C-Nu-1..3 ordered status set
C-Nu parent commits
open-debt set
BioOS v0.5 parent commit
M0-M11 layer map
M10/M11 authority mode
```

Its canonical JSON is sealed by

```text
SHA256("BIOOS-GREMLIN-CANON-PIN/v0.6\0" || canonical_json(core))
```

and must equal

`58d435575368c6fedc794d5d620c2b1adeec71f37b369773ad340c0c854e2ea8`.

The compiled Python contract reconstructs the same manifest independently and exact-compares the canonical JSON. A content change or commitment change activates fail-closed validation.

## Authority firewall

The binding invariant is:

```text
canon_source_can_be_rewritten_by_bioos = false
authority_grant = false
execution_admitted = false
production_runtime_write = false
m10_append_only = true
m11_fail_closed = true
```

BioOS consumes and binds the pinned canonical knowledge. Promotion, supersession, or alteration of `C-Nu-*` authority follows a new provenance-bearing GREMLIN/SoT action.

## Receipt

`BIOOS_GREMLIN_CANON_BINDING_M10_RECEIPT_V0_6` binds:

- canonical GREMLIN commit;
- canonical ledger blob SHA;
- machine-readable canon manifest commitment;
- BioOS v0.5 parent commit;
- v0.6 binding commitment;
- evidence references;
- append-only authority state.

## Open debts retained

```text
NEUTRINO_FRAME_TO_H_I_SOURCE_BINDING
NEUTRINO_SPECTRUM_CROSS_FRAMEWORK_HOLONOMY
```

These remain first-class M11/M10-visible debts.

## Validation status

Current repo-local host conformance for the machine-readable pin extension:

```text
python compile: PASS
v0.6 unittest: 8/8 PASS
failures: 0
errors: 0
```

The GitHub Actions runs observed before this extension failed before checkout with `runner_id=0` and `steps=[]`; the existing provenance receipt records that infrastructure state. The updated branch intentionally triggers a fresh workflow run so the CI gate can be re-evaluated on the new head.

## Promotion gate

v0.6 remains a BioOS candidate until the GitHub Actions infrastructure gate supplies a completed runner execution for the exact promoted head, including the dependent v0.5 regression surface. Promotion to BioOS canon or merge to `main` is a separate explicit action.
