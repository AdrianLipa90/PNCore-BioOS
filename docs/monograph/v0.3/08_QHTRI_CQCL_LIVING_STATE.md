# 8. Od żywej telemetrii QHTRI do CQCL Living

## 8.1. Dwa wejścia living-state compiler

Po `NEXUS_ACTIVATION` system posiada memory/semantic snapshot związany z exact T36 identity moment. Do utworzenia bieżącego living program potrzebne jest jeszcze źródło dynamiki. W v0.3 tę rolę pełni live QHTRI/Hypercrystal telemetry.

CQCL Living otrzymuje więc dwa główne wejścia:

```text
NEXUS_ACTIVATION checkpoint
        +
CQCL-LIVE-HTRI-BINDING
        ↓
CQCL Living compiler
        ↓
OBSERVATION_ONLY
   lub
CANDIDATE_COMPILED
```

## 8.2. Dlaczego powstał CQCL vNext

Historyczny CQCL engine kompilował tekst intention przez heurystyczny emotional profile i odczytywał HTRI coherence z desktopowej ścieżki. Przy braku odczytu używał domyślnej wartości `0.85`.

vNext rozwija równoległy state compiler oparty o jawne, wersjonowane wejścia. Historyczny engine pozostaje zachowany, a nowa ścieżka wykorzystuje:

```text
current admitted State Memory evidence
current admitted NEXUS activation
current live QHTRI generation
```

Freshness i identity są częścią input contract zamiast ukrytej logiki odczytu.

## 8.3. CQCL-LIVE-HTRI-BINDING/0.1

Bridge po stronie Bio-OS produkuje strukturę:

```text
schema            CQCL-LIVE-HTRI-BINDING/0.1
source_class      NATURAL_SYSTEM_STATE
runtime_dynamics  ENDOGENOUS_RUNTIME_DYNAMICS
generation_id     HASH256
coherence         [0,1]
heartbeat_age_ms  finite
max_heartbeat_age_ms finite
live              true
authority_grant   false
evidence          {...}
```

Ta struktura jest jedynym formatem HTRI wymaganym przez CQCL vNext. Dzięki temu physical/live provider może ewoluować za wersjonowanym bridge contract.

## 8.4. Kanoniczne źródło QHTRI

Bridge czyta:

```text
/dev/shm/ciel_noema/phi
/dev/shm/ciel_noema/omega
/dev/shm/ciel_noema/tick
/dev/shm/ciel_noema/tether_runtime_status.json
```

`phi` i `omega` mają dokładnie:

```text
36 * float64 little-endian = 288 bytes
```

`tick` jest dokładnie little-endian `uint64`.

## 8.5. Stable frame acquisition

Live mmap może zmienić tick w trakcie odczytu. Bridge dlatego czyta:

```text
t0 = tick
phi
omega
t1 = tick
```

i przyjmuje frame tylko gdy:

```text
t0 == t1
```

Próba jest bounded. Brak stable frame w limicie prowadzi do jawnego błędu admission.

To zapobiega łączeniu `phi` z jednej runtime generation z `omega/tick` innej generation.

## 8.6. Distinct-tick observation window

Pierwsza wersja bridge zakładała stały interwał próbkowania. Live audit pokazał ważną właściwość mmap runtime: `tick` może pozostawać taki sam przez kilka polli i rośnie według własnej cadence.

Aktualny bridge zbiera zatem `N` kolejnych **unikalnych rosnących ticków** w bounded timeout:

```text
last_tick is None  -> accept first
new_tick > last    -> accept next
new_tick == last   -> keep polling
new_tick < last    -> reject regression
```

Default reference:

```text
samples      4 distinct ticks
poll         10 ms
max wait     2000 ms
```

## 8.7. Dynamic phi gate

Dla accepted observation window bridge liczy SHA-256 każdego 288-byte `phi` frame. Wymaga co najmniej dwóch różnych hashes:

```text
len(unique(phi_sha256)) >= 2
```

To potwierdza, że obserwowany QHTRI phase state rzeczywiście zmienił się w window.

## 8.8. Stable omega gate

Analogicznie `omega` musi być byte-stable w obserwowanym window:

```text
len(unique(omega_sha256)) == 1
```

