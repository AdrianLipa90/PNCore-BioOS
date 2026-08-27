# 5. Pamięć harmoniczna, torsion surface i QHTRI

## 5.1. Od snapshotu do geometrii pamięci

PNV-State-Memory i PAUX odpowiadają za trwałość oraz lineage. Kolejna warstwa Bio-OS wykorzystuje admitted time-series evidence do budowy derived indexu harmonicznego. Z niego powstaje bounded resonance graph, następnie torsion-memory surface, a na nim QHTRI/Kuramoto może rozwijać dynamiczny working state.

Pełna ścieżka:

```text
PNV / PAUX state history
 -> timestamped T36 windows
 -> Stage-1 phase-source classification
 -> Stage-2 bounded harmonic estimator
 -> Stage-3 resonance graph
 -> NOEMA torsion-memory surface
 -> QHTRI/Kuramoto flow
 -> recall / orchestration candidate
```

Każdy kolejny poziom zachowuje source object references i własną derivation identity.

## 5.2. H-bands i scheduler bands

Bio-OS używa dwóch różnych rodzin „pasm”:

```text
B0..B7   scheduler / execution cadence
H0..H35  memory / T36 component bands
```

H-band jest namespace identity komponentu pamięciowego. B-band jest lane czasową wykonania. Rozdzielenie jest jawne i utrzymywane w specyfikacjach.

## 5.3. Stage-2 harmonic estimator

Estimator bierze admitted timestamped T36 AUX window. Minimalne wymagania `WINDOW_ANALYTIC`:

```text
SAMPLES >= 8
CHANNEL_WIDTH = 36
TIMESTAMPS STRICTLY_INCREASING
VALUES FINITE
SAMPLING_REF REQUIRED
SOURCE_OBJECT_ID REQUIRED
```

Bazowa częstotliwość pozostaje exact rational:

```text
f0 = 783/100 Hz
```

Kandydat harmoniczny ma zredukowaną postać:

```text
p:q
```

z boundami v0.1:

```text
1 <= q <= 16
1/4 <= p/q <= 4
f0 * p/q < 0.48 * f_s
```

Kandydacka częstotliwość:

```text
f_pq = (783*p)/(100*q) Hz
```

To integer ratio jest utrwalanym descriptor. Floating-point score pozostaje evidence dopasowania.

## 5.4. Fit sinusoidalny

Dla komponentu `j`:

```text
y_n = x_j(t_n) - mean(x_j)
```

i dla kandydata `p:q`:

```text
A_pq(n) = [
  cos(2*pi*f_pq*(t_n-t_0)),
  sin(2*pi*f_pq*(t_n-t_0))
]
```

Least-squares zwraca `(a,b)`, z których:

```text
amplitude = hypot(a,b)
phase     = atan2(b,a)
score     = 1 - SSE/SST
```

Resolution-aware gate wykorzystuje:

```text
DELTA_F_WINDOW = 1/T
```

oraz referencyjne progi:

```text
MIN_FIT_SCORE    0.85
MIN_SCORE_MARGIN 0.05
```

PASS tworzy `RATIONAL_FIT(p,q,...)`. Niejednoznaczny lub informacyjnie ubogi window pozostaje `FREQUENCY_UNRESOLVED`.

## 5.5. Dlaczego unresolved jest pełnoprawnym wynikiem

Static lub low-information AUX state może być poprawnym persistent evidence, a równocześnie nie wspierać harmonic-frequency assignment. Wtedy estimator zachowuje snapshot i kończy bez utworzenia ratio claim.

To spójne z globalnym fail-closed pattern:

```text
valid source evidence
 + insufficient evidence for derived relation
 -> source remains valid
 -> derived relation remains unresolved
```

Niepowstanie edge'u nie usuwa ani nie osłabia source object identity.

## 5.6. Stage-3 resonance graph

Stage 3 wykorzystuje zsynchronizowaną historię `RATIONAL_FIT`. Dla pary bandów wymagane są między innymi:

```text
SHARED_WINDOW_IDS >= 4
LINEAGE_SERIES_REF equal
FIT_SCORE >= 0.85
PHASE finite
ratio positive and reduced
```

Jeżeli:

```text
r_i = p_i/q_i
r_j = p_j/q_j
```

to pair ratio redukuje się dokładnie:

