# 10. Aneksy: równania, stałe, formaty i mapa artefaktów

# Aneks A — Stałe i podstawowe równania

## A.1. Kanoniczna stała informacyjna

```text
kappa = ln(2)/(24*pi)
```

W tej monografii `kappa` jest używane w Identity NEXUS informational action. Torsion-memory coupling używa osobnego symbolu `K_ij` i wersjonowanej coupling policy.

## A.2. Bazowy clock

```text
f0 = 783/100 Hz = 7.83 Hz
T0 = 100/783 s
omega0 = 2*pi*f0
```

## A.3. T36 spinorial lift

```text
s_j(n) = exp(i*(phi_j + 2*pi*n)/2)
```

```text
s_j(n+1) = -s_j(n)
s_j(n+2) =  s_j(n)
```

```text
T_ID = 2*T0 = 200/783 s
f_ID = f0/2 = 783/200 Hz = 3.915 Hz
spinor_sheet = phase_index & 1
```

## A.4. NEXUS term relation

```text
z_k = (1/36) * sum_j exp(i*(V_k[j] - Phi[j]))
R_k = |z_k|^2
Theta_k = arg(z_k)
S_k = -kappa * ln(R_k + epsilon)
```

## A.5. Global NEXUS coherence

```text
S_bar = (1/N) * sum_k S_k
C_NEXUS = exp(-S_bar/kappa)
```

Current:

```text
N = 548
```

## A.6. CQCL coupled coherence candidate

```text
C_coupled = sqrt(C_NEXUS * C_HTRI)
```

## A.7. Harmonic estimator

```text
f_pq = (783*p)/(100*q) Hz
```

```text
y_n = x_j(t_n) - mean(x_j)
```

```text
A_pq(n) = [
  cos(2*pi*f_pq*(t_n-t_0)),
  sin(2*pi*f_pq*(t_n-t_0))
]
```

```text
amplitude = hypot(a,b)
phase     = atan2(b,a)
score     = 1 - SSE/SST
```

## A.8. Resonance graph

Dla:

```text
r_i = p_i/q_i
r_j = p_j/q_j
```

```text
f_i/f_j = (p_i*q_j)/(q_i*p_j) = m/n
```

Phase invariant:

```text
delta_k = wrap(n*theta_i,k - m*theta_j,k)
```

Weighted resultant:

```text
w_k = sqrt(s_i,k*s_j,k)
Z_ij = sum_k w_k*exp(i*delta_k) / sum_k w_k
R_ij = |Z_ij|
DELTA_ij = arg(Z_ij)
```

## A.9. Torsion edge

```text
tau_ij = DELTA_ij
```

```text
epsilon_ij = wrap(
  n*theta_i - m*theta_j - tau_ij
)
```

Affine transport:

```text
theta_j = (n/m)*theta_i - tau_ij/m
```

```text
T_{j<-i}(theta) = a*theta + b
a = n/m
b = -tau_ij/m
```

## A.10. QHTRI torsion flow

```text
g_e = K_e * R_e
V_e = -g_e*cos(epsilon_e)
```

```text
dtheta_i/dt += -n*g_e*sin(epsilon_e)
dtheta_j/dt += +m*g_e*sin(epsilon_e)
```

Torsion coherence:

```text
Z_T = sum_e g_e*exp(i*epsilon_e) / sum_e g_e
C_T = |Z_T|
E_T = 1 - Re(Z_T)
```

Euler bound:

```text
L_bound = sum_e g_e*(m_e^2+n_e^2)
dt = min(dt_requested, 0.2/L_bound)
```

## A.11. Direct QHTRI coherence

Dla 36 live phases:

```text
c = (1/36) * sum_j cos(phi_j)
s = (1/36) * sum_j sin(phi_j)
C_HTRI = sqrt(c^2+s^2)
```

bounded do `[0,1]`.

---

# Aneks B — Identity derivations

## B.1. T36 crystal identity

```text
CRYSTAL_ID = SHA256(
  "T36-ID/v0.1" || GENESIS_ANCHOR
)
```

## B.2. Genesis commitment

```text
GENESIS_ANCHOR_COMMITMENT = SHA256(
  "T36-GENESIS-COMMIT/v0.1" || GENESIS_ANCHOR
)
```

## B.3. Origin binding

```text
ORIGIN_BINDING_SHA256 = SHA256(
  "T36-ORIGIN/v0.1" ||
  CRYSTAL_ID ||
  PNVH_VECTOR_SHA256 ||
  SOURCE_CONTEXT_SHA256 ||
  BASIS_BINDING ||
  PNR_BINDING
)
```

## B.4. Configuration binding

