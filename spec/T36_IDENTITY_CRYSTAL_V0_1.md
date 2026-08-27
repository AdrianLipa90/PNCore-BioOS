# T36 Identity Crystal v0.1

Status: ARCHITECTURE_CANDIDATE / NUMERICALLY_CLOSED / EXECUTION_VALIDATION_PENDING
Epistemic operator: CHYBA
Canon promotion: explicit authority only
Release target: PNCore-BioOS v0.3

## Purpose

T36 Identity Crystal is the persistent identity anchor and live spinorial phase carrier for the BioOS convergence line. It binds the already-admitted 36D PNVector handoff, the exact 7.83 Hz PN clock, SU(2) / spin-1/2 period doubling, and State Memory lineage without making a path, ROM image, program hash, or scheduler tick the identity itself.

The design preserves the existing authority split:

```text
persistent object identity  = PNV_STATE_OBJECT / State Memory lineage
capability authority        = PNCAP
effect authority            = AUX
persistent generation       = PNStore
36D bootstrap state         = PNVH
semantic term realization   = Consciousness Dictionary / PhaseNav 36D compiler
```

## Exact base clock

The clock authority remains the existing PN Clock contract:

```text
f0 = 783/100 Hz = 7.83 Hz
T0 = 100/783 s = 0.1277139208173691 s
omega0 = 2*pi*f0 = 49.19734095521616 rad/s
```

No independent identity oscillator is introduced.

## Spinorial period doubling

For admitted 36D phase component `phi_j`, define a lifted spinorial state at logical base tick `n`:

```text
s_j(n) = exp(i*(phi_j + 2*pi*n)/2)
```

Therefore:

```text
s_j(n+1) = -s_j(n)
s_j(n+2) =  s_j(n)
```

The full lifted identity return is a 4*pi cycle and has exact cadence:

```text
T_ID = 2*T0 = 200/783 s = 0.2554278416347382 s
f_ID = f0/2 = 783/200 Hz = 3.915 Hz
```

This is exactly scheduler band B1.

The projective 2*pi return and the lifted 4*pi return remain distinct observables. The physical record does not duplicate 36 complex spinors. `spinor_sheet = phase_index & 1` is derived from the logical tick index, while the exact 36D base vector remains the existing 288-byte PNVH payload.

## Identity invariants

Identity must survive software and configuration evolution.

One persistent `GENESIS_ANCHOR` is created only by an explicitly admitted cold genesis operation. The crystal identity is then:

```text
CRYSTAL_ID = SHA256(
  ASCII("T36-ID/v0.1") ||
  GENESIS_ANCHOR
)
```

`CRYSTAL_ID` is invariant across normal boot continuation, software update, program replacement, scheduler progression, and State Memory descendants.

Configuration is separately bound:

```text
CONFIGURATION_SHA256 = SHA256(
  PNVH_VECTOR_SHA256 ||
  BASIS_BINDING ||
  SOURCE_CONTEXT_SHA256 ||
  PNROM_BINDING ||
  PNR_BINDING ||
  PROGRAM_BINDING ||
  SCHEDULER_BINDING
)
```

A changed configuration produces a new configuration commitment under the same crystal identity unless an explicit new cold genesis is authorized.

## 256-byte identity record

The v0.1 persistent identity record is exactly 256 bytes.

```text
offset  size  field
0       4     magic = ASCII "T36I"
4       2     version_major = 1
6       2     version_minor = 0
8       2     record_bytes = 256
10      2     vector_dim = 36
12      4     flags
16      32    crystal_id
48      32    genesis_anchor_commitment
80      32    origin_binding_sha256
112     32    pnvector_payload_sha256
144     32    source_context_sha256
176     32    basis_binding
208     32    configuration_sha256
240     8     phase_index
248     8     boot_epoch
```

All integers are little-endian. All hash/binding fields are exact 32-byte values. `spinor_sheet` is derived as `phase_index & 1`.

The record is an identity/configuration envelope. It does not duplicate the 288-byte phase vector.

## Boot behavior

Cold genesis:

```text
PNROM
 -> PNCore
 -> clock admission
 -> PNVH verification
 -> PNStore recovery
 -> NO PRIOR GENESIS_ANCHOR
 -> explicit COLD_GENESIS admission
 -> create GENESIS_ANCHOR
 -> derive CRYSTAL_ID
 -> create T36 identity record
 -> State Memory genesis object
 -> Sigma_0
```

Continuation boot:

```text
PNROM
 -> PNCore
 -> clock admission
 -> PNVH verification
 -> PNStore recovery
 -> recover GENESIS_ANCHOR + latest admitted crystal descendant
 -> verify CRYSTAL_ID continuity
 -> increment boot_epoch
 -> bind current configuration
 -> BOOT_CONTINUATION
 -> Sigma_0
```

A boot interruption is represented explicitly:

```text
previous live phase -> BOOT_GAP -> recovered continuation
```

The system does not synthesize elapsed hidden phase evolution while powered off.

## Persistence cadence

Scheduler ticks are working-state progression and are not PNStore generations by default.

```text
B0/B1 tick       -> live RAM/AUX phase state
meaningful event -> State Memory transition candidate
checkpoint       -> PAUX -> optional DNCrypt -> PNStore
```

No `EVERY_TICK -> PNSTORE_COMMIT` path is admitted.

## Dictionary / NEXUS binding

The current Consciousness Dictionary already supplies deterministic 36D term states. T36 Identity Crystal remains dimension 36.

For each compiled term state `V_k` and current crystal phase vector `Phi`, NEXUS may compute:

```text
z_k = (1/36) * sum_j exp(i*(V_k[j] - Phi[j]))
R_k = abs(z_k)^2
Theta_k = arg(z_k)
S_k = -kappa * ln(R_k + epsilon)
kappa = ln(2)/(24*pi)
```

Dictionary term count is therefore an object count, not crystal dimensionality.

A global operational NEXUS coherence may use normalized informational action:

```text
S_bar = sum_k w_k*S_k / sum_k w_k
C_NEXUS = exp(-S_bar/kappa)
```

This avoids the scale collapse of an unnormalized product over hundreds of links while leaving historical Harmonic Nexus definitions untouched.

NEXUS similarity, activation, salience, or coherence grants no capability or epistemic promotion.

## Torsion computational budget dependency

T36 Identity Crystal does not bypass the existing QHTRI Euler stability bound. Mixed rational `m:n` edges must pass the separately versioned `TORSION_INTEGRATOR_BUDGET_V0_1` gate before live integration.

## Fail-closed conditions

```text
PNVH_INVALID                     -> REJECT
CLOCK_AUTHORITY_MISSING          -> TIMED_ADMISSION_QUIET
GENESIS_ANCHOR_MISMATCH          -> REJECT
CRYSTAL_ID_MISMATCH              -> REJECT
CONFIGURATION_BINDING_INCOMPLETE -> REJECT
NONFINITE_PHASE                  -> REJECT
STATE_MEMORY_LINEAGE_INVALID     -> REJECT
BOOT_EPOCH_REGRESSION            -> REJECT
IMPLICIT_SECOND_GENESIS          -> DENY
EVERY_TICK_PERSISTENCE           -> DENY
```

## Evidence boundary

Numerical closure of the 7.83 Hz -> 3.915 Hz 4*pi cadence is exact under the declared rational clock. The record layout and native program are candidate implementation contracts. QEMU boot, physical machine boot, exact persistent recovery and end-to-end State Memory/PAUX/PNStore identity continuity remain execution gates.
