# PNCore-BioOS

PNCore BioOS is a candidate vector-native system stack for dynamic AC-flow NOEMA/PhaseNav systems on conventional PC hardware.

Current development line: **v0.2.6 stage 5 — PAUX harmonic orbital memory through lossless harmonic base selection and PAUX-R orbital reconstruction**.

```text
RESET @ 0xFFFF0
 -> PNROM @ 0xF0000
 -> x86_64 capability admission
 -> PNMap/MMU substrate
 -> long mode
 -> PNVector Handoff -> RAM 0x5000
 -> PNCore @ 0xF0156
 -> PN Realization admission
 -> Genesis physical predicate
 -> Sigma_0 @ 0x5200
 -> transition evidence @ 0x5300
 -> harmonic admission selector
 -> PNClock exact-rational source gate
 -> PNV relational state object
 -> AUX persistent carrier (*.paux)
 -> PNStore append-only generation transition
 -> AUX durable persistence boundary
 -> PAUX harmonic orbital derived index
 -> bounded rational harmonic estimator
 -> H-band resonance graph
 -> PAUX-C harmonic exact-base selection
 -> PAUX-R orbital reconstruction evidence
 -> dual-HEAD recovery / exactly-once evidence
```

## Core primitives

- **PNV** — native program/witness surface.
- **PNH5** — transactional trajectory/state persistence profile.
- **PNR** — content-addressed architecture-specific physical realization binding.
- **PNObject / Generation Cell** — common generation-bound object model.
- **PNStore** — admitted append/commit persistence.
- **PNFS** — relational object-space view.
- **PNMap** — relational mapping/resolution contract.
- **PNCAP** — generation-bound capability admission.
- **PNResource** — physical resources represented through PNObject semantics.
- **PNVector Handoff** — exact ordered 36D firmware-to-PNCore state carrier.
- **PN Harmonic Scheduler** — single-counter dyadic admission classes anchored at 7.83 Hz.
- **PNClock** — exact rational absolute phase-index clock realization; x86 TSC-deadline is admitted only with explicit hardware frequency authority.
- **PAUX (`.paux`)** — persistent AUX carrier for canonical `PNV_STATE_OBJECT` identity, lineage, capability and evidence binding. Profiles: `PAUX-EXACT`, lossless `PAUX-C`, and reconstruction `PAUX-R`.
- **PAUX Harmonic Orbital Memory** — derived exact-rational H-band geometry (`H0..H35`) bound to source `OBJECT_ID` through `DERIVATION_ID`; phase provenance is classified as `DIRECT_PHASE`, `WINDOW_ANALYTIC`, or `PHASE_UNKNOWN`. Stage 2 resolves admitted windows against a bounded rational frequency lattice, Stage 3 derives phase-lock resonance edges, Stage 4 uses harmonic revisits only as exact `XOR64` base candidates, and Stage 5 provides separately identified `RECONSTRUCTION_ONLY` orbital PAUX-R profiles.
- **PNStore × AUX binding** — admitted persistence route from PAUX generation transitions through exact PNCAP grants into AUX physical-media adapters.
- **PNStore Media Core** — deterministic append-only generation layout, CRC32C commit seals, alternating dual HEAD and bounded recovery realization.

## GREMLIN-guided reductions

GREMLIN is used only as a bounded candidate generator and structural critic.

Current accepted engineering candidates for this branch:

```text
separate .pnx executable                -> removed as duplicate
layered inode/device ontology            -> replaced by unified PNObject relations
text PNV parser in reset runtime         -> rejected by structural comparison
schedule-only physical table             -> rejected by structural comparison
PN Realization                           -> structural match candidate
x86 page walk <-> PNMap resolve          -> structural match candidate
separate boot-info block                 -> folded into PNVector Handoff path
seven independent band timers            -> one tick index + ctz/BSF selector
incremental timer catch-up path           -> absolute phase-index deadlines
in-place PNStore mutation                 -> append-only generation extents
classic replay journal                    -> commit seal + alternating dual HEAD
direct PNStore device binding             -> AUX persistence boundary + .paux
lossless repeated AUX frames              -> KEYSTATE + REF + RUN / DELTA_XOR64
reconstruction compression                -> separate PAUX-R reconstruction evidence spine
harmonic frequency ratios                 -> exact rational orbital radius index
window frequency inference                -> bounded rational lattice + sinus/cos fit
harmonic relation                         -> exact commensurability + n*theta_i-m*theta_j lock
harmonic revisit in PAUX-C                -> candidate base only; exact XOR64 cost decides
orbital PAUX-R reconstruction             -> model + quantized residual + separate reconstruction identity
```