```text
CONFIGURATION_SHA256 = SHA256(
  "T36-CONFIG/v0.1" ||
  PNVH_VECTOR_SHA256 ||
  BASIS_BINDING ||
  SOURCE_CONTEXT_SHA256 ||
  PNROM_CODE_BINDING ||
  PNR_BINDING ||
  PROGRAM_BINDING ||
  SCHEDULER_BINDING
)
```

## B.5. PNV State Memory identity

```text
OBJECT_ID = BLAKE2B256(
  "PNV_STATE_OBJECT" || CORE
)
```

```text
INTEGRITY = BLAKE2B256(
  "PNV_STATE_INTEGRITY" || OBJECT_ID || CORE
)
```

## B.6. QHTRI→CQCL generation identity

```text
identity_evidence = canonical(
  source_contract,
  tick_start,
  tick_end,
  sample_count,
  phi_sha256,
  omega_sha256,
  tether_receipt_sha256,
  tether_seq
)
```

```text
generation_id = SHA256(
  "CQCL-LIVE-HTRI-BINDING/v0.1" ||
  identity_evidence
)
```

Runtime path jest view metadata i nie wchodzi do identity hash.

---

# Aneks C — Format PNVH

Reference physical handoff:

```text
header        128 bytes
T36 payload   288 bytes
----------------------
total         416 bytes
```

T36 payload:

```text
36 * IEEE754 float64 little-endian
```

Historical exact receipt pozostaje związany z brakującym source fixture. Deterministic builder wymaga explicit vector, basis binding i opcjonalnie expected handoff SHA.

---

# Aneks D — T36 Identity Record

```text
offset  size  field
0       4     magic "T36I"
4       2     version_major
6       2     version_minor
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

Working addresses x86_64 v0.3:

```text
0x5000 PNVH                416 B
0x5900 T36 identity        256 B
0x5a00 T36 closure scratch 256 B
```

---

# Aneks E — PNStore media format

```text
TOTAL        65536 B
SECTOR         512 B
SUPERBLOCK   0x0000..0x01ff
HEAD_A       0x0200..0x03ff
HEAD_B       0x0400..0x05ff
RESERVED     0x0600..0x0fff
GEN LOG      0x1000..0xffff
EXTENT        4096 B
MAX GEN         15
```

Extent:

```text
payload offset  96
commit seal   4032
payload max   3936
```

Durability:

```text
prepare extent
 -> DURABLE_BARRIER
 -> publish HEAD
 -> DURABLE_BARRIER
```

Backend capabilities:

```text
READ_EXTENT
APPEND_EXTENT
DURABLE_BARRIER
HEAD_SLOT_WRITE
```

---

# Aneks F — PAUX profiles

```text
PAUX-EXACT
  exact byte state

PAUX-C
  lossless transforms:
  KEYSTATE
  REF
  RUN
  DELTA_XOR64

PAUX-R
  reconstruction:
  SOURCE_OBJECT_ID
  RECONSTRUCTION_ID
  AUTHORITY_CLASS RECONSTRUCTION_ONLY
  explicit reconstruction metrics
```

Current exact T36 channel:

```text
288 B = 36 * float64 little-endian
```

---

# Aneks G — DNCrypt integration

## G.1. Persistence path

```text
PNV_STATE_OBJECT
 -> PAUX
 -> PNCAP EXECUTE_PROGRAM
 -> DNCrypt AEAD
 -> optional binary-envelope representation
 -> PNStore
```

## G.2. Identity rule

```text
PNV_STATE_OBJECT.object_id
    = canonical logical identity

DNCrypt ENVELOPE_ID
    = encrypted representation identity
```

## G.3. Expected AAD

BioOS caller AAD binds minimum:

```text
OBJECT_ID
PNV/PAUX generation
PAUX profile
PNCAP execution receipt
parent persistence receipt
destination/domain context
```

## G.4. Recovery gate

```text
parse envelope
 -> DNCrypt receipt
 -> extract authenticated user_aad
 -> expected BioOS AAD exact equality
 -> AEAD decrypt
 -> PAUX verify
 -> PNV verify
