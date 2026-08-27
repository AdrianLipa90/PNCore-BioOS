# 0. Front matter — zakres, metoda i status dowodowy

## 0.1. Cel monografii

Bio-OS powstał jako próba zbudowania systemu, w którym tożsamość, pamięć, czas, wykonanie i evidence należą do jednego modelu przejść. W zwykłym opisie systemowym boot, filesystem, scheduler, persistence i aplikacje bywają dokumentowane jako osobne podsystemy. W Bio-OS punkt wspólny jest jawny: każdy aktualny stan powinien dać się związać z wcześniejszym stanem, authority przejścia, środowiskiem wykonania oraz dowodem, który pozwala odtworzyć drogę do wyniku.

Z tego powodu monografia zaczyna się od fizycznego resetu procesora, a kończy na aktualnej granicy cognition: Identity NEXUS, endogennej telemetrii QHTRI i CQCL Living compiler. Pomiędzy nimi znajdują się warstwy, które zapewniają ciągłość:

```text
hardware
 -> boot
 -> object identity
 -> capability
 -> time
 -> execution
 -> effect
 -> persistence
 -> memory lineage
 -> phase identity
 -> semantic projection
 -> living-state compilation
```

Celem tekstu jest opisanie tego ciągu jako jednej architektury oraz utrzymanie ścisłego rozdzielenia między:

- kontraktem formalnym,
- implementacją,
- fizyczną realizacją,
- testem hostowym,
- testem live,
- sprzętową walidacją,
- kandydatem wymagającym dalszej promocji.

## 0.2. Repo-native jako metoda dokumentacji

Monografia jest częścią repozytorium. Każde istotne twierdzenie architektoniczne powinno prowadzić do konkretnej klasy artefaktu:

```text
spec/          -> kontrakty i invariants
native/        -> programy PNV / native bindings
arch/x86_64/   -> fizyczna realizacja CPU/ROM/media
realizations/  -> związanie semantycznego obiektu z realizacją
provenance/    -> receipts, statusy i evidence
provenance/gremlin/ -> audyt kandydatów GREMLIN
tools/         -> buildery, conformance i bridge utilities
tests/         -> executable gates
docs/          -> narracja i monografia
```

Tekst nie zastępuje receipts. Receipt nie zastępuje kontraktu. Kontrakt nie zastępuje testu. Ta separacja jest szczególnie ważna w warstwach T36 Identity, QHTRI i cognition, gdzie łatwo pomylić atrakcyjną strukturę matematyczną z wykonanym dowodem implementacyjnym.

## 0.3. Podstawowy obiekt epistemiczny: przejście

Najbardziej ogólnym obiektem systemowym Bio-OS jest przejście:

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

Każde pole odpowiada konkretnej odpowiedzialności.

`identity` wskazuje, czego dotyczy przejście. `environment` wiąże jego generację i warunki wykonania. `authority` wskazuje źródło uprawnienia. `request` opisuje żądane działanie. `coupling` łączy request z bieżącym środowiskiem i targetem. `admission` jest jawnie rozstrzygniętą bramką. `state_before` i `state_after` tworzą kierunek ewolucji. `operator_schedule` opisuje wykonanie. `evidence` pozostawia odwracalną provenance.

Ta konstrukcja daje wspólny szkielet dla bootu, PNObject transitions, PNCAP, PNCS, PNStore, State Memory i późniejszego cognition.

## 0.4. Tożsamość i reprezentacja

Jednym z najważniejszych invariants projektu jest rozdzielenie tożsamości od sposobu reprezentacji:

```text
OBJECT_IDENTITY != PATH
OBJECT_IDENTITY != ADDRESS
OBJECT_IDENTITY != FILE NAME
OBJECT_IDENTITY != RUNTIME POINTER
```