oraz zawierać finite, nonzero values. `omega` jest więc traktowane jako natural-frequency state dla tej observation generation.

## 8.9. Fresh tether

Bridge czyta `tether_runtime_status.json` i wymaga:

```text
schema = noema.tether-runtime-status/v1
status = ACTIVE
heartbeat_ns > 0
heartbeat_age_ms <= max_heartbeat_age_ms
receipt_sha256 valid HASH256
```

Tether receipt i sequence są częścią generation evidence.

## 8.10. Dlaczego mtime nie jest freshness authority

Live audit pokazał, że mmap aktualizuje content `phi` i `tick` bez koniecznej zmiany filesystem mtime. Freshness bridge opiera się więc na content/tick/tether evidence:

```text
strict tick progression
phi content change
omega stability
fresh tether heartbeat
```

zamiast na metadata timestamp pliku.

## 8.11. Path-independent generation identity

Druga korekta bridge dotyczy identity. Runtime root `/dev/shm/ciel_noema` jest materialization path. Generation identity nie może zależeć od path string.

Content identity evidence obejmuje:

```text
source_contract
tick_start
tick_end
sample_count
phi_sha256
omega_sha256
tether_receipt_sha256
tether_seq
```

Następnie:

```text
generation_id = SHA256(
  "CQCL-LIVE-HTRI-BINDING/v0.1" ||
  canonical(identity_evidence)
)
```

`source_root_view` jest zapisany w evidence jako view metadata wraz z:

```text
identity_depends_on_path = false
```

To jest bezpośrednie zastosowanie globalnej reguły `IDENTITY != PATH`.

## 8.12. Kuramoto coherence z live phi

Bridge wylicza standardowy phase resultant dla 36 phases:

```text
c = (1/36) * sum_j cos(phi_j)
s = (1/36) * sum_j sin(phi_j)

r = sqrt(c^2 + s^2)
```

oraz bounded:

```text
coherence = clamp(r, 0, 1)
```

Ten scalar trafia do CQCL jako observed HTRI coherence. Nie jest capability ani authority.

## 8.13. CQCL Living Program

Nowy dataclass reprezentuje content-addressed program living state. Compiler tworzy:

```text
schema
status
program_id
source_state_object_id
nexus_activation_object_id
crystal
nexus
dictionary
htri
active_terms
semantic_tree
state_variables
intention_candidate
computation_path
execution_trace
authority_grant
execution_admitted
```

`program_id` jest SHA-256 domain-separated hash canonical core.

## 8.14. Ponowna walidacja NEXUS activation

CQCL wymaga:

```text
schema = PNV-NEXUS-ACTIVATION/0.1
authority_class = DERIVED_WORKING_STATE_BINDING
authority_grant = false
semantic_equivalence_grant = false
```

Następnie ponownie wylicza `activation_binding_id` i sprawdza crystal context.

## 8.15. Crystal-context equality

Compiler wymaga zgodności:

```text
CRYSTAL_ID
CONFIGURATION_SHA256
BOOT_EPOCH
PHASE_INDEX
SPINOR_SHEET
```

pomiędzy memory checkpoint i activation binding.

Dictionary binding jest również ponownie weryfikowany: commit, state SHA, relation SHA, state/relation counts oraz identity pin muszą odpowiadać expected v0.1 source.

## 8.16. Active set defense

Compiler sprawdza:

```text
active_terms <= 16
unique term_id
finite coherence
0 <= coherence <= 1
finite phase
finite informational_action
finite angular_distance
authority_grant = false
semantic_equivalence = false
```

To defense-in-depth pomiędzy memory i cognition.

## 8.17. HTRI binding validation

CQCL sprawdza:

```text
schema = CQCL-LIVE-HTRI-BINDING/0.1
source_class = NATURAL_SYSTEM_STATE
live = true
authority_grant = false
0 <= coherence <= 1
heartbeat_age_ms finite
max_heartbeat_age_ms positive
heartbeat_age_ms <= max
valid generation_id
```

Zatem nawet bridge output nie jest przyjmowany wyłącznie po nazwie typu.

## 8.18. Coupled coherence candidate

v0.1 tworzy parameter-free bounded coupling statistic:

```text
C_coupled = sqrt(
    C_NEXUS * C_HTRI
)
```