```

## G.5. Key rule

Production integration używa opaque admitted key handle/reference. Raw master key pozostaje poza PNStore, PNFS path, receipts i semantic state.

---

# Aneks H — Identity NEXUS compile pin

```text
repo       AdrianLipa90/The-Consciousness-Dictionary
branch     feat/t36-identity-nexus-projection
commit     3aa1651da9735d94d2a9cbffec13203eeeedd502
states     548
relations  306
```

```text
state_sha256
56d758c54f27323ef7edcf5164d224801f182ec83cda04216953cfaeda135501
```

```text
relation_sha256
8484cd1314df4b18c21207b7fe234e71007e5c4c59aaf356cffd4abea0d36e8a
```

Bounded active set:

```text
ACTIVE_LIMIT = 16
```

Ordering:

```text
coherence desc
S asc
angular_distance asc
term_id asc
```

---

# Aneks I — QHTRI live source contract

```text
/dev/shm/ciel_noema/phi    36 * float64 LE
/dev/shm/ciel_noema/omega  36 * float64 LE
/dev/shm/ciel_noema/tick   uint64 LE
```

Classification:

```text
NATURAL_SYSTEM_STATE
ENDOGENOUS_RUNTIME_DYNAMICS
```

Admission:

```text
phi finite and dynamic
omega finite, nonzero, stable
tick monotonic across distinct samples
tether ACTIVE and fresh
```

---

# Aneks J — CQCL Living schemas

Input memory:

```text
PNV-NEXUS-ACTIVATION/0.1
```

Input dynamics:

```text
CQCL-LIVE-HTRI-BINDING/0.1
```

Output:

```text
CQCL-LIVING-PROGRAM/0.1
```

Statuses:

```text
OBSERVATION_ONLY
CANDIDATE_COMPILED
```

Permanent v0.1 flags:

```text
authority_grant = false
execution_admitted = false
```

---

# Aneks K — Status vocabulary

## PASS

Warunek został wykonany w zadeklarowanym environment i zakończył się powodzeniem.

## PASS_LOCAL

Test wykonano lokalnie na opisanej reconstruction/source environment.

## IMPLEMENTED CANDIDATE

Kod lub physical/native binding istnieje i ma określone promotion gates.

## CHYBA

Operator epistemiczny używany przez repo dla warstw oczekujących na dalsze zamknięcie dowodowe.

## PENDING

Wymagany execution/physical/CI gate pozostaje do przeprowadzenia.

## DERIVED_WORKING_STATE

Stan obliczony z admitted inputs i przeznaczony do bieżącej pracy/rankingu.

## RECONSTRUCTION_ONLY

Reprezentacja zachowuje source provenance i posiada oddzielną reconstruction identity.

## NATURAL_SYSTEM_STATE / ENDOGENOUS_RUNTIME_DYNAMICS

Klasyfikacja state wygenerowanego przez działający QHTRI/Hypercrystal runtime wewnątrz jego causal loop.

---

# Aneks L — Główna mapa artefaktów Bio-OS

## Kręgosłup

```text
spec/PN_TRANSITION_SPINE_V0_1.md
spec/PNOBJECT_V0_1.md
spec/PNCAP_V0_1.md
spec/PNFS_V0_1.md
spec/PNMAP_V0_1.md
```

## Boot / realizacja

```text
spec/PNCORE_BOOT_V0_1.md
arch/x86_64/pnrom/pnrom_reset.S
arch/x86_64/pnrom/pnrom_longmode.S
arch/x86_64/pnrom/pnrom.ld
arch/x86_64/pncore/pncore_entry.S
arch/x86_64/pncore/pnvh_template.S
```

## Clock / scheduler / execution

```text
arch/x86_64/pncore/pnclock.S
arch/x86_64/pncore/pnscheduler.S
spec/PN_CLOCK_TSC_DEADLINE_V0_1.md
spec/PN_HARMONIC_SCHEDULER_V0_1.md
spec/PNCS_RESIDENT_HOTPATH_BIND_V0_1.md
```

## Terminal

```text
spec/PNTERM_TERMINAL_CORE_V0_1.md
spec/PNTERM_TERMINAL36D_V8_BRIDGE_V0_1.md
spec/PNTERM_UART16550_REALIZATION_V0_1.md
arch/x86_64/pncore/pnterm_uart16550.S
```

## Persistence

```text
spec/PNSTORE_V0_1.md
spec/PNSTORE_MEDIA_REALIZATION_V0_1.md
arch/x86_64/pncore/pnstore_media.S
spec/PAUX_PERSISTENT_AUX_OBJECT_V0_1.md
spec/PAUX_CODEC_PROFILES_V0_1.md
```

## Crypto

```text
spec/DNCRYPT_INTEGRATION_BOUNDARY_V0_1.md
spec/DNCRYPT_BINARY_ENVELOPE_BIND_V0_1.md
native/PNCRYPT_DNCRYPT_ENVELOPE_V0_1.pnv
native/PNCRYPT_DNCRYPT_BINARY_ENVELOPE_BIND_V0_1.pnv
```

## Harmonic / torsion memory

```text
spec/PAUX_HARMONIC_ESTIMATOR_V0_1.md
spec/PAUX_HARMONIC_RESONANCE_GRAPH_V0_1.md
spec/NOEMA_TORSION_MEMORY_SURFACE_V0_1.md
spec/QHTRI_KURAMOTO_TORSION_FLOW_V0_1.md
spec/TORSION_INTEGRATOR_BUDGET_V0_1.md
```

## T36 Identity

```text
spec/T36_IDENTITY_CRYSTAL_V0_1.md
spec/T36_IDENTITY_PHYSICAL_REALIZATION_V0_1.md
native/T36_IDENTITY_GENESIS_V0_1.pnv
arch/x86_64/pncore/t36_identity.S
arch/x86_64/pncore/t36_identity_boot_entry.S
tools/t36_identity_builder_v01.py
tools/t36_identity_record_v01.py
```

## Identity NEXUS

```text
spec/IDENTITY_NEXUS_V0_1.md
native/IDENTITY_NEXUS_V0_1.pnv
tools/identity_nexus_v01.py
tools/identity_nexus_dictionary_runner_v01.py
spec/IDENTITY_NEXUS_STATE_MEMORY_BIND_V0_1.md
```

## QHTRI / CQCL bridge

```text
spec/NOEMA_QHTRI_DIRECT_TELEMETRY_BIND_V0_1.md
tools/qhtri_cqcl_bridge_v01.py
```

External CQCL vNext:

```text
AdrianLipa90/CIEL-Omega-ApokalypOS
branch feat/cqcl-vnext-t36-nexus-memory