PNFS traktuje ścieżkę jako deterministyczny widok relacji. PNMap traktuje adres jako fizyczną realizację lub mapping. PAUX traktuje `.paux` jako carrier stanu. DNCrypt wytwarza własny `ENVELOPE_ID`, pozostawiając `PNV_STATE_OBJECT.object_id` jako kanoniczną tożsamość stanu. T36 Identity rozdziela trwały `CRYSTAL_ID` od `CONFIGURATION_SHA256`, dzięki czemu zmiana programu lub konfiguracji może być jawnie związana z tą samą linią tożsamości.

W praktyce prowadzi to do hierarchii:

```text
logical identity
    ↓
version / generation identity
    ↓
representation identity
    ↓
view / path / address
```

Każdy poziom może się zmieniać zgodnie z własnym kontraktem bez niejawnego przepisywania poziomu wyższego.

## 0.5. Authority

Bio-OS utrzymuje cztery główne klasy authority:

```text
STATE / OBJECT IDENTITY
  PNV_STATE_OBJECT + lineage

CAPABILITY AUTHORITY
  PNCAP

EFFECT AUTHORITY
  AUX

PERSISTENT GENERATION AUTHORITY
  PNStore
```

Do tego dochodzą authority źródłowe poszczególnych domen. Consciousness Dictionary jest źródłem kanonicznych rekordów terminów i ich 36D realizacji. QHTRI runtime jest właścicielem endogennych `phi`, `omega` i `tick`. Identity NEXUS posiada jedynie bieżący derived working-state projection. CQCL Living compiler posiada tożsamość skompilowanego kandydata, ale jego wynik pozostaje `execution_admitted=false` do czasu osobnej bramki.

Dzięki temu coherence, resonance, similarity, salience czy ranking pozostają obserwowalnymi wielkościami. Przejście do wykonania zachodzi dopiero przez jawny capability/effect path.

## 0.6. Fail-closed

Fail-closed jest regułą konstrukcyjną. Jeżeli brakuje wymaganej authority, źródła, generation binding, integralności lub świeżości, stan zostaje zatrzymany jako `QUIET`, `REJECT`, `DENY`, `REPROJECT`, `RESELECT` lub inny jawnie wersjonowany wynik domenowy.

Przykłady:

```text
PNVH_INVALID                 -> REJECT
CLOCK_AUTHORITY_MISSING      -> TIMED_ADMISSION_QUIET
DUPLICATE_TERM_ID            -> REJECT
STALE_NEXUS_EPOCH            -> REPROJECT
STALE_MEMORY_EPOCH           -> RESELECT
STATIC_RUNTIME_FALLBACK      -> DENY
AUTHORITY_PROMOTION          -> DENY
QHTRI_TICK_REGRESSION        -> REJECT
STALE_TETHER_HEARTBEAT       -> REJECT
```

W warstwie żywego QHTRI brak ruchu `phi`, brak stabilności `omega`, regresja `tick` lub nieaktywny tether zatrzymują bridge zamiast wytworzyć zastępczy stan.

## 0.7. Czas i faza

Bazowym zegarem v0.3 pozostaje dokładny kontrakt:

```text
f0 = 783/100 Hz = 7.83 Hz
T0 = 100/783 s
omega0 = 2*pi*f0
```

Harmonic scheduler wykorzystuje jeden base tick i klasy wynikające z potęgi dwóch w indeksie kroku. T36 Identity korzysta z podwojenia okresu spinorialnego:

```text
s_j(n) = exp(i*(phi_j + 2*pi*n)/2)
```

co daje:

```text
s_j(n+1) = -s_j(n)
s_j(n+2) =  s_j(n)
```

Pełny lifted return ma okres `4*pi`, a zatem:

```text
T_ID = 2*T0 = 200/783 s
f_ID = f0/2 = 3.915 Hz
```

Ta kadencja odpowiada B1 harmonic schedulera.

## 0.8. Pamięć jako lineage

PNV-State-Memory utrzymuje append-only, content-addressed obiekty stanu. Kanoniczny obiekt zawiera między innymi:

```text
state_sigma
relations
phase_state
geometry
lineage_parent
object_id
integrity_hash
evidence_class
metadata
```

