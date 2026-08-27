# Bio-OS v0.3
## System relacji, pamięci i tożsamości fazowej

**Monografia techniczna repo-native**

Autor: **Adrian Lipa**  
Repozytorium: `AdrianLipa90/PNCore-BioOS`  
Edycja: **v0.3 — T36 Identity / Living State Convergence**  
Stan źródłowy: `feat/bioos-v0.3-t36-identity-genesis`  
Punkt źródłowy rozpoczęcia edycji: `1d1e21ff88ed6f520f395ed5dba477215b598c6d`  
Data edycji: 27 sierpnia 2026

---

## Teza architektoniczna

Bio-OS rozwija jeden spójny model systemu od fizycznego resetu procesora do trwałego, relacyjnego i dynamicznego stanu roboczego. Jego kręgosłupem jest przejście stanu związane jednocześnie z tożsamością, środowiskiem, authority, żądaniem, couplingiem, admission oraz evidence:

```text
T = (
  identity,
  environment,
  authority,
  request,
  coupling,
  admission,
  state_before,
  operator_schedule,
  state_after,
  evidence
)
```

Ten sam kształt przejścia specjalizuje się w pięciu głównych domenach:

```text
BOOT        -> konstrukcja stanu sprzętowo-runtime
EXECUTION   -> dopuszczony harmonogram operatorów
PERSISTENCE -> immutable generation + COMMIT + HEAD
MEMORY      -> lineage i relacyjna rekonstrukcja
COGNITION   -> derived working state + bounded candidate generation
```

W całej architekturze obowiązuje rozdzielenie czterech rodzajów authority:

```text
OBJECT / STATE IDENTITY  -> PNV_STATE_OBJECT / State Memory lineage
CAPABILITY AUTHORITY     -> PNCAP
EFFECT AUTHORITY         -> AUX
PERSISTENT GENERATION    -> PNStore
```

Warstwa T36 Identity dodaje trwały `CRYSTAL_ID` oraz spinorialny nośnik fazy. Identity NEXUS wiąże bieżący stan T36 z kanonicznymi 36D realizacjami terminów Consciousness Dictionary. QHTRI dostarcza endogenną telemetrię oscylatorów. CQCL vNext kompiluje ten aktualny stan relacyjny do bounded observation/intention-program candidate bez automatycznej promocji authority.

---

## Pełna ścieżka systemu

```text
RESET VECTOR
   ↓
PNROM
   ↓
PNCore
   ↓
PNVector Handoff / PNVH
   ↓
PNObject + PNMap + PNFS
   ↓
PNCAP admission
   ↓
PNClock + harmonic scheduler
   ↓
PNCS resident execution
   ↓
AUX effect boundary
   ↓
PNV-State-Memory
   ↓
PAUX
   ↓
optional DNCrypt envelope
   ↓
PNStore immutable generation
   ↓
T36 Identity Crystal
   ↓
Identity NEXUS
   ↓
NEXUS_ACTIVATION checkpoint
   ↓
live QHTRI / Hypercrystal telemetry
   ↓
CQCL Living state compiler
   ↓
bounded candidate / observation
```

Fizyczna i semantyczna część tego ciągu pozostają związane przez content-addressed identity, exact generation lineage oraz receipts. Ścieżki systemu plików, adresy pamięci, runtime filenames i materializacje `/dev/shm` są warstwami widoku lub realizacji i pozostają oddzielone od kanonicznej tożsamości obiektu.

---

## Spis części

