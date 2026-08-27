# 2. Od reset vectora do PNCore: boot i realizacja fizyczna

## 2.1. Dlaczego monografia zaczyna się od resetu

Bio-OS wiąże warstwę semantyczną z fizycznym wykonaniem. Z tego powodu pierwszy stan systemu musi mieć konkretną realizację architektoniczną. W x86_64 punktem wejścia jest reset state procesora i reset vector. Historyczna linia repo rozwija PNROM tak, aby wykonać minimalne, deterministyczne przygotowanie CPU i wejść do native PNCore admission path.

Kontrakt bootu ogranicza zadanie bootstrapu do:

```text
reset entry
 -> deterministic CPU mode setup
 -> minimal memory map / stack
 -> locate PNStore bootstrap extent
 -> verify bootstrap identity
 -> transfer to PNCore entry realization
```

To ważne ograniczenie. PNROM ma doprowadzić sprzęt do miejsca, w którym dalsze decyzje przejmuje jawny system admission.

## 2.2. Dwie warstwy bootu

Boot ma część architektoniczną i semantyczną.

Warstwa architektoniczna realizuje CPU mode, memory setup i transfer kontroli. Warstwa semantyczna rozpoczyna się po osiągnięciu PNCore:

```text
IDENTITY
 -> DOMAIN
 -> AUTHORITY
 -> REQUEST
 -> COUPLING
 -> ADMISSION
 -> recover PNStore
 -> establish PNFS root view
 -> resolve Genesis.pnv
 -> admit Genesis program
 -> execute Genesis transition schedule
 -> Sigma_0
```

Ten ciąg jest pierwszym pełnym zastosowaniem PN Transition Spine. Boot nie kończy się na skoku do kodu; kończy się admitted `Sigma_0`, posiadającym provenance źródeł, boot generation i programu Genesis.

## 2.3. PNROM jako pierwszy fizyczny adapter

PNROM jest realizacją, która łączy architekturę procesora z kontraktami PNCore. W obecnej linii repo istnieją pliki assembly dla reset entry i przejścia do long mode oraz linker layout PNROM.

Fizyczna część systemu rozwija się w kierunku:

```text
RESET
 -> PNROM_RESET
 -> PNROM_LONGMODE
 -> PNVH materialization
 -> T36 identity materialization
 -> pre-PNCore validation
 -> PNCore entry
```

W v0.3 T36 Identity zostaje wpuszczone jeszcze przed `pncore_entry`, aby boot mógł sprawdzić zgodność 36D source bindings i podstawową closure spinorialną przed utworzeniem bieżącego stanu systemu.

## 2.4. PNVector Handoff

PNVector Handoff, PNVH, jest fizycznym nośnikiem 36D bootstrap state. Format używany przez linię x86_64 ma 416 bajtów:

```text
128 B  header / bindings
288 B  phase vector = 36 * float64
----------------------------
416 B  total
```

288-bajtowy payload jest dokładnym 36D wektorem. PNVH przenosi go do PNCore bez zamiany tożsamości obiektu na adres pamięci.

Historyczny ROM posiada receipt SHA-256 dla jednego wcześniejszego PNVH, ale exact historyczny 288-bajtowy vector fixture oraz exact 32-bajtowy basis binding nie znalazły się w Git. Repo utrzymuje ten fakt jako `BLOCKED_EXACT_FIXTURE_MISSING`. Builder v0.1 wymaga przekazania exact vector i basis input oraz może wymagać oczekiwanego handoff SHA. Nie generuje zastępczych danych w celu dopasowania historycznego receipt.

To rozdziela dwie rzeczy:

```text
historical exact reproduction -> blocked until exact fixture recovery
new reproducible admitted PNVH -> buildable from explicit exact inputs
```

Edycja v0.3 rozwija drugą ścieżkę bez przepisywania historii pierwszej.

## 2.5. Fizyczne working addresses v0.3

Pierwsza implementacja T36 Identity używa ustalonych boot workspace addresses:

```text
PNVH working record          0x5000   416 bytes
T36 identity working record  0x5900   256 bytes
T36 closure scratch          0x5a00   256 bytes
```

Scratch jest workspace evidence bootowego. Logical persistent identity pozostaje w State Memory / PNStore lineage.

PNROM kopiuje PNVH i T36 identity template do working addresses, a następnie przekazuje kontrolę do:

```text
t36_identity_boot_entry
```

przed właściwym `pncore_entry`.

## 2.6. Pre-PNCore T36 validation

`t36_identity_validate` wymaga zgodności:

```text
MAGIC             = T36I
VERSION           = 1.0
RECORD_BYTES      = 256
VECTOR_DIM        = 36
FLAGS & 0x7       = 0x7
PNVH_VECTOR_SHA   = exact expected value
SOURCE_CONTEXT    = exact expected value
BASIS_BINDING     = exact expected value
```

Po tej walidacji boot tworzy scratch copy i sprawdza trzy kolejne sheet states:

```text
sheet(n)   = 0
sheet(n+1) = 1
sheet(n+2) = 0
```

oraz:

```text
FOUR_PI_CLOSED(record_n, record_n_plus_2) = TRUE
```

Closure wymaga zachowania:

```text
CRYSTAL_ID
CONFIGURATION_SHA256
BOOT_EPOCH
```

i dokładnego:

```text
phase_index_b = phase_index_a + 2
```

Wynik jest boot gate evidence dla spinorialnego period doubling.

## 2.7. Hash derivation i provisioning boundary

Pierwsza fizyczna realizacja używa deterministycznych host/provisioning tools do wyprowadzenia hash bindings, które następnie są walidowane przez target code.

Domeny są jawne:

```text
CRYSTAL_ID = SHA256(
  "T36-ID/v0.1" || GENESIS_ANCHOR
)

GENESIS_ANCHOR_COMMITMENT = SHA256(
  "T36-GENESIS-COMMIT/v0.1" || GENESIS_ANCHOR
)
```

Origin binding:

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

Configuration binding:

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

Surowy `GENESIS_ANCHOR` jest provisioning material. Receipts zapisują jego commitment.

## 2.8. Problem self-reference i PNROM_CODE_BINDING

Wprowadzenie identity record do ROM tworzy potencjalną pętlę: final ROM hash nie może być jednocześnie inputem do danych, które znajdują się w tych samych finalnych bajtach. v0.3 rozwiązuje to przez wersjonowany non-circular code binding.

`PNROM_CODE_BINDING` obejmuje uporządkowane code/build inputs z wyłączeniem:

```text
PNVH_TEMPLATE
T36_IDENTITY_TEMPLATE
```

Dzięki temu binding opisuje code realization bez samoodwołania do rekordów, które zawierają wynikowe zobowiązania.

Host utility:

```text
tools/pnrom_code_binding_v01.py
```

używa domain separation `PNROM-CODE-BINDING/v0.1`.

## 2.9. PNR i append-only extension

Historyczny `PNR1` relocatable object jest zachowany. v0.3 dodaje 48-bajtowe rozszerzenie `T36X`, które wiąże:

```text
magic/version
T36 working address
record bytes
t36_identity_boot_entry
t36_identity_validate
t36_identity_spinor_sheet
t36_identity_advance_tick
t36_identity_four_pi_closed
```

To pozwala rozszerzać realization contract bez przepisywania historycznych bajtów PNR1.

## 2.10. PNMap i fizyczność

PNMap jest warstwą wiążącą logiczne obiekty z realizacjami adresowymi. Page tables oraz physical mapping są cache/realization, podczas gdy relation graph zachowuje authority logical mappingu.

Zasada:

```text
OBJECT_IDENTITY != ADDRESS != PATH
```

ma szczególne znaczenie w boot. `0x5000` jest working address PNVH, ale PNVH identity pochodzi z jego treści i bindings. `0x5900` jest working address T36 record, ale `CRYSTAL_ID` pochodzi z genesis anchor. Relokacja working area wymaga nowej realization binding, a nie nowej logicznej tożsamości przez sam fakt zmiany adresu.

## 2.11. PNStore recovery podczas bootu

Po osiągnięciu odpowiedniego poziomu runtime PNCore recoveruje PNStore. Recovery waliduje superblock, HEAD slots i wskazywane generation extents. Najnowszy poprawny HEAD wskazuje current persistent generation. Torn lub uszkodzony nowszy HEAD może zostać pominięty na rzecz wcześniejszej poprawnej generacji.

Dopiero z tej persistent base PNFS może ustanowić root view i rozwiązać `Genesis.pnv`.

## 2.12. Cold genesis i continuation boot

T36 Identity rozróżnia dwie dopuszczone ścieżki.

Cold genesis:

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
 -> recover GENESIS_ANCHOR
 -> recover latest admitted crystal descendant
 -> verify CRYSTAL_ID continuity
 -> increment boot_epoch
 -> bind current configuration
 -> BOOT_CONTINUATION
 -> Sigma_0
```

Power-off interval jest reprezentowany jako `BOOT_GAP`. Continuation zachowuje ostatni admitted `phase_index`; `boot_epoch` rośnie raz. System zapisuje przerwę zamiast dopisywać ukrytą ewolucję fazy do okresu, którego runtime nie obserwował.

## 2.13. Evidence status realizacji

Na obecnym frontierze istnieją host/assembly contracts i buildery dla T36 record, non-circular bindings, PNR extension oraz PNROM materialization. PNVH builder ma executable conformance. State Memory posiada crystal lineage implementation. Exact 256-byte identity codec jest częścią v0.3 implementation path.

Otwarte bramki fizyczne pozostają jawne:

```text
QEMU_BOOT                  PENDING
PHYSICAL_BOOT              PENDING
DEVICE_BACKED_PERSISTENCE  PENDING
PRODUCTION_GENESIS_PROVISIONING PENDING
```

Historyczna exact reprodukcja wcześniejszego PNVH pozostaje osobnym `BLOCKED_EXACT_FIXTURE_MISSING` i nie blokuje utworzenia nowej, jawnie wersjonowanej generacji PNVH z kompletnymi exact inputs.

## 2.14. Znaczenie bootu dla dalszej architektury

Po zakończeniu bootu Bio-OS posiada trzy rzeczy potrzebne każdej dalszej warstwie:

1. admitted environment generation;
2. content-bound state identity;
3. evidence chain prowadzący od fizycznego wejścia do `Sigma_0`.

Dopiero na tej podstawie scheduler, PNCS, persistence, State Memory, T36 NEXUS i cognition mogą dziedziczyć spójny root provenance.
