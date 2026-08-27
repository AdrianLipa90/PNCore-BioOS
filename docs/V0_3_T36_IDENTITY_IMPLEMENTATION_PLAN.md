# PNCore-BioOS v0.3 — T36 Identity Genesis Implementation Plan

Status: ACTIVE_FEATURE_BRANCH / IMPLEMENTATION_FRONTIER
Branch: `feat/bioos-v0.3-t36-identity-genesis`
Base: `feat/bioos-v0.2.9-convergence`
Epistemic operator: CHYBA
Canon allowed: false

## Goal

Close one end-to-end identity lineage before adding higher cognitive layers:

```text
RESET
 -> PNROM
 -> PNCore
 -> exact clock admission
 -> PNVH 36D verification
 -> PNStore recovery
 -> T36 cold genesis or verified continuation
 -> T36 identity record
 -> State Memory lineage
 -> Sigma_0
 -> checkpoint
 -> PAUX / optional DNCrypt / PNStore
 -> reboot
 -> same CRYSTAL_ID
```

The completion criterion is continuity of one persistent crystal identity through a real recovery cycle, not the mere presence of a new object in source code.

## Stage 0 — numerical and binary contract

Implemented on this branch:

- `spec/T36_IDENTITY_CRYSTAL_V0_1.md`
- `native/T36_IDENTITY_GENESIS_V0_1.pnv`
- `tools/t36_identity_record_v01.py`
- `tests/test_t36_identity_v01.py`
- `spec/TORSION_INTEGRATOR_BUDGET_V0_1.md`
- `native/TORSION_INTEGRATOR_BUDGET_V0_1.pnv`
- `provenance/T36_IDENTITY_NUMERICAL_AUDIT_V0_1.json`

Numerical closure:

```text
7.83 Hz B0
 -> one 2*pi projective step per base tick
 -> SU(2) sign reversal after one tick
 -> full 4*pi lifted return after two ticks
 -> 3.915 Hz
 -> exact scheduler B1 cadence
```

## Stage 1 — PNCore physical carrier

Implement x86_64 materialization of the exact 256-byte T36 identity record.

Expected additions:

```text
arch/x86_64/pncore/t36_identity.S
spec/T36_IDENTITY_X86_64_REALIZATION_V0_1.md
provenance/T36_IDENTITY_X86_64_BUILD_RECEIPT_V0_1.json
```

Required operations:

- validate exact record header and length;
- expose phase_index / boot_epoch;
- derive `spinor_sheet = phase_index & 1`;
- compare recovered and current `CRYSTAL_ID` fail-closed;
- never derive identity from address/path/program location;
- never silently create a second genesis anchor.

Gate:

```text
HOST_BUILD
+ byte-exact codec cross-check
+ malformed-record rejection
+ identity/configuration separation tests
```

## Stage 2 — Genesis and recovery integration

Extend the existing PNCore convergence path so recovery precedes identity creation.

```text
PNStore recover
 -> existing crystal lineage?
    YES -> BOOT_CONTINUATION
    NO  -> explicit COLD_GENESIS admission
```

Required receipt fields:

```text
crystal_id
genesis_anchor_commitment
configuration_sha256
phase_index
spinor_sheet
boot_epoch
parent_state_object_id
recovery_generation
cold_genesis: true|false
```

A powered-off interval is represented by `BOOT_GAP`; no hidden phase samples are synthesized.

## Stage 3 — PNV-State-Memory lineage bind

Target external repo: `AdrianLipa90/PNV-State-Memory`.

Add identity envelope fields without replacing State Memory object identity:

```text
crystal_id
boot_epoch
phase_index
configuration_sha256
transition_kind
```

Transition kinds:

```text
CRYSTAL_GENESIS
CRYSTAL_CHECKPOINT
BOOT_CONTINUATION
BOOT_GAP
CONFIGURATION_CHANGE
```

Persistence remains:

```text
OBJECT -> RECEIPT -> CURRENT
```

No per-tick durable object is generated.

Gate:

```text
cold genesis
 -> checkpoint
 -> simulated restart
 -> recover
 -> same CRYSTAL_ID
 -> new descendant object
 -> valid parent receipt
```

## Stage 4 — PAUX / PNStore closure

Bind the T36 identity envelope into the existing persistent AUX carrier.

Requirements:

- preserve State Memory `OBJECT_ID` and integrity identity;
- persist identity record/checkpoint only on admitted transition;
- exact 256-byte base record remains independent of transport path;
- verify payload fits the current PNStore generation extent after all envelope overhead;
- measure exact encoded size rather than relying on theoretical base64 estimates.

If DNCrypt is enabled, its role is envelope confidentiality/integrity and provenance binding; encryption does not become canonical object identity.

## Stage 5 — Identity NEXUS

Bind to the existing Consciousness Dictionary compiled 36D states.

Current external authority:

```text
repo: AdrianLipa90/The-Consciousness-Dictionary
compiled states: 548
compiled declared relations: 306
vector width: 36
```

NEXUS runtime state:

```text
CRYSTAL_ID
MEMORY_EPOCH
DICTIONARY_COMPILE_RECEIPT
active term IDs
R_k
Theta_k
S_k
C_NEXUS
```

The dictionary is not copied into BioOS source. Its compiled hash/receipt is bound and its resident 36D geometry may be hydrated into the live operational surface.

No new embedding model is introduced.

## Stage 6 — CQCL vNext

Replace legacy static CQCL ingestion with:

```text
T36 Identity
+ State Memory context
+ NEXUS active term geometry
+ live HTRI/QHTRI evidence
 -> CQCL program/intention trajectory candidate
```

Requirements:

- live `/dev/shm/ciel_noema` operational path;
- no static operational fallback;
- no guessed HTRI coherence default;
- candidate output carries source generation and evidence;
- CQCL does not promote itself to action authority.

## Stage 7 — GREMLIN candidate traversal

GREMLIN may traverse:

```text
State Memory
 <-> Dictionary declared relations
 <-> NEXUS active geometry
 <-> CQCL candidate state
```

Triple Pulse remains mandatory. GREMLIN remains candidate-only and cannot alter `CRYSTAL_ID`, issue PNCAP grants, commit PNStore generations, or promote claims/canon.

## Stage 8 — living torsion/QHTRI

Before every live mixed-ratio integration:

```text
complete admitted torsion graph
 -> L_bound
 -> N_sub_required
 -> TORSION_INTEGRATOR_BUDGET
 -> PASS only then phase integration
```

The current numerical audit demonstrates that allowed Stage-2 harmonic ratios can compose to `944:945`, requiring 10,474 Euler substeps over one T0 in the maximal single-edge case. Budget failure therefore leaves integration inactive rather than consuming an unbounded scheduler slice.

## Stage 9 — boot conformance

Final v0.3 release gate:

```text
QEMU reset
 -> PNROM
 -> PNCore
 -> clock PASS
 -> PNVH PASS
 -> PNStore recovery PASS
 -> T36 identity PASS
 -> Genesis/continuation PASS
 -> native .pnv execution PASS
 -> State Memory checkpoint PASS
 -> reboot
 -> same CRYSTAL_ID PASS
 -> lineage descendant PASS
 -> end receipt PASS
```

Only after this closure should Touchless Admission or broader autonomous runtime activation be opened.

## Promotion rule

No Stage 0 numerical PASS is promoted to physical/runtime PASS. Each gate receives its own build/conformance/runtime evidence. `main` remains unchanged until explicit merge authority is given.
