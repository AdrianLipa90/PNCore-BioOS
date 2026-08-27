# 6. T36 Identity Crystal: trwała tożsamość i spinorialny czas

## 6.1. Problem ciągłości

Do v0.2.x Bio-OS posiadał już obiekty, generation lineage, dokładny zegar, harmonic scheduler, persistence i dynamiczną pamięć. v0.3 dodaje warstwę, która wiąże te elementy w trwałą tożsamość systemową przechodzącą przez boot continuation, zmianę programu i zmianę konfiguracji.

T36 Identity Crystal jest persistent identity anchor oraz live spinorial phase carrier. Jego źródłami są:

```text
PNVector Handoff / 36D source state
PN Clock 7.83 Hz
spin-1/2 / SU(2) period doubling
State Memory lineage
PNROM / PNR / program / scheduler bindings
```

## 6.2. Authority split

T36 zachowuje istniejące role:

```text
persistent object identity  -> PNV_STATE_OBJECT / State Memory
capability authority        -> PNCAP
effect authority            -> AUX
persistent generation       -> PNStore
36D bootstrap state         -> PNVH
semantic term realization   -> Consciousness Dictionary
```

T36 posiada własny `CRYSTAL_ID` jako identity anchor oraz `CONFIGURATION_SHA256` jako commitment realizacji.

## 6.3. Exact base clock

Clock authority:

```text
f0 = 783/100 Hz = 7.83 Hz
T0 = 100/783 s
omega0 = 2*pi*f0
```

T36 korzysta z tego samego clock contractu. Identity cadence wynika z liftu spinorialnego.

## 6.4. Spinorial lift

Dla komponentu fazowego `phi_j` i base tick `n`:

```text
s_j(n) = exp(i*(phi_j + 2*pi*n)/2)
```

Stąd:

```text
s_j(n+1) = -s_j(n)
s_j(n+2) =  s_j(n)
```

Projective `2*pi` return i lifted `4*pi` return są osobnymi obserwablami. Full lifted identity return:

```text
T_ID = 2*T0
     = 200/783 s
     ≈ 0.2554278416347382 s

f_ID = f0/2
     = 783/200 Hz
     = 3.915 Hz
```

To dokładnie scheduler band B1.

## 6.5. Spinor sheet

Physical record nie przechowuje 36 zespolonych spinorów. Exact 288-byte 36D base vector pozostaje w PNVH. T36 identity record przechowuje `phase_index`, a:

```text
spinor_sheet = phase_index & 1
```

jest wyprowadzane deterministycznie.

To redukuje persistent footprint i utrzymuje jedno source of truth dla 36D payload.

## 6.6. Genesis anchor

Trwała tożsamość zaczyna się od explicit admitted cold genesis. Tworzony jest jeden `GENESIS_ANCHOR`. Następnie:

```text
CRYSTAL_ID = SHA256(
  ASCII("T36-ID/v0.1") ||
  GENESIS_ANCHOR
)
```

`CRYSTAL_ID` jest invariantem linii kontynuacji.

Raw anchor jest provisioning material. Persistent receipt zapisuje:

```text
GENESIS_ANCHOR_COMMITMENT = SHA256(
  ASCII("T36-GENESIS-COMMIT/v0.1") ||
  GENESIS_ANCHOR
)
```

## 6.7. Identity i configuration

Tożsamość i konfiguracja są rozdzielone:

```text
CRYSTAL_ID != CONFIGURATION_SHA256
```

Configuration commitment obejmuje dokładne source/build bindings:

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

Nowy program, scheduler lub realization może więc utworzyć nowy configuration commitment pod tą samą crystal identity, o ile continuity przejdzie admission.

## 6.8. Origin binding

Pierwsza realization wyprowadza także:

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

Origin binding wiąże genesis identity z podstawowymi źródłami, z których powstała pierwsza realizacja.

## 6.9. 256-byte identity record

Persistent/working record v0.1 ma dokładnie 256 bajtów:

```text
offset  size  field
0       4     magic = "T36I"
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

Integer fields są little-endian. Hash/binding fields mają dokładnie 32 bytes.

## 6.10. Record jako identity/configuration envelope

T36 record nie duplikuje 288-byte vector payload. Wiąże jego hash i source context. Dzięki temu persistent record może pozostać stałego rozmiaru, podczas gdy source phase vector zachowuje własny carrier.

Logical relation:

```text
T36 identity record
  BINDS -> PNVH payload identity
  BINDS -> source context
  BINDS -> basis
  BINDS -> configuration
  CARRIES -> phase_index / boot_epoch
```

## 6.11. Cold genesis

Cold genesis path:

```text
PNROM
 -> PNCore
 -> clock admission
 -> PNVH verification
 -> PNStore recovery
 -> explicit COLD_GENESIS admission
 -> create GENESIS_ANCHOR
 -> derive CRYSTAL_ID
 -> create T36 identity record
 -> State Memory CRYSTAL_GENESIS
 -> Sigma_0