## Current evidence

```text
64 KiB PNROM build: PASS
final ELF relocations: 0
reset vector: exact @ 0xFFF0
live PhaseNav registry binding: PASS
PNR program/schedule/composition binding: PASS
PNVector Handoff structural binding: PASS
harmonic scheduler host reference: 1,048,576/1,048,576 PASS
PNClock host conformance: 224,576 checks PASS
current host exact CPUID.15 source: QUIET / fail-closed
PNStore fsync block-image conformance: 118/118 PASS
PNStore bounded generations: 15; generation 16 fail-closed
PNStore effect boundary: AUX/.paux BOUND
physical AUX media adapter: PENDING
v0.2.3 conformance: 25/25 PASS
PAUX × PNV-State-Memory GREMLIN structural test: SUPPORTED_BY_DECLARED_TESTS
PAUX GREMLIN critic: PASS
PAUX-EXACT live shadow round-trip: PASS (2 x 288 B byte-identical)
PAUX-C live 64-frame RLE/REF round-trip: 64/64 PASS
PAUX-C favorable fixture logical payload reduction: 99.21875%
PAUX codec conformance: 24/24 PASS
PAUX harmonic orbital stage 1: 19/19 PASS
PAUX harmonic estimator stage 2: 20/20 PASS; synthetic T36 36/36 PASS
PAUX harmonic resonance graph stage 3: 18/18 PASS
PAUX-C harmonic base stage 4: 24/24 PASS
PAUX-C stage-4 synthetic changed-word reduction: 93.33333333333333%
PAUX-R orbital reconstruction stage 5: 21/21 PASS
PAUX-R stage-5 selected reference profile: MODEL_QR8
PAUX-R stage-5 synthetic logical reduction: 85.7421875%
PAUX-R stage-5 synthetic NRMSE: 0.00040190830518126766
v0.2.6 declared stage checks: 102/102 PASS
live AUX stage-1 snapshot phase classifier: PHASE_UNKNOWN without explicit phase provenance
live AUX stage-2 window: FREQUENCY_UNRESOLVED for static state
live AUX exact profile precedence: PAUX-C RUN
runtime emulation: pending
physical-machine execution: pending
```

All project-native runtime/program artifacts remain PNV/PNR and assembly bootstrap sources; the target tree contains zero `.py` files.

## PN Harmonic Scheduler candidate

The current development branch adds a single-clock harmonic admission scheduler anchored at `f0 = 7.83 Hz`. `B0` is a bounded service lane on every tick. Mutually-exclusive admission classes are selected for positive tick index `n` by `band(n) = 1 + nu2(n) = 1 + ctz(n)`. Current admitted classes are `B1..B7`; deeper classes remain `RESERVED_QUIET`. Missed windows and re-entry are skipped; catch-up bursts are denied.

The x86_64 physical selector lives in `arch/x86_64/pncore/pnscheduler.S`. Host execution checked 1,048,576 tick values against the mathematical reference with exact agreement.

## PNClock candidate

The scheduler clock path uses the exact rational `f0 = 783/100 Hz`. For a complete CPUID.15 tuple `(d,u,c)`, BioOS keeps the period as `N/D` with `N = c*u*100` and `D = d*783`; deadline `n` is `base_tsc + floor(n*N/D)`. The next event is selected directly from the current TSC and phase index, so missed windows are skipped rather than replayed.

The preferred x86 source is `TSC_DEADLINE_EXACT`. It requires TSC, TSC-deadline, invariant TSC, and non-zero CPUID.15 denominator/numerator/crystal frequency. Missing exact hardware frequency leaves timed admission quiet until an admitted fallback realization exists.

## PNStore Media Core candidate

PNStore v0.2.3 freezes the first byte-exact medium realization. A 64 KiB bounded image carries a CRC32C superblock, two alternating 512-byte HEAD slots and fifteen immutable 4 KiB generation extents. Extent preparation and HEAD publication are separate operations so a hardware backend can enforce `PREPARE -> DURABLE_BARRIER -> HEAD -> DURABLE_BARRIER`.

