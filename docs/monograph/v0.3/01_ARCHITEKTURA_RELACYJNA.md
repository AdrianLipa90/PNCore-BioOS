# 1. Architektura relacyjna i PN Transition Spine

## 1.1. Punkt wyjścia

Bio-OS organizuje system wokół relacji pomiędzy stanami. Dane, proces wykonania, pamięć, capability i fizyczna realizacja są opisywane poprzez jawne obiekty oraz przejścia, które pozostawiają provenance. Dzięki temu ten sam język strukturalny może objąć reset procesora, zmianę obiektu, zapis trwałej generacji i utworzenie pamięciowego checkpointu.

Centralnym kontraktem jest `PN_TRANSITION_SPINE_V0_1`:

```text
IDENTITY -----> GATE
                  ^
ENVIRONMENT ----->|
AUTHORITY -------->|
REQUEST -> COUPLING|
ENVIRONMENT -> COUPLING
COUPLING --------->GATE

GATE --ADMITS--> TRANSITION
TRANSITION --PRODUCES--> STATE
TRANSITION --RECEIPTED_BY--> EVIDENCE
STATE --EVIDENCED_BY--> EVIDENCE
IDENTITY --IDENTIFIES--> STATE
ENVIRONMENT --GENERATES--> STATE
```

To nie jest jedynie diagram zależności. Jego rolą jest wymuszenie, aby wynik nie pojawiał się bez znanego targetu, środowiska, authority i dowodu przejścia.

## 1.2. Kanoniczna krotka przejścia

Formalnie:

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

Każda specjalizacja może mieć własny format, ale nie powinna tracić tych ról.

W boot `identity` może wskazywać tożsamość systemową i konfigurację, `environment` — aktualny stan sprzętu, `authority` — admitted boot/clock/genesis contract, a `state_after` — `Sigma_0`.

W execution `request` wskazuje operator lub program, `authority` jest exact capability, `operator_schedule` jest dopuszczonym schedule, a `evidence` zawiera receipt wykonania.

W PNStore `state_before` jest bieżącą trwałą generacją, `operator_schedule` realizuje prepare/barrier/publish/barrier, a `state_after` jest nowym immutable generation wskazywanym przez poprawny HEAD.

W State Memory `state_after` jest nowym content-addressed checkpointem z `lineage_parent` wskazującym dokładnego przodka.

## 1.3. Immutable state-after

Jedna z najważniejszych konsekwencji Spine brzmi:

```text
state_after is immutable after admission
```

Kolejna zmiana prowadzi do kolejnej generacji. Ta zasada przechodzi przez cały stos:

```text
PNObject G_n -> PNObject G_{n+1}
PNStore G_n  -> PNStore G_{n+1}
Memory O_n   -> Memory O_{n+1}
NEXUS A/B    -> next complete NEXUS generation
Torsion A/B  -> next complete memory-surface generation
```

Double buffering w NEXUS i torsion memory jest runtime odpowiednikiem tej samej idei: reader otrzymuje kompletną generację, a writer przygotowuje następną poza aktywnym HEAD.

## 1.4. Relacja przed nazwą ścieżki

PNFS realizuje fundamentalną regułę:

```text
OBJECT IDENTITY != PATH
```

Przykładowa relacja:

```text
root --NAME:system--> A --NAME:genesis--> B
```

może zostać wyrenderowana jako:

```text
/system/genesis
```

ale tożsamość `B` pozostaje własnością PNObject identity/generation. Path jest projekcją relacji. To rozdzielenie ma znaczenie również poza filesystemem.

W PNMap obowiązuje analogiczna separacja:

```text
OBJECT_IDENTITY != ADDRESS
```

Adres pamięci reprezentuje konkretną realizację. Pointer może się zmienić; object identity jest związana z treścią i lineage.

W DNCrypt:

```text
PNV_STATE_OBJECT.object_id != ENVELOPE_ID
```

W T36 Identity:

```text
CRYSTAL_ID != CONFIGURATION_SHA256
```

W State Memory activation:

```text
state_id != checkpoint object_id
```

To jedna zasada architektoniczna przechodząca przez wiele domen.

## 1.5. PNObject

PNObject jest logicznym nośnikiem tożsamości i generacji. W praktyce jego dane mogą mieć wiele realizacji: w RAM, na PNStore, jako PAUX, jako view PNFS lub jako źródło fizycznego mappingu. O tym, który obiekt jest aktualnym targetem przejścia, decyduje exact identity/generation, a nie tekstowa nazwa.

PNV-State-Memory pokazuje najbardziej konkretną postać tej logiki. `PNV_STATE_OBJECT` zawiera:

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

Obiekt jest wyprowadzany z kanonicznej treści:

```text
OBJECT_ID = BLAKE2B256("PNV_STATE_OBJECT" || CORE)
```

oraz posiada osobny integrity binding:

```text
INTEGRITY = BLAKE2B256(
    "PNV_STATE_INTEGRITY" || OBJECT_ID || CORE
)
```

Dzięki temu `VERIFY` może ponownie policzyć oba zobowiązania i odrzucić zmieniony stan.

## 1.6. Relacje jako system adresowania

Pierwszy kierunek adresowania State Memory ma postać:

```text
ADDRESS = DOMAIN || PHASE_CLASS || LINEAGE_COMMITMENT || OBJECT_ID
```

