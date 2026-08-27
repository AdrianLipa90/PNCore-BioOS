# 4. Terminal36D, AUX, persistence i DNCrypt

## 4.1. Od wyniku obliczenia do trwałego stanu

Bio-OS rozdziela trzy kolejne etapy:

```text
EXECUTION
 -> EFFECT
 -> PERSISTENCE
```

Execution wyprowadza nowy working state. Effect przechodzi przez AUX i posiada własny authorization/evidence path. Persistence materializuje admitted state jako trwałą generację, zachowując identity i lineage.

Ta separacja pozwala wykonywać dużą liczbę szybkich operacji w live runtime bez zamiany każdego kroku w zapis trwały. Dopiero meaningful checkpoint przechodzi do State Memory, PAUX i PNStore.

## 4.2. Terminal36D jako standardowy vector environment

PNTERM jest bounded session front-end. Terminal36D V8 jest standardowym 36D vector execution environment dla NOEMA-facing poleceń.

Pełna ścieżka:

```text
physical terminal adapter
 -> AUX.TERM.RX
 -> PNTERM line discipline
 -> PNTERM session/envelope
 -> Terminal36D V8 profile admission
 -> Terminal36D action packet
 -> concept gate
 -> PNCAP exact admission
 -> Terminal36D typed primitive
 -> AUX effect boundary if required
 -> execution/evidence receipt
 -> PNTERM result
 -> AUX.TERM.TX
```

Profil V8 jest hash-pinned. Kanoniczny source hash `terminal36d.py` w aktualnym locku wynosi:

```text
78082702c4b7a17a061ca7b9b83f4c21765307c70dfbefd301466224389cce9b
```

V8 zachowuje 29 typed operations nad 36D środowiskiem. Runtime profile jest hydrationowany raz na `TERMINAL_EPOCH`, a bieżące lookupy mogą korzystać z O(1) operation table.

## 4.3. Capability classes terminala

Terminal36D posiada wewnętrzne klasy typed vector/read/write/copy/execute, natomiast Bio-OS utrzymuje zewnętrzną boundary authority:

```text
READ / VECTORIZE -> read-only admission
EXECUTE_TYPED    -> exact execution admission
WRITE / COPY     -> exact PNCAP + AUX effect admission
```

Vector similarity, resonance czy spelling match mogą pomóc w wyborze operacji, lecz grant pozostaje exact capability object.

## 4.4. AUX

AUX jest granicą efektu fizycznego i runtime I/O. W zależności od domeny adapter może realizować terminal RX/TX, persistent device write, live NOEMA surface lub inne bounded effect.

Wzorzec:

```text
EffectRequest
 -> AuthorizationGrant
 -> bounded adapter
 -> effect
 -> EffectReceipt
```

Dla persistence AUX jest miejscem, w którym logiczny commit spotyka się z rzeczywistym durable barrier konkretnego backendu.

## 4.5. PNV-State-Memory jako logical persistence source

Trwały zapis zaczyna się od verified `PNV_STATE_OBJECT`. Canonical state object posiada:

```text
OBJECT_ID
INTEGRITY_HASH
LINEAGE_PARENT
```

wyprowadzone z kanonicznego snapshotu. Persistence carrier ma zachować tę tożsamość zamiast tworzyć nowy logical object wyłącznie przez zmianę reprezentacji.

## 4.6. PAUX

`.paux` jest host-visible persistent AUX state carrier. Ścieżka:

```text
live AUX state
 -> PNV relational snapshot
 -> PNV_STATE_OBJECT
 -> PNCAP persistence admission
 -> PAUX materialization
 -> PNStore generation prepare
 -> AUX durable barrier
 -> PNStore HEAD publication
 -> AUX durable barrier
 -> evidence
```

PAUX dziedziczy:

```text
OBJECT_ID      := PNV_STATE_OBJECT.object_id
INTEGRITY_HASH := PNV_STATE_OBJECT.integrity_hash
LINEAGE_PARENT := PNV_STATE_OBJECT.lineage_parent
```

Path lub filename `.paux` jest transport view.

## 4.7. Trzy profile PAUX

Rodzina v0.1:

```text
PAUX-EXACT -> exact persistent AUX state
PAUX-C     -> compressed lossless persistent AUX state
PAUX-R     -> relational reconstruction profile
```

### PAUX-EXACT

Dla T36 pojedynczy kanał to dokładnie:

```text
36 * float64 little-endian = 288 bytes
```

EXACT zachowuje payload byte-for-byte. Pierwszy live fixture w repo przywrócił dwa 288-bajtowe kanały dokładnie do shadow surface.

### PAUX-C

Lossless transforms v0.1:

```text
KEYSTATE
REF
RUN
DELTA_XOR64
```