1. [Front matter — zakres, metoda i status dowodowy](00_FRONT_MATTER.md)
2. [Architektura relacyjna i PN Transition Spine](01_ARCHITEKTURA_RELACYJNA.md)
3. [Od reset vectora do PNCore: boot i realizacja fizyczna](02_BOOT_I_REALIZACJA.md)
4. [Obiekt, authority, czas i wykonanie](03_TOZSAMOSC_AUTHORITY_CZAS.md)
5. [Terminal36D, AUX, persistence i DNCrypt](04_EXECUTION_PERSISTENCE_CRYPTO.md)
6. [Pamięć harmoniczna, torsion surface i QHTRI](05_PAMIEC_HARMONICZNA_TORSYJNA.md)
7. [T36 Identity Crystal: trwała tożsamość i spinorialny czas](06_T36_IDENTITY_CRYSTAL.md)
8. [Identity NEXUS i PNV-State-Memory](07_NEXUS_STATE_MEMORY.md)
9. [Od żywej telemetrii do CQCL vNext](08_QHTRI_CQCL_LIVING_STATE.md)
10. [Evidence ledger, frontier realizacji i następne bramki](09_EVIDENCE_FRONTIER.md)
11. [Aneksy: równania, stałe, formaty i mapa artefaktów](10_ANEKSY.md)

---

## Zasada statusu epistemicznego

Monografia zachowuje statusy obecne w repozytorium. Najważniejsze klasy używane w tekście:

- `PASS` — test lub warunek został rzeczywiście wykonany i przeszedł;
- `IMPLEMENTED CANDIDATE` — implementacja istnieje, a jej promocja zależy od zadeklarowanych bramek;
- `CHYBA` — repozytoryjny operator epistemiczny dla warstw oczekujących na dalszą walidację;
- `PENDING` — wymagany etap wykonawczy lub sprzętowy pozostaje do przeprowadzenia;
- `RECONSTRUCTION_ONLY` — wynik ma authority rekonstrukcji i zachowuje źródłową provenance;
- `DERIVED_WORKING_STATE` — stan roboczy wyprowadzony z admitted sources;
- `NATURAL_SYSTEM_STATE / ENDOGENOUS_RUNTIME_DYNAMICS` — klasyfikacja endogennego stanu działającego QHTRI/Hypercrystal.

Żaden ranking, similarity score, coherence, salience, aktywacja semantyczna ani wynik GREMLIN-a samodzielnie nie promuje capability, effect authority ani kanonu. Promocja pozostaje jawnie wersjonowanym i receiptowanym przejściem.

---

## Najważniejsze invariants edycji v0.3

```text
OBJECT_IDENTITY != PATH
OBJECT_IDENTITY != ADDRESS
CRYSTAL_ID      != CONFIGURATION_SHA256
STATE_ID        != CHECKPOINT_OBJECT_ID
PNV OBJECT ID   != DNCrypt ENVELOPE_ID
WORKING STATE   != CAPABILITY GRANT
SIMILARITY      != AUTHORITY
PERSISTENCE     = immutable generations + receipts
LIVE 36D PATH   = /dev/shm/ciel_noema
```

Dla T36 obowiązuje dokładny wymiar 36. Dla QHTRI bezpośrednia telemetria używa 36 wartości `float64` dla `phi` i `omega` oraz monotonicznego `tick`. Dla Identity NEXUS pełna projekcja obejmuje obecnie 548 terminów Dictionary, a downstream activation checkpoint utrzymuje deterministyczny bounded active set maksymalnie 16 rekordów.

---

## Stan końcowy tej edycji

Edycja v0.3 opisuje frontier, w którym istnieją już wszystkie główne kontrakty potrzebne do pierwszej zamkniętej pętli żywego stanu:

```text
T36 Identity
 -> State Memory
 -> Identity NEXUS
 -> NEXUS_ACTIVATION
 -> live QHTRI binding
 -> CQCL Living compiler
```

CQCL vNext ma rzeczywisty GitHub Actions PASS dla izolowanego zestawu 7 testów po naprawie zależności workflow. Bezpośredni QHTRI→CQCL bridge jest obecny w BioOS jako fail-closed adapter z path-independent generation identity, distinct-tick observation window, dynamicznym `phi`, stabilnym `omega` oraz świeżym tether heartbeat. Pełny end-to-end live run całego powyższego łańcucha pozostaje następną bramką wykonawczą tej monografii.