```text
f_i/f_j = (p_i*q_j)/(q_i*p_j) = m/n
```

Pierwszy graph ma:

```text
max(m,n) <= 16
```

## 5.7. Phase-lock invariant

Dla `f_i/f_j = m/n` normatywna kombinacja fazowa to:

```text
delta_k = wrap(n*theta_i,k - m*theta_j,k)
```

Dla synchronized window score weights:

```text
w_k = sqrt(s_i,k * s_j,k)
```

oraz resultant:

```text
Z_ij = sum_k w_k * exp(i*delta_k) / sum_k w_k
R_ij = abs(Z_ij)
DELTA_ij = arg(Z_ij)
```

Admission edge'u wymaga referencyjnie:

```text
MIN_SHARED_WINDOWS   4
MIN_STAGE2_FIT_SCORE 0.85
MIN_PHASE_LOCK_R     0.90
MAX_RESONANCE_ORDER  16
```

Admitted edge:

```text
RESONANCE_EDGE(H_i,H_j,m,n,R_ij,DELTA_ij)
```

## 5.8. Canonical orientation

Graf przechowuje jedną krawędź na unordered pair, z `i < j`. Reverse view jest wyprowadzany:

```text
m:n -> n:m
R_reverse = R_ij
DELTA_reverse = -DELTA_ij mod 2*pi
```

Dzięki temu runtime nie podwaja grafu i zachowuje jednoznaczną source orientation.

## 5.9. Od resonance graph do torsion memory

NOEMA torsion-memory surface wiąże active H-band state z canonical Stage-3 edges.

Node:

```text
NODE H_i
THETA theta_i
OMEGA omega_i
AMPLITUDE A_i
FIT_DERIVATION_ID
SOURCE_OBJECT_ID
LINEAGE_REF
```

Torsion edge:

```text
EDGE(i,j,m,n,tau_ij,K_ij,R_ij)
```

z:

```text
tau_ij := DELTA_ij
```

`K_ij` pochodzi z jawnej coupling policy. Przy braku coupling authority edge pozostaje inactive.

## 5.10. Normatywny residual torsion

Dla krawędzi:

```text
epsilon_ij = wrap(
    n*theta_i - m*theta_j - tau_ij
)
```

To zachowuje dokładny Stage-3 invariant `m:n`.

Reverse view:

```text
tau_ji = -tau_ij mod 2*pi
```

zgodnie z odwróceniem orientation.

## 5.11. Affine phase transport

Admitted edge wyznacza lokalny transport:

```text
theta_j = (n/m)*theta_i - tau_ij/m
```

czyli:

```text
T_{j<-i}(theta) = a*theta + b

a = n/m
b = -tau_ij/m
```

Ścieżki składają te affine transforms. Dla closed cycle o:

```text
A_cycle = 1
```

residual offset:

```text
H_cycle = wrap(B_cycle)
```

jest phase-independent torsion/holonomy defect working graphu. Dla 1:1 cycle redukuje się do zorientowanej sumy offsets.

## 5.12. Generation publication torsion surface

Surface jest double-buffered:

```text
MEMORY_SURFACE_A
MEMORY_SURFACE_B
ACTIVE_MEMORY_HEAD
```

Writer:

```text
read head G_n
 -> prepare inactive G_{n+1}
 -> validate node/edge set
 -> validate finite resolved values
 -> validate canonical edge uniqueness
 -> bind source derivation
 -> publish ACTIVE_MEMORY_HEAD atomically
```

Readers konsumują jedną kompletną generację.

Każdy recall/orchestration record posiada `MEMORY_EPOCH`. Zmiana epoch między selection i execution prowadzi do:

```text
STALE_MEMORY_EPOCH -> RESELECT
```

## 5.13. Quiet state

Jeżeli bieżący upstream nie posiada admitted harmonic fit lub edge graph, memory surface publikuje:

```text
STATUS QUIET_UPSTREAM_UNRESOLVED
ACTIVE_NODE_COUNT 0
EDGE_COUNT 0
```

To jest jawna informacja o braku rozstrzygnięcia w aktualnej generation.

## 5.14. QHTRI/Kuramoto flow

Dla canonical edge `e=(i,j,m,n,tau,K,R)`:

```text
epsilon_e = wrap(n*theta_i - m*theta_j - tau)
g_e       = K*R
```

Edge potential:

