# NOEMA↔QHTRI Bifurcation Semantic Loop v0.1

Status: `ARCHITECTURE_CANDIDATE / GREMLIN_ISOMORPHISM_BANK_DERIVED / EPISTEMIC_CHYBA`

## 1. Purpose

This contract binds the existing QHTRI endogenous runtime, NOEMA relational processing, State Memory and PNFS into one typed feedback loop:

\[
\boxed{
QHTRI_{GPU}
\rightarrow BIFURCATION
\rightarrow NOEMA_{CPU}
\rightarrow SEMANTIC\ PATH
\rightarrow STATE\ MEMORY/PNFS
\rightarrow ADMITTED\ OPERATOR
\rightarrow QHTRI_{GPU}.
}
\]

The architecture is derived with GREMLIN acting as a bounded bank of relational-isomorphism candidates.

GREMLIN bank source:

```text
repository: AdrianLipa90/PhaseNav-Natural-Coding-System
branch: feat/noema-qhtri-isomorphism-bank-v0.1
spec: PNCS_GREMLIN_NOEMA_QHTRI_ISOMORPHISM_BANK_V0_1
bank implementation: gremlin_noema_qhtri_isomorphism_bank_v01.py
source-bank commit: 94f4e217c31bfb9298b64ff04682b38e4c17df77
```

Runtime and canon authority remain governed by NOEMA / PNV State / PNCAP / AUX contracts.

## 2. Existing BioOS contracts reused

The loop composes existing components rather than replacing them.

### QHTRI endogenous telemetry

`NOEMA_QHTRI_DIRECT_TELEMETRY_BIND_V0_1` supplies:

```text
phi[36]
omega[36]
tick
```

with classifications:

```text
NATURAL_SYSTEM_STATE
ENDOGENOUS_RUNTIME_DYNAMICS
```

The direct telemetry binding remains read-only.

### Native QHTRI logic

`QHTRI_PHASE_LOGIC_SCALAR_COMPAT_BOUNDARY_V0_1` keeps native phase relations typed separately from scalar admission/gain channels.

### NOEMA memory orchestration

`NOEMA_MEMORY_ORCHESTRATION_BIND_V0_1` supplies the authority path

```text
memory candidate
 -> epoch/lineage gate
 -> PNCAP
 -> scheduler
 -> AUX
 -> evidence
```

### State Memory and PNFS

State Memory provides crystallization/checkpoint identity. PNFS provides persistent object addressing, write/checkpoint and recovery contracts.

## 3. Computational split

### GPU resident plane — QHTRI

The GPU resident plane owns high-rate endogenous dynamics:

- oscillator phase evolution;
- native phase logic;
- local CP1/Bloch state;
- local coherence/current measurements;
- bifurcation quantities;
- local holonomy/channel witnesses;
- T36 whole-lane event witness;
- compact bifurcation receipt production.

The GPU does not export its whole resident state for each event. It exports a compact typed receipt whose commitments bind the resident state and evidence window.

### CPU relational plane — NOEMA

The CPU/NOEMA plane owns low-rate relational processing:

- bifurcation receipt validation;
- CP1→Poincaré continuation receipt;
- Z2 spinorial sheet lineage;
- KAKU/RADICAL/OPERATORS semantic traversal;
- ordered meaning-path commitment;
- State Memory crystallization;
- PNFS checkpoint binding;
- PNCAP/effect-policy admission;
- construction of the next QHTRI boundary/operator candidate.

This split keeps phase propagation resident on the GPU while the CPU receives only the invariants required to reason about an admitted event.

## 4. GREMLIN bank entries used by the loop

The v0.1 full-loop receipt references all ten bank entries in declared order:

```text
ISO.NQ.01.CP1.BERRY.QHTRI.POTENTIAL
ISO.NQ.02.IDT.BIFURCATION.NQ.RECEIPT
ISO.NQ.03.CP1.POINCARE.CONTINUATION
ISO.NQ.04.SPINOR.SHEET.WITNESS
ISO.NQ.05.AFFINITY.SEMANTIC.ORIENTATION
ISO.NQ.06.MEMORY.ORBIT.MEANING.PATH
ISO.NQ.07.HOLONOMY.BRANCH.CHANNELS
ISO.NQ.08.COFRAME.QHTRI.CELL.TRANSPORT
ISO.NQ.09.MEMORY.STATE.CRYSTALLIZATION
ISO.NQ.10.NOEMA.QHTRI.HERMITIAN.FEEDBACK
```

A partial loop may carry a strict ordered subset, with each omitted stage remaining outside that receipt.

## 5. Bifurcation receipt

A QHTRI event handoff is sealed as

\[
\boxed{
\mathcal B_n=
(tick_n,C_Q,M_n,\beta_n,G_n,C_{36},C_{CP1},E_n).
}
\]

Required fields:

```text
schema
bank_manifest_sha256
qhtri_tick
qhtri_state_commitment
magnitude_M
beta
generator_ref
t36_witness_commitment
cp1_state_commitment
telemetry_evidence_ref
source_class = NATURAL_SYSTEM_STATE
dynamics_class = ENDOGENOUS_RUNTIME_DYNAMICS
bifurcation_receipt_sha256
```