Host execution uses the same assembly media core against an `mmap + msync + fsync` block image. Power-cut tests verify that an unreferenced prepared tail stays outside current state, a torn newer HEAD or corrupt newer extent falls back to the previous valid generation, and replay of any previously committed transition ID returns its original generation without byte mutation.

## PAUX persistent AUX binding candidate

BioOS v0.2.4 binds persistence to the existing `PNV-State-Memory` object model. A persistent AUX artifact uses the `.paux` extension and carries the canonical `PNV_STATE_OBJECT.object_id`, integrity commitment and immutable lineage into the AUX/PNStore transition path.

```text
live AUX state
 -> PNV relational snapshot
 -> PNV_STATE_OBJECT
 -> PNCAP persistence admission
 -> *.paux
 -> PNStore generation prepare
 -> AUX durable barrier
 -> PNStore HEAD publication
 -> AUX durable barrier
 -> evidence
```

The canonical state identity remains the PNV-State-Memory `OBJECT_ID`. Generation, transition, capability and evidence references are persistence-envelope data around that object. Device-specific storage realization is dispatched below the AUX boundary.

Current live `/dev/shm/ciel_noema/aux_phi` and `aux_feedback_phi` remain the versioned live T36 transport endpoints. `.paux` applies to persistent AUX materializations in this version.

## PAUX codec profiles candidate

BioOS v0.2.5 adds three explicit PAUX profiles. `PAUX-EXACT` preserves admitted T36 channel payloads byte-for-byte. `PAUX-C` applies reversible transforms (`KEYSTATE`, hash-equal `REF`, exact `RUN`, and sparse `DELTA_XOR64`) and re-enters the exact recovery path only after object identity and integrity verification. `PAUX-R` carries `SOURCE_OBJECT_ID` plus its own `RECONSTRUCTION_ID` and produces explicit reconstruction metrics.

The first live PAUX-EXACT test materialized the active `aux_phi` and `aux_feedback_phi` into a `.paux` carrier and restored both into `/dev/shm/ciel_noema/paux_restore_shadow` byte-identically while leaving the active tether files untouched. The first PAUX-C live observation fixture contained 64 repeated states with feedback byte-identical to the primary AUX channel; `KEYSTATE + REF + RUN` reconstructed all 64 frames exactly. Its measured reduction is recorded only for that favorable fixture.

## PAUX harmonic orbital memory candidate

BioOS v0.2.6 Stage 1 introduces a derived harmonic-orbital index over admitted PAUX state identity. Memory bands use `H0..H35`, while scheduler lanes retain `B0..B7`. Harmonic ratios are stored as reduced positive integer pairs `p:q`; wavelength and normalized sphere-radius ratios are derived exactly as `q/p` and `N*q/(N0*p)`.

Phase provenance is explicit. A versioned 36-value phase source enters as `DIRECT_PHASE`; a finite timestamped window of at least four T36 samples enters as `WINDOW_ANALYTIC`; a snapshot without either source enters as `PHASE_UNKNOWN`.

Stage 2 resolves admitted windows by searching a bounded exact-rational lattice relative to `f0 = 783/100 Hz`, fitting sinus/cos coefficients and emitting phase, amplitude, fit score and ambiguity evidence. Static or ambiguous windows fail closed to `FREQUENCY_UNRESOLVED`.

Stage 3 converts resolved H-band fits into a derived resonance graph. For exact pair frequency ratio `f_i/f_j = m/n`, phase locking is measured with the invariant `n*theta_i - m*theta_j`; lineage and quality gates remain explicit.

Stage 4 allows orbital phase revisits to nominate earlier PAUX-C base frames. The previous frame remains the baseline and exact uint64 `XOR64` changed-word cost makes the final selection. Harmonic geometry therefore cannot reduce exact recovery guarantees.

Stage 5 adds an executable PAUX-R orbital reconstruction profile using per-band sinus/cos models plus optional QR8/QR16 quantized residuals. Every representation carries a separate `RECONSTRUCTION_ID`, remains `AUTHORITY_CLASS RECONSTRUCTION_ONLY`, and is admitted only through explicit reconstruction metrics. On the declared 36×256 synthetic reference fixture, `MODEL_QR8` is the smallest passing profile with 85.7421875% logical reduction and NRMSE 0.00040190830518126766. The current live static AUX fixture remains on the exact `PAUX-C RUN` path.