```

Explicit admission chroni przed przypadkowym utworzeniem drugiej tożsamości w istniejącej linii.

## 6.12. Continuation boot

Continuation:

```text
PNROM
 -> PNCore
 -> clock admission
 -> PNVH verification
 -> PNStore recovery
 -> recover GENESIS_ANCHOR
 -> recover latest crystal descendant
 -> verify CRYSTAL_ID continuity
 -> increment boot_epoch
 -> bind current configuration
 -> BOOT_CONTINUATION
 -> Sigma_0
```

`boot_epoch` jest monotonicznym licznikiem restartów/continuations w persistent identity lineage.

## 6.13. BOOT_GAP

Przerwa zasilania jest jawna:

```text
previous live state
 -> BOOT_GAP
 -> BOOT_CONTINUATION
```

`BOOT_GAP` zachowuje ostatni admitted `phase_index` i state oraz zwiększa `boot_epoch` według kontraktu continuation. Dzięki temu timeline rozróżnia obserwowaną live evolution od nieobserwowanego okresu power-off.

## 6.14. State Memory relations

PNV-State-Memory jest właścicielem logical lineage T36. Relacje v0.3 obejmują:

```text
CRYSTAL_GENESIS
CRYSTAL_CHECKPOINT
BOOT_GAP
BOOT_CONTINUATION
```

T36 physical record dostarcza crystal context, a State Memory tworzy content-addressed checkpointy.

## 6.15. State ID i checkpoint object ID

W memory lineage ważna jest separacja:

```text
state_id != checkpoint object_id
```

`state_id` identyfikuje bieżący logical state crystal lineage. `object_id` checkpointu identyfikuje konkretną memory record/generation, której metadata może zostać rozszerzona o nowe evidence bez udawania, że zmieniła się fizyczna faza.

Ta zasada jest później użyta przez `NEXUS_ACTIVATION`.

## 6.16. Boot pre-validation

W x86_64 realization boot materializuje T36 record przy `0x5900` i przed PNCore sprawdza header, vector dimension oraz exact equality source bindings. Następnie wykonuje closure test:

```text
sheet(n)   = 0
sheet(n+1) = 1
sheet(n+2) = 0
```

oraz wymaga, aby po dwóch krokach:

```text
CRYSTAL_ID unchanged
CONFIGURATION_SHA256 unchanged
BOOT_EPOCH unchanged
phase_index += 2
```

To jest executable form podstawowego `4*pi` invariant w boot realization.

## 6.17. Persistence cadence

T36 nie zamienia każdej identity cadence w PNStore write. Live phase progression pozostaje w RAM/AUX. Meaningful events mogą tworzyć State Memory candidates. Checkpoint persistence korzysta z PAUX, opcjonalnego DNCrypt i PNStore.

```text
B1 identity cycle
 -> working state
 -> optional meaningful transition
 -> State Memory checkpoint
 -> PAUX
 -> optional DNCrypt
 -> PNStore
```

## 6.18. Configuration evolution

Jeżeli program lub scheduler zostanie zmieniony, nowa configuration jest wyliczana z nowych bindings. Continuation może zachować `CRYSTAL_ID`, gdy identity continuity przechodzi validation.

Taka struktura umożliwia historyczne pytania:

```text
jaki był system?
na jakim programie?
na jakim schedulerze?
z jakiego PNVH?
w którym boot_epoch?
w którym phase_index?
```

bez utożsamiania odpowiedzi na te pytania z samym trwałym identity anchor.

## 6.19. Fail-closed gates

Główne gates T36:

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

## 6.20. Evidence status

Aktualny v0.3 contract ma status `ARCHITECTURE_CANDIDATE / NUMERICALLY_CLOSED / EXECUTION_VALIDATION_PENDING`. Pierwsza physical realization ma status `IMPLEMENTED HOST/ASSEMBLY CANDIDATE`.

W repo istnieją host derivation tools, exact 256-byte codec path, assembly routines, State Memory lineage i PAUX exact reconstruction bindings. QEMU boot, bare-metal physical boot, device-backed persistence i production genesis provisioning pozostają kolejnymi execution gates.

## 6.21. Dlaczego T36 otwiera NEXUS

Dopiero po utworzeniu trwałego crystal context można jednoznacznie pytać o relację bieżącego stanu do kanonicznych 36D realizacji terminów. Identity NEXUS wykorzystuje dokładnie ten context:

```text
CRYSTAL_ID
CONFIGURATION_SHA256
BOOT_EPOCH
PHASE_INDEX
SPINOR_SHEET
SOURCE_STATE_OBJECT_ID
```

Każda semantic projection staje się więc funkcją określonej, receiptowanej chwili tożsamości. To jest temat następnego rozdziału.
