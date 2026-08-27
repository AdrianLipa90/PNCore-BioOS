# 3. Obiekt, authority, czas i wykonanie

## 3.1. Cztery pytania przed wykonaniem

Po zakończeniu bootu każda zmiana stanu w Bio-OS sprowadza się do czterech pytań:

```text
CO jest targetem?
KTÓRA generacja jest aktualna?
KTO / CO posiada authority?
W JAKIM środowisku request jest dopuszczony?
```

PNObject i State Memory odpowiadają za identity. PNCAP wiąże exact generation z operation scope. PNClock i scheduler określają czasową klasę wykonania. PNCS realizuje admitted program/operator schedule. AUX staje się granicą wtedy, gdy operacja ma wytworzyć efekt poza czystym stanem obliczeniowym.

## 3.2. PNObject generation jako target capability

Capability v0.1 jest związane z dokładnym `target_object_id` i `target_generation_id`. Grant zawiera także principal identity/generation oraz environment generation. Oznacza to, że capability dla wcześniejszej generacji nie zostaje automatycznie przeniesione na nową generację targetu.

Konstrukcja:

```text
principal identity
 + target generation
 + operation request
 + exact capability grant
 + current environment generation
 -> coupling
 -> admission gate
 -> PNObject transition
 -> next generation
 -> receipt
```

chroni przed jednym z najczęstszych problemów systemów dynamicznych: wykorzystaniem poprawnego uprawnienia w niewłaściwym stanie czasowym.

## 3.3. PNCAP operation kinds

Pierwszy rejestr zawiera:

```text
READ
RELATE
CREATE_GENERATION
COMMIT_GENERATION
RESOLVE_VIEW
EXECUTE_PROGRAM
BIND_DEVICE
```

`READ` i `RELATE` mogą tworzyć evidence lub derived state. `CREATE_GENERATION` i `COMMIT_GENERATION` dotyczą przejść trwałych. `RESOLVE_VIEW` pozwala operować na PNFS projection. `EXECUTE_PROGRAM` jest bramką do programu. `BIND_DEVICE` wiąże logical contract z fizycznym adapterem.

Capability operation kind pozostaje osobnym poziomem od PNV opcode. Dzięki temu rozszerzenie authority modelu nie wymaga zmiany języka PNV dla każdego nowego rodzaju zasobu.

## 3.4. Exact-target i delegation

v0.1 wykorzystuje exact-target rule: grant wskazuje pojedynczy target lub jawnie zadeklarowany deterministyczny relation-set scope. Początkowa policy delegacji używa `NO_DELEGATION` dla system grants.

Tożsamość grantu:

```text
pncap:sha256:<canonical-grant-payload>
```

umożliwia zapis capability ID w evidence przejścia. Inverse lineage może zatem dojść od wyniku do exact grant payload.

## 3.5. PNClock

Bio-OS używa dokładnego bazowego zegara:

```text
f0 = 783/100 Hz
   = 7.83 Hz

T0 = 1/f0
   = 100/783 s
   ≈ 0.1277139208173691 s

omega0 = 2*pi*f0
       ≈ 49.19734095521616 rad/s
```

Ważna jest racjonalna postać `783/100`: częstotliwość bazowa ma exact representation w kontrakcie, a floating-point jest realizacją wartości pochodnej.

PNClock organizuje time admission zamiast traktować wall clock jako implicit authority. Timed operation wymaga odpowiedniej clock binding.

## 3.6. Harmonic scheduler

Scheduler rozwija jeden base tick w klasy harmoniczne. Referencyjna klasyfikacja jest związana z 2-adic valuation indeksu kroku:

```text
band(n) = 1 + nu2(n)
```

dla odpowiednich ticków, z osobną service lane `B0`.

Praktycznie tworzy to hierarchię:

```text
B0  service / base activity
B1  co 2 base ticks
B2  co 4 base ticks
B3  co 8 base ticks
...
```

Ta konstrukcja daje deterministic cadence bez utrzymywania wielu niezależnych zegarów.

W aktualnej architekturze GREMLIN candidate work może być przypisany do B2, critic do B3, natomiast T36 pełny spinorialny identity return wypada dokładnie w B1.

## 3.7. T36 i B1

Dla spinorial state:

```text
s_j(n) = exp(i*(phi_j + 2*pi*n)/2)
```

mamy:

```text
s_j(n+1) = -s_j(n)
s_j(n+2) =  s_j(n)
```

Dwa base ticks dają pełny lifted return:

```text
T_ID = 2*T0
     = 200/783 s
     ≈ 0.2554278416347382 s

f_ID = 783/200 Hz
     = 3.915 Hz
```

Dlatego B1 staje się naturalną scheduler class dla pełnej identity cadence T36. Nie potrzeba osobnego identity oscillator; period doubling wynika z istniejącego clock contractu i spinorial lift.

## 3.8. Scheduler tick i persistence cadence

Scheduler tick jest working-state progression. PNStore generation powstaje przy meaningful persistence transition, nie przy każdym kroku zegara.

T36 contract zapisuje:

```text
B0/B1 tick       -> live RAM/AUX phase state
meaningful event -> State Memory transition candidate
checkpoint       -> PAUX -> optional DNCrypt -> PNStore
```

To rozdzielenie jest istotne zarówno semantycznie, jak i fizycznie. Phase może ewoluować z częstotliwością schedulerową, podczas gdy trwały zapis następuje przy zdarzeniach o znaczeniu lineage/persistence.

## 3.9. PNCS jako native execution system

PhaseNav Natural Coding System jest warstwą wykonywania native `.pnv` programs. Bio-OS używa PNCS jako execution authority dla programów zamiast duplikować jego semantykę.