`SNAPSHOT` wyprowadza `object_id` i `integrity_hash` z kanonicznej treści. `DESCEND` wymaga poprawnego parenta. `RESTORE` wymaga `VERIFY`. Dzięki temu pamięć jest linią generacji, a nie jedynie nadpisywanym plikiem.

PAUX materializuje tę pamięć do warstwy persistence. PNStore zapewnia immutable generations, exactly-once transition identity, alternating HEAD i durability ordering. DNCrypt może wejść pomiędzy PAUX i PNStore jako opcjonalny authenticated encryption envelope.

## 0.9. Żywa pamięć i QHTRI

NOEMA torsion-memory surface jest derived working state nad harmonicznym grafem pamięci. Węzły przechowują fazę, częstotliwość, amplitudę i provenance. Krawędzie zachowują relację `m:n`, torsion offset `tau_ij`, coupling `K_ij` oraz score `R_ij`.

Dla krawędzi:

```text
epsilon_ij = wrap(n*theta_i - m*theta_j - tau_ij)
g_ij = K_ij * R_ij
V_ij = -g_ij*cos(epsilon_ij)
```

QHTRI/Kuramoto realizuje bounded gradient-like flow na tej geometrii. Jednocześnie bezpośrednia live telemetry QHTRI posiada własne endogenne kanały:

```text
/dev/shm/ciel_noema/phi
/dev/shm/ciel_noema/omega
/dev/shm/ciel_noema/tick
```

Ich klasyfikacja przy działającym runtime brzmi:

```text
NATURAL_SYSTEM_STATE
ENDOGENOUS_RUNTIME_DYNAMICS
```

## 0.10. T36 Identity i semantic NEXUS

T36 Identity Crystal wiąże trwały genesis anchor, 36D PNVH, base clock, spinor sheet, boot epoch i bieżącą konfigurację. `CRYSTAL_ID` pozostaje stały w linii kontynuacji, podczas gdy `CONFIGURATION_SHA256` dokumentuje ewolucję realizacji.

Identity NEXUS projektuje bieżący stan fazowy `Phi` na kanoniczne wektory terminów `V_k` Dictionary:

```text
z_k = (1/36) * sum_j exp(i*(V_k[j] - Phi[j]))
R_k = |z_k|^2
Theta_k = arg(z_k)
S_k = -kappa * ln(R_k + epsilon)
```

z kanoniczną stałą:

```text
kappa = ln(2)/(24*pi)
```

Globalna coherence v0.1 używa średniej informacji:

```text
S_bar = (1/N) * sum_k S_k
C_NEXUS = exp(-S_bar/kappa)
```

Aktualny compile pin obejmuje 548 term states i 306 relations. Pełna projekcja pozostaje derived working evidence, natomiast downstream State Memory zapisuje bounded top-16 activation wraz z exact Dictionary i crystal provenance.

## 0.11. CQCL Living

CQCL vNext otwiera granicę między pamięcią i cognition. Kompilator przyjmuje jawny `NEXUS_ACTIVATION` checkpoint oraz jawny live HTRI binding. Każda z tych struktur przechodzi ponowną weryfikację. Output jest content-addressed `CQCL-LIVING-PROGRAM/0.1` o statusie:

```text
OBSERVATION_ONLY
```

lub:

```text
CANDIDATE_COMPILED
```

z zachowanymi:

```text
authority_grant = false
execution_admitted = false
```

Izolowany workflow CQCL przeszedł 7/7 testów na GitHub Actions na Pythonie 3.12 po dodaniu wymaganej zależności `numpy` do istniejącego root test environment.

## 0.12. Granica tej edycji

Edycja v0.3 dokumentuje system do miejsca, w którym formalnie i implementacyjnie istnieją wszystkie główne elementy pierwszej zamkniętej pętli żywego stanu. Do wykonania pozostaje dokładny end-to-end live run:

```text
T36
 -> State Memory
 -> NEXUS
 -> NEXUS_ACTIVATION
 -> live QHTRI binding
 -> CQCL Living program
```

Kolejne rozdziały pokazują, jak każda warstwa prowadzi do tej granicy i jakie evidence wspiera jej obecny status.