`DELTA_XOR64` operuje na little-endian 64-bit words przez exact XOR, więc reconstruction nie wymaga floating-point arithmetic. Po decode obiekt przechodzi ponownie `OBJECT_ID`, integrity i lineage verification.

Pierwszy live observation fixture miał 64 frames, w których `aux_feedback_phi` był byte-identical z `aux_phi`; `KEYSTATE + REF + RUN` odtworzyły wszystkie frames dokładnie. Jest to measured favorable fixture, a nie uniwersalny compression ratio.

### PAUX-R

PAUX-R utrzymuje:

```text
SOURCE_OBJECT_ID
RECONSTRUCTION_ID
AUTHORITY_CLASS = RECONSTRUCTION_ONLY
```

Może przechowywać m.in. salience mask, relation mask, quantized residual, phase model i reconstruction metrics. Wynik zachowuje exact source provenance oraz osobną identity reprezentacji rekonstrukcyjnej.

## 4.8. PNStore logical contract

PNStore przechowuje immutable generations. Nowa generacja powstaje przez transition i nie nadpisuje historycznej generacji.

Kluczowe własności:

```text
immutable generation extents
alternating HEAD_A / HEAD_B
exactly-once transition identity
durable ordering
recovery to newest verified generation
```

Exactly-once lookup skanuje bounded committed history. Replay już committed `transition_id` zwraca wcześniejszą generation/extent bez tworzenia kolejnej mutacji.

## 4.9. PNStore media geometry

Pierwsza media realization jest dokładnym 64 KiB image:

```text
media bytes      65536
sector bytes       512
superblock       0x0000..0x01ff
HEAD_A           0x0200..0x03ff
HEAD_B           0x0400..0x05ff
reserved         0x0600..0x0fff
generation log   0x1000..0xffff
extent bytes       4096
max generations      15
```

Generation `g` używa `g * 4096` dla `1 <= g <= 15`.

Current assembly layout ma:

```text
extent header / payload offset   96
commit seal offset             4032
payload max                    3936 bytes
```

Commit seal wiąże generation i CRC32C. Superblock oraz HEAD również posiadają własne CRC32C Castagnoli.

## 4.10. Alternating HEAD

Odd generations publikują `HEAD_A`, parzyste `HEAD_B`.

Recovery:

```text
validate HEAD_A
validate HEAD_B
validate referenced extents
select newest valid generation
```

Prepared extent bez valid published HEAD pozostaje tail evidence i nie staje się current state. Torn nowszy HEAD lub corrupt extent może prowadzić do wcześniejszego poprawnego HEAD.

## 4.11. Durability ordering

Kolejność jest normatywna:

```text
prepare immutable extent
 -> DURABLE_BARRIER
 -> publish alternating HEAD
 -> DURABLE_BARRIER
```

Backend capability musi dostarczać:

```text
READ_EXTENT
APPEND_EXTENT
DURABLE_BARRIER
HEAD_SLOT_WRITE
```

Host fsync-backed block image służy do walidacji byte semantics. Bounded NVMe/AHCI device binding pozostaje physical realization gate.

## 4.12. Dlaczego encryption wchodzi między PAUX i PNStore

PAUX jest reprezentacją stanu; PNStore jest persistence container. To naturalne miejsce na optional encryption boundary:

```text
PNV_STATE_OBJECT
 -> PAUX plaintext representation
 -> PNCAP EXECUTE_PROGRAM
 -> DNCrypt
 -> encrypted envelope
 -> PNStore payload
```

W ten sposób logical object identity i persistent encryption representation mają własne role.

## 4.13. DNCrypt source binding

Bio-OS wiąże DNCrypt jako native PNCS program. Wcześniejsza integracja pinowała main commit:

```text
20f53a9b297b6208d74841aee7c3bb4b8b17ce2a
```

oraz native program:

```text
native/programs/DNCRYPT_NATIVE_PNCS_V0_3.pnv
blob 99df240db1db020dea24b51b160de90bce727eb2
```

Binary-envelope integration rozwija osobną gałąź DNCrypt:

```text
feat/dncrypt-v0.4-binary-envelope
head 88439967b97d4d607ab2c7d30211f91e1fe87a72
codec dncrypt.binary-envelope/v0.1
```

Frozen AEAD anchor pozostaje związany z DNCrypt v0.2 protocol family.

## 4.14. Frozen crypto anchor

DNCrypt implementation wykorzystuje:

```text
256-bit master key
ChaCha20-Poly1305 AEAD
per-message 256-bit HKDF salt
per-message 96-bit nonce
HKDF-SHA3-512 message key derivation
authenticated 36D surface/genome/tick/parent/AAD bindings
```