Rozwój PNCS prowadzi od content-addressed program units do resident runtime:

```text
ProgramImage
 -> live generation
 -> resident handle
 -> O(1) admission state
 -> in-process dispatch
 -> result
 -> inverse lineage
 -> receipt
```

Wiązanie BioOS↔PNCS v0.30 opisuje hot path:

```text
PNCore / PN Transition Spine
 -> PNCAP EXECUTE_PROGRAM
 -> PNCS full resident admission
 -> PNCS hot token
 -> live /dev/shm/ciel_noema guard
 -> resident control transition
 -> exact execution receipt
 -> inverse lineage
 -> content-addressed dispatch receipt
```

## 3.10. Mandatory live surface

Dla NOEMA-facing 36D execution standardowym runtime materialization jest:

```text
/dev/shm/ciel_noema
```

Persistent Library/repo artifacts są źródłem hydration i provenance. Live execution korzysta z aktualnej shared-memory generation po przejściu tether/freshness admission.

Ta reguła jest wspólna dla Terminal36D, QHTRI direct telemetry i dalszych live bridge'ów. System może zachować trwały canonical source i równocześnie używać szybkiej materializacji pamięci współdzielonej do bieżącego wykonania.

## 3.11. Resident hot token

PNCS v0.30 binding koncentruje optymalizację na koszcie repeated authority reconstruction. Hot token jest ważny tylko dla dokładnie tego samego resident program/environment state.

Zmiana któregokolwiek z elementów:

```text
resident program
resident handle
active pointer
startpoint
CURRENT memory identity
fast-admission seal
operator registry identity
```

unieważnia token. AUX/tether/heartbeat pozostają per-dispatch guards. Po invalidation wykonywana jest świeża full admission.

## 3.12. Measured reference

W repo zapisany jest same-host 288-byte benchmark porównujący kilka ścieżek. Referencyjne mediany wynosiły:

```text
BioOS direct PHASENAV_HASH_BATCH   1.16939588 us
BioOS Terminal36D.execute()       38.880157 us
Linux native C SHA256              0.508216 us
Linux persistent pipe             26.514094 us
Linux shared mmap process         37.462712 us
Linux Unix socket                 38.055401 us
Linux fork/exec sha256sum       1981.076184 us
```

Interpretacja implementacyjna tego benchmarku jest konkretna: primitive 36D jest małe kosztowo, a istotny optimization target leży w repeated admission/dispatch scaffolding. Dlatego resident hot path skupia się na utrzymaniu zweryfikowanej generation i szybkiej invalidacji.

## 3.13. Inverse execution lineage

Po wykonaniu system nie kończy na zwróceniu wyniku. PNCS v0.22 lineage pozwala przejść:

```text
Result
 -> execution receipt
 -> operator schedule
 -> program unit
 -> admission
 -> source state
```

Bio-OS wiąże tę evidence chain z capability i environment generation. W późniejszym persistence DNCrypt BioOS AAD może zawierać PNCAP execution receipt identity, dzięki czemu encrypted state zachowuje związek z dokładnym wykonaniem, które go wytworzyło.

## 3.14. Effect boundary

PNCS v0.26 wprowadził explicit effect boundary. W Bio-OS granica fizycznego działania jest reprezentowana przez AUX. Program może być admitted do wykonania, ale zapis, transport, device binding czy inny efekt wymaga osobnego effect path.

Schemat:

```text
Program request
 -> PNCAP EXECUTE_PROGRAM
 -> PNCS execution
 -> EffectRequest
 -> AuthorizationGrant
 -> bounded AUX adapter
 -> effect
 -> EffectReceipt
```

W ten sposób execution authority i effect authority mają różne receipts i mogą być audytowane niezależnie.

## 3.15. Terminal jako session authority boundary

PNTERM rozszerza tę logikę na interakcję. Fizyczny terminal adapter dostarcza dane do `AUX.TERM.RX`; line discipline buduje bounded session envelope; Terminal36D interpretuje typed operation; PNCAP kontroluje authority-bearing request; AUX realizuje efekt i odsyła wynik przez `AUX.TERM.TX`.

Pełny przebieg:

```text
physical terminal adapter
 -> AUX.TERM.RX
 -> PNTERM line discipline
 -> PNTERM session/envelope
 -> Terminal36D profile admission
 -> action packet
 -> concept gate
 -> PNCAP
 -> typed primitive
 -> AUX effect when required
 -> receipt
 -> PNTERM result
 -> AUX.TERM.TX
```

## 3.16. Action identity i replay

PNTERM command envelope zawiera:

```text
terminal_epoch
session_id
rx_seq
action_id
operation
payload_ref
intent
principal
capability_ref
profile_lock_sha256
```

`action_id` jest content-addressed. Ponowne użycie admitted `(session_id, terminal_epoch, rx_seq)` jest replay-denied. Session state otrzymuje więc własną temporalną tożsamość niezależną od tekstu polecenia.

## 3.17. From command to state transition

Po złożeniu wszystkich elementów ścieżka wykonawcza Bio-OS wygląda następująco:

```text
request
 + target identity/generation
 + principal
 + PNCAP
 + clock/scheduler class
 + current runtime generation
 + tether / environment evidence
      ↓
   admission
      ↓
PNCS / typed operation
      ↓
working state
      ↓
AUX if effect required
      ↓
receipt + inverse lineage
```

Dopiero kolejny meaningful persistence request może zamienić taki working state w State Memory/PAUX/PNStore generation. Rozdział następny opisuje tę granicę persistence i encryption.