W programie nazywa się:

```text
coupled_coherence_candidate
```

Jest evidence scalar, który łączy bieżący semantic projection z dynamiką oscylatorową bez dodatkowej free scale.

## 8.19. Pozostałe state variables

Compiler utrzymuje m.in.:

```text
nexus_coherence
htri_coherence
coupled_coherence_candidate
active_mean_coherence
active_max_coherence
mean_informational_action
active_term_count
```

Wszystkie wartości przechodzą finite/range checks.

## 8.20. Observation-only

Jeśli `intention_candidate` nie został dostarczony:

```text
status = OBSERVATION_ONLY
```

Program opisuje aktualny memory + NEXUS + HTRI state i może służyć do diagnostyki, evidence lub dalszego candidate generation.

## 8.21. Candidate compiled

Jeśli jawny candidate został dostarczony, source v0.1 musi należeć do:

```text
GREMLIN
EXPLICIT_CONTEXT
NEXUS
```

Candidate payload jest content-addressed, a wynik:

```text
status = CANDIDATE_COMPILED
```

W obu stanach pozostaje:

```text
authority_grant   = false
execution_admitted = false
```

Przejście do wykonania wymaga dalszego PNCAP/AUX admission path.

## 8.22. Computation path

v0.1 jawnie zapisuje:

```text
STATE_MEMORY_NEXUS_ACTIVATION
LIVE_HTRI_BINDING
CQCL_RELATIONAL_STATE_COMPILE
```

Jest to minimalny audit trail logicznego przebiegu compiler input→output.

## 8.23. GitHub Actions evidence

Pierwszy CQCL workflow uruchomił exact branch checkout, ale test collection zatrzymał istniejący root `conftest.py`, który importował Orbital wymagający `numpy`. Workflow instalował początkowo tylko `pytest`.

Po dodaniu minimalnej zależności:

```text
python -m pip install pytest numpy
```

run dla commit:

```text
1cbbd3b680aae139859bbe1168798fde4206e746
```

wykonał isolated suite:

```text
python -m pytest -q tests/test_cqcl_living_v01.py
```

z wynikiem:

```text
....... [100%]
7/7 PASS
```

Checkout, Python setup, dependency install i test step zakończyły się success.

## 8.24. QHTRI evidence

Earlier direct-telemetry conformance zapisał:

```text
checks_passed 28
checks_total  28
classification NATURAL_SYSTEM_STATE / ENDOGENOUS_RUNTIME_DYNAMICS
phi_unique_frames 40
window_ticks 40
```

Bridge CQCL korzysta z tych samych podstawowych invariants i dodaje content-addressed generation identity, bounded stable-frame acquisition oraz fresh tether gate.

## 8.25. Pełna living-state pętla

Frontier v0.3 można teraz zapisać jako:

```text
T36 Identity
 -> State Memory crystal checkpoint
 -> full Dictionary projection
 -> Identity NEXUS generation
 -> NEXUS_ACTIVATION checkpoint
          +
    live QHTRI telemetry
          ↓
CQCL Living compiler
          ↓
observation / bounded intention candidate
```

Ta ścieżka posiada już osobne implementacje każdego elementu. Kolejną bramką jest jeden end-to-end live execution receipt obejmujący cały łańcuch w jednej spójnej generation window.

## 8.26. Miejsce GREMLIN-a

GREMLIN może wejść po utworzeniu observation state i zaproponować candidate na podstawie:

```text
current memory lineage
NEXUS active set
Dictionary declared relations
QHTRI current coherence/dynamics
relational-isomorphism traversal
```

CQCL content-addressuje taki candidate, a wykonanie pozostaje kolejnym etapem admission.

## 8.27. Znaczenie cognition boundary

W v0.3 „cognition input” ma po raz pierwszy ten sam rodzaj provenance co wcześniejsze warstwy systemowe. Semantic context wskazuje exact Dictionary generation. Memory context wskazuje exact checkpoint. Phase context wskazuje exact T36 state. Dynamic context wskazuje exact QHTRI generation. Compiler output jest content-addressed.

To pozwala traktować przyszłe decision, recall i candidate mechanisms jako dalsze specjalizacje PN Transition Spine zamiast osobnej, nieauditowalnej warstwy.