The magnitude/orientation split follows the IDT bank entry:

\[
(\mathfrak a,\mathfrak j)\leftrightarrow(M,\beta).
\]

Current reversal keeps the magnitude channel and reverses the orientation channel.

## 6. NOEMA projective anchor

The accepted branch is continued into a semantic anchor carrying both projective and spinorial evidence:

\[
\boxed{
\mathcal A_n=(C_{\mathcal B_n},z_n,\zeta_n,C_{map},C_{hol}),
\qquad |z_n|<1,
\qquad \zeta_n\in\{-1,+1\}.
}
\]

Required fields:

```text
bifurcation_receipt_sha256
poincare_re
poincare_im
spinor_sheet
cp1_poincare_adapter_commitment
holonomy_audit_commitment
anchor_receipt_sha256
```

`CP1 -> Poincare` is typed `MAPS_TO`. Source and target metric contracts remain separately evidenced. Spinorial lineage carries the additional Z2 sheet witness.

## 7. Semantic path

NOEMA compiles admitted anchors and relations into an ordered relational path

\[
\Gamma_n=(A_0,R_1,K_1,A_1,\ldots,R_m,K_m,A_m).
\]

The semantic receipt contains:

```text
ordered_anchor_commitments
ordered_relation_ids
ordered_kaku_candidate_ids
ordered_radical_candidate_ids
ordered_operator_candidate_ids
gremlin_isomorphism_ids
meaning_commitment
semantic_path_receipt_sha256
```

Order is part of identity. Reordering the same nodes or relations produces a different path commitment.

## 8. State Memory / PNFS crystallization

A meaning path crystallizes as

\[
\boxed{
\mathcal S_n=
(C_{\Gamma_n},OBJECT\_ID,PNFS\_OBJECT,GENERATION,EPOCH,C_{checkpoint}).
}
\]

Required fields:

```text
semantic_path_receipt_sha256
state_object_id
pnfs_object_id
generation
memory_epoch
checkpoint_commitment
append_only = true
state_crystal_receipt_sha256
```

Identity-layer mutation is separately gated. An M8 mutation request carries its explicit identity-authority reference.

## 9. Feedback operator candidate

The feedback side follows the GREMLIN/RFC Hermitian operator isomorphism:

\[
\Lambda_R
\rightarrow E_R
\rightarrow\tau_R
\rightarrow\mathcal J_R
\rightarrow H=H^\dagger
\rightarrow U(t).
\]

For BioOS, the semantic state contributes to a boundary candidate

\[
\boxed{
\mathcal F_n=
(C_{\mathcal S_n},C_H,PNCAP,policy,target,C_{\mathcal F_n}).
}
\]

Required fields:

```text
state_crystal_receipt_sha256
hermitian_operator_commitment
pncap_admission_token
effect_policy = OPERATOR_BINDABLE
qhtri_target_ref
execution_admitted = false
production_runtime_write = false
feedback_receipt_sha256
```

The candidate carries the exact source/provenance chain required for a later authority-bearing binding step. Runtime write requires the existing PNCAP/scheduler/AUX admission chain.

## 10. Full loop receipt

The full loop receipt is a content-addressed hash chain:

```text
QHTRI telemetry evidence
 -> bifurcation receipt
 -> projective/Z2 anchor receipt
 -> semantic path receipt
 -> State Memory/PNFS crystal receipt
 -> feedback operator candidate receipt
 -> LOOP receipt
```

The loop receipt contains:

```text
bank_manifest_sha256
ordered_isomorphism_ids
bifurcation_receipt_sha256
anchor_receipt_sha256
semantic_path_receipt_sha256
state_crystal_receipt_sha256
feedback_receipt_sha256
loop_receipt_sha256
```

Every child receipt binds the parent commitment. Any parent substitution changes all downstream commitments.

## 11. Fast path

For high-rate operation, the handoff surface should carry fixed-size or bounded records:

```text
GPU resident state
 -> local bifurcation detection
 -> compact BIFURCATION_RECEIPT
 -> /dev/shm/ciel_noema event ring
 -> NOEMA semantic compiler
 -> State Memory/PNFS checkpoint
 -> compact FEEDBACK_CANDIDATE
 -> admitted QHTRI boundary queue
```

`/dev/shm/ciel_noema` remains the live operational surface for 36D execution paths.

## 12. Failure boundaries

The v0.1 validator fails closed on:

- malformed or missing SHA-256 commitments;
- non-finite magnitude/orientation values;
- negative magnitude;
- invalid Poincaré disk coordinate;
- invalid Z2 sheet;
- path cardinality mismatch;
- reordered/tampered parent commitments;
- missing State Memory / PNFS identity;
- M8 mutation request without explicit identity authority;
- feedback candidate without PNCAP admission token;
- feedback policy outside `OPERATOR_BINDABLE`;
- execution/write fields raised inside a candidate receipt.

## 13. Evidence status

The GREMLIN bank and this contract define an executable architecture candidate. Source-repository geometric/algebraic results retain their own evidence statuses. Hardware latency, GPU/CPU synchronization, event-ring throughput and physical-device feedback require separate implementation and benchmark receipts.