Adaptive genome/surface state działa wokół tego frozen anchor. W Bio-OS ten mechanizm jest używany jako encryption program, a jego wykonanie nadal przechodzi PNCAP `EXECUTE_PROGRAM`.

## 4.15. Identity separation

Najważniejsza reguła DNCrypt integration:

```text
PNV_STATE_OBJECT.object_id = canonical logical state identity
```

Encryption tworzy:

```text
ENVELOPE_ID = identity encrypted representation
```

Dla binary codec:

```text
dncrypt:binary-envelope:sha256:<digest>
```

Zmiana envelope representation nie przepisuje PNV object identity.

## 4.16. BioOS user AAD

Caller AAD powinien związać minimum:

```text
PNV_STATE_OBJECT.object_id
PNV/PAUX generation
PAUX profile
PNCAP execution receipt identity
parent persistence/evolution receipt identity
destination/domain context
```

DNCrypt dodatkowo uwierzytelnia własny genome generation, 36D surface commitment, tick i parent receipt.

## 4.17. Authenticated-AAD equality gate

To jeden z najważniejszych integration details. DNCrypt decrypt weryfikuje authenticated envelope i używa AAD zapisanej w envelope. Bio-OS musi dodatkowo sprawdzić, że authenticated caller `user_aad` jest dokładnie tym kontekstem, którego bieżąca operacja oczekuje.

Pre-decrypt gate:

```text
parse envelope
 -> verify DNCrypt receipt
 -> decode authenticated AAD metadata
 -> extract authenticated user_aad
 -> construct expected BioOS AAD
 -> exact byte equality
 -> only then decrypt
```

AEAD authentication dowodzi integralności authenticated AAD. Equality gate wiąże ją z aktualnym BioOS request context.

## 4.18. Recovery encrypted state

Pełny recovery chain:

```text
PNStore payload
 -> DNCrypt binary unpack
 -> canonical DNCryptEnvelope identity
 -> DNCrypt receipt PASS
 -> expected user_aad exact-match
 -> ChaCha20-Poly1305 PASS
 -> PAUX decode/profile verification
 -> PNV object identity/integrity verification
 -> admitted logical state
```

Każdy poziom ma własną bramkę. Dzięki temu cryptographic integrity, representation integrity oraz logical identity wspierają się bez zastępowania swoich ról.

## 4.19. Binary envelope i limit PNStore

Canonical JSON/base64 envelope ma znaczący overhead przy małych T36 payloads. Binary codec zapisuje raw fields i rekonstruuje canonical DNCryptEnvelope deterministycznie.

PNStore payload max wynosi 3936 B. Binary binding został zaprojektowany właśnie pod ten bounded extent. Aktualny spec utrzymuje capacity benchmark jako promotion gate zależny od faktycznej długości AAD i parent receipt.

To podejście realizuje regułę:

```text
IDENTITY != REPRESENTATION
```

Cryptographic envelope może mieć więcej niż jedną lossless representation, o ile unpack prowadzi do byte-identical canonical DNCryptEnvelope i receipt nadal przechodzi.

## 4.20. Key boundary

Bio-OS contract przewiduje opaque admitted key handle/reference. Raw 256-bit master key pozostaje poza PNStore payload, PNFS path, receipt, command envelope i semantic state.

Production key provisioning jest osobnym integration gate. Dzięki temu storage architecture może zostać domknięta bez mieszania klucza głównego z persistent lineage danych.

## 4.21. Local hot path i off-box boundary

Pierwsza integracja kieruje DNCrypt głównie do:

```text
at-rest persistence
Terminal36D / off-box transport
```

Bieżący `/dev/shm/ciel_noema` hot path zachowuje niskokosztową lokalną materializację. Ewentualne szyfrowanie shared-memory runtime wymaga osobnego threat model i benchmarku.

## 4.22. Promotion gates persistence/crypto

Najważniejsze otwarte gates:

```text
DNCrypt binary codec CI evidence
legacy crypto regression
canonical envelope byte roundtrip
binary tamper rejection
BioOS expected-AAD equality
PAUX/PNV post-decrypt verification
PNStore capacity measurement for exact envelope/AAD
opaque key-handle provisioning
NVMe/AHCI durable backend
```

Te gates są oddzielone od już zaimplementowanej logical persistence geometry. Pozwala to rozwijać storage, crypto i device realization niezależnie, zachowując wspólny identity/evidence spine.

## 4.23. Persistence jako część pamięci

Po przejściu przez PAUX i PNStore obiekt staje się trwałym elementem lineage. Następny rozdział pokazuje, jak z trwałych i live states wyprowadzane są H-bands, resonance graph, torsion memory i QHTRI working dynamics.