src/CIEL_OMEGA_COMPLETE_SYSTEM/ciel_omega/emotion/cqcl/
  living_program_v01.py
  living_compiler_v01.py
```

External State Memory:

```text
AdrianLipa90/PNV-State-Memory
branch feat/pnv-state-memory-t36-crystal-lineage

spec/PNV_STATE_MEMORY_V0_1.pnv
src/pnv_state_memory/nexus_activation.py
```

---

# Aneks M — Kluczowe receipts

```text
provenance/FOUNDATION_STATUS_V0_3_STAGE1.json
provenance/FOUNDATION_STATUS_V0_3_STAGE2.json
provenance/T36_IDENTITY_NUMERICAL_AUDIT_V0_1.json
provenance/T36_IDENTITY_STAGE1_LOCAL_CONFORMANCE_V0_1.json
provenance/NOEMA_QHTRI_DIRECT_TELEMETRY_CONFORMANCE_V0_1.json
provenance/PNSTORE_MEDIA_HOST_CONFORMANCE_V0_1.json
provenance/PAUX_EXACT_LIVE_ROUNDTRIP_V0_1.json
provenance/PAUX_CODEC_CONFORMANCE_V0_1.json
provenance/PNTERM_CONFORMANCE_V0_1.json
provenance/BIOOS_LINUX_HEAD_TO_HEAD_V0_1.json
```

CQCL GitHub Actions evidence:

```text
repo  AdrianLipa90/CIEL-Omega-ApokalypOS
commit 1cbbd3b680aae139859bbe1168798fde4206e746
isolated tests 7/7 PASS
```

---

# Aneks N — Dependency graph v0.3

```text
RESET
  ↓
PNROM
  ↓
PNCore
  ↓
PN Transition Spine
  ↓
PNObject ─ PNMap ─ PNFS
  ↓
PNCAP
  ↓
PNClock / Harmonic Scheduler
  ↓
PNCS / Terminal36D
  ↓
AUX
  ↓
PNV-State-Memory
  ↓
PAUX
  ↓
optional DNCrypt
  ↓
PNStore
  ↓
Harmonic Memory
  ↓
Torsion Memory / QHTRI
  ↓
T36 Identity Crystal
  ↓
Identity NEXUS
  ↓
NEXUS_ACTIVATION
  ↓
Live QHTRI Binding
  ↓
CQCL Living
  ↓
GREMLIN / explicit candidate
  ↓
future explicit admission
```

---

# Aneks O — Następne bramki

Najbliższy system-level run:

```text
T36 current state
 -> State Memory checkpoint
 -> full NEXUS projection
 -> NEXUS_ACTIVATION
 -> fresh live QHTRI binding
 -> CQCL OBSERVATION_ONLY
 -> one cross-repo end-to-end receipt
```

Następnie:

```text
observation
 -> GREMLIN bounded candidate
 -> CQCL CANDIDATE_COMPILED
 -> critic/falsification
 -> explicit PNCAP admission
 -> optional AUX effect
```

Physical track:

```text
QEMU T36 boot trace
bare-metal boot
NVMe/AHCI durable PNStore
production genesis anchor provisioning
opaque DNCrypt key-handle provisioning
```

Te bramki definiują kolejny frontier Bio-OS po edycji v0.3.