To ważne przesunięcie: adres logiczny zawiera znaczenie domenowe i lineage zamiast ograniczać się do miejsca na urządzeniu. Physical address i persistent media offset są realizacjami niższej warstwy.

PNFS może następnie tworzyć czytelne ścieżki jako view. PNStore może przechowywać extent. AUX może materializować endpoint runtime. Żaden z tych carrierów nie przejmuje source identity.

## 1.7. Authority jako osobny obiekt

PNCAP jest generation-bound capability admission. Capability ID ma postać:

```text
pncap:sha256:<canonical-grant-payload>
```

i wiąże:

```text
principal_object_id
principal_generation_id
target_object_id
target_generation_id
operation_kind
capability_scope
environment_generation_id
expiry_condition_or_none
delegation_policy
```

Początkowy registry posiada zero grantów. Zmiana stanu wymaga exact matching capability.

Podstawowe operation kinds v0.1:

```text
READ
RELATE
CREATE_GENERATION
COMMIT_GENERATION
RESOLVE_VIEW
EXECUTE_PROGRAM
BIND_DEVICE
```

To operation kinds capability-domain. Wykonanie programu nie jest tym samym co uzyskanie efektu fizycznego. Efekty przechodzą przez AUX.

## 1.8. Coupling

Pole `coupling` w Transition Spine pozwala opisać zależność pomiędzy requestem i aktualnym środowiskiem. Jest miejscem, w którym można wymagać zgodności generation, clock, target, runtime binding czy semantic source.

Przykłady:

- Terminal36D bridge wiąże request z exact profile lock i bieżącym tetherem;
- T36 Identity wiąże 36D payload z genesis anchor, configuration i clock;
- NEXUS wiąże bieżący crystal context z dokładnym compile receipt Dictionary;
- CQCL Living wiąże NEXUS activation checkpoint z live HTRI generation.

W każdym przypadku coupling jest evidence-bearing. Similarity lub phase alignment może być częścią coupling score, lecz authority nadal pochodzi z osobnego źródła.

## 1.9. Evidence i inverse lineage

Przejście kończy się evidence. Dzięki temu system może rekonstruować:

```text
state generation
 -> transition
 -> capability
 -> request
 -> principal
 -> environment generation
```

PNCS v0.22 rozwija tę ideę jako inverse execution lineage. PNStore przechowuje transition identity w immutable history. State Memory posiada `lineage_parent`. DNCrypt posiada envelope/receipt, a BioOS dodaje expected-AAD equality gate. NEXUS aktywacja wiąże generation identity pełnej projekcji oraz exact Dictionary compile state.

Monografia traktuje tę odwracalność jako jeden z najważniejszych mechanizmów kontroli systemu: wynik powinien być powiązany ze źródłem i drogą wykonania.

## 1.10. Recovery jako normalne przejście

Recovery korzysta z tej samej logiki. PNStore waliduje oba HEAD slots i extents, wybierając najnowszą poprawną generację. State Memory weryfikuje obiekt przed `RESTORE`. DNCrypt recovery weryfikuje receipt, expected AAD, AEAD, PAUX oraz PNV identity. T36 continuation boot odzyskuje genesis anchor i sprawdza continuity `CRYSTAL_ID`.

Recovery nie jest zatem specjalnym „trybem awaryjnym” odłączonym od modelu. Jest wersjonowanym przejściem ze swoim admission i evidence.

## 1.11. O(1) live admission i trwała provenance

W warstwie live projekt rozdziela hydration od powtarzalnego hot path. Kanoniczne persistent artifacts służą jako recovery/provenance. Bieżące 36D wykonanie działa na `/dev/shm/ciel_noema`. Po zweryfikowanym nawodnieniu bieżącej generation runtime może używać content-pinned state i O(1) admission structures zamiast ponownego skanowania całej persistent historii przy każdym kroku.

Ta sama zasada jest obecna w PNCS resident runtime, Terminal36D profile hydration oraz Identity NEXUS A/B publication.

## 1.12. GREMLIN jako warstwa kandydatów i audytu

GREMLIN pozostaje bounded warstwą generowania kandydatów i krytyki. Może szukać relacyjnych izomorfizmów, proponować nowe zależności, porównywać struktury PAUX, analizować graf harmoniczny i dostarczać candidate paths do cognition. Wynik GREMLIN-a trafia do dalszej walidacji.

W architekturze authority:

```text
GREMLIN candidate
 -> validation / critic
 -> explicit admission candidate
 -> PNCAP/AUX path if promoted
```

Ta pozycja jest szczególnie ważna po wprowadzeniu Identity NEXUS i CQCL: GREMLIN może korzystać z aktualnego kontekstu pamięciowego i semantycznego, a execution authority pozostaje poza jego bezpośrednią kontrolą.

## 1.13. Konsekwencja dla całego Bio-OS

Po połączeniu tych elementów Bio-OS można czytać jako graf generacji:

```text
identity
  + environment
  + authority
  + request
      ↓
   admission
      ↓
  transition
      ↓
immutable state generation
      ↓
   evidence
      ↓
next admitted relation
```

Boot, wykonanie, persistence, pamięć i cognition różnią się operatorami i typami stanu, lecz zachowują ten sam kręgosłup. Dzięki temu v0.3 może dołożyć T36 Identity i NEXUS bez tworzenia osobnego modelu władzy czy pamięci: nowe warstwy wpinają się w istniejący Transition Spine.