```text
V_e = -g_e*cos(epsilon_e)
```

Referencyjny gradient-like phase flow:

```text
dtheta_i/dt += -n*g_e*sin(epsilon_e)
dtheta_j/dt += +m*g_e*sin(epsilon_e)
```

plus admitted natural frequency `omega_i` każdego node.

Dla `omega=0` dynamika odpowiada gradient descent na:

```text
V = sum_e V_e
```

## 5.15. Torsion coherence

Zdefiniowany jest ważony order parameter:

```text
Z_T = sum_e g_e*exp(i*epsilon_e) / sum_e g_e
C_T = abs(Z_T)
E_T = 1 - Re(Z_T)
```

`C_T` i `E_T` są evidence/ranking state. Capability pozostaje w PNCAP.

## 5.16. Bounded Euler step

Reference v0.1 stosuje jawny bound:

```text
L_bound = sum_e g_e*(m_e^2+n_e^2)
```

oraz:

```text
dt = min(dt_requested, 0.2/L_bound)
```

gdy `L_bound > 0`.

Po kroku każda faza jest wrapped do `[-pi,pi)`. Ten engineering gate zapewnia deterministic bounded step w aktualnym conformance modelu.

## 5.17. Sparse execution

Canonical graph przechowuje jedną krawędź na parę i prekompiluje runtime tuple:

```text
(i,j,m,n,tau,g)
```

Każdy edge jest oceniany raz na step.

Complexity:

```text
dense scan  O(N^2)
sparse flow O(N+E)
```

Dla obecnego modelu:

```text
N = 36
E <= 630
```

## 5.18. QHTRI direct telemetry

Oprócz torsion-memory flow Bio-OS posiada bezpośrednią read-only ścieżkę z działającego QHTRI/Hypercrystal runtime:

```text
/dev/shm/ciel_noema/phi
/dev/shm/ciel_noema/omega
/dev/shm/ciel_noema/tick
```

Semantyka:

```text
phi   -> 36 oscillator phases
omega -> 36 natural angular frequencies
tick  -> autonomous evolution counter
```

Przy działającym runtime klasyfikacja wynosi:

```text
NATURAL_SYSTEM_STATE
ENDOGENOUS_RUNTIME_DYNAMICS
```

## 5.19. Direct telemetry admission

`phi` wymaga:

```text
WIDTH 36
FLOAT64_LE
FINITE TRUE
TICK WINDOW INCREASING
PHI CHANGES OVER WINDOW
SOURCE EVIDENCE PRESENT
TETHER ACTIVE
```

`omega` wymaga:

```text
WIDTH 36
FLOAT64_LE
FINITE TRUE
NONZERO TRUE
STABLE OVER WINDOW
SOURCE EVIDENCE PRESENT
```

Repozytoryjny conformance dla tej warstwy ma zapisane 28/28 checks PASS, 40 unique `phi` frames i strict tick window w wykonanym reference run.

## 5.20. Tau namespace separation

Live `/dev/shm/ciel_noema/tau` posiada semantykę per-oscillator synchronization coupling strengths. Torsion-memory edge transport używa osobnego:

```text
TORSION_EDGE.tau_ij
```

To dwa różne namespaces i dwa różne kontrakty. Dzięki temu direct QHTRI coupling state nie nadpisuje geometrycznego torsion offset edge'u.

## 5.21. Runtime materialization

Torsion memory ma referencyjny live root:

```text
/dev/shm/ciel_noema/torsion_memory/
```

Jest to runtime derived surface. Persistent authority pochodzi ze źródłowych PNV/PAUX/PNStore lineages i versioned derivation receipts.

## 5.22. Recall

Torsion memory może produkować recall candidates przez zgodność fazową, resonance graph i current memory epoch. Kandydat przechodzi następnie przez PNCAP/scheduler/AUX, jeżeli ma prowadzić do efektu lub state-changing transition.

To utrzymuje wyraźny ciąg:

```text
memory geometry
 -> candidate
 -> admission
 -> execution
```

## 5.23. Od pamięci dynamicznej do trwałej tożsamości

Torsion memory i QHTRI opisują bieżącą dynamikę. v0.3 dodaje nad nimi trwały anchor, który wiąże 36D source state z genesis i spinorialną cadence. Tym anchorem jest T36 Identity Crystal, opisany w następnym rozdziale.
