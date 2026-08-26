ANEKS A — KLUCZOWE RÓWNANIA
## A.1. Zestaw referencyjny
f₀ = 7.83 Hz = 783/100 Hz
bazowa częstotliwość scheduler/clock
band(n)=1+ν₂(n)
dyadyczna klasa admission
deadline(n)=base_tsc+floor(nN/D)
exact rational TSC deadline
f_k/f₀=p_k/q_k
harmonic band ratio
2πr_k=N_kλ_k
orbital closure
f_i/f_j=m/n
pair commensurability
δ=wrap(nθ_i−mθ_j)
phase-lock invariant
ε=wrap(nθ_i−mθ_j−τ_ij)
torsion residual
g_ij=K_ijR_ij
effective coupling
V_e=−g_e cos ε_e
edge potential
Z_T=Σg_e exp(iε_e)/Σg_e
torsion resultant
κ=ln2/(24π)
canonical coupling scalar
K_ij=κ/max(1,d_i,d_j)
degree-bounded coupling policy
ANEKS B — MAPA ARTEFAKTÓW REPOZYTORIUM
## B.1. Główne dokumenty implementacyjne

Repozytoryjny stan użyty do monografii: AdrianLipa90/PNCore-BioOS, feature commit e8134c7329799b593da53308eebc43a21e00050f. Główna gałąź w momencie przygotowania dokumentu pozostawała na 67a2c6aaad21db8016d7e7386d394663ec0cad69.
ANEKS C — SŁOWNIK POJĘĆ
## C.1. Skróty i role


## Zakończenie
PNCore-BioOS przeszedł w tej wersji drogę od bardzo niskiego poziomu — reset vectora, ROM-u, long mode i page tables — do wysokiego poziomu dynamicznej pamięci, która ma własne pasma harmoniczne, relacje m:n, torsion offsets i Kuramoto flow. Najważniejsze jest jednak to, że te warstwy są spięte jednym ciągiem authority i evidence.
Dlatego pamięć torsyjna jest naturalnym końcem obecnego rozdziału rozwoju, a nie początkiem całego systemu. Jej możliwość wynika z wcześniejszych decyzji: PNVector daje uporządkowany stan, PNClock daje fazową oś czasu, PNStore daje pokolenia, PAUX daje trwałą reprezentację, PNCAP oddziela skojarzenie od uprawnienia, a AUX domyka efekt. Dopiero na tej podstawie rezonans i Kuramoto mogą stać się mechanizmem systemowym.


| Najkrótsza mapa systemu PNROM buduje warunki wejścia do PNCore. PNVector przenosi 36D stan. PNR wiąże program z realizacją fizyczną. PNMap ustala mapowanie. PNClock i scheduler porządkują czas. PNCAP przyznaje uprawnienia. AUX jest granicą efektów. PNStore/PAUX utrwalają stan. H-bands i resonance graph nadają pamięci geometrię. NOEMA torsion surface utrzymuje jej żywy stan, a QHTRI/Kuramoto nadaje mu dynamikę. |
| --- |


| Kręgosłup projektu STATE ma provenance. REALIZATION ma identity. TIME ma exact source. CAPABILITY ma explicit grant. EFFECT przechodzi przez AUX. PERSISTENCE ma generation/HEAD. MEMORY ma geometry i phase. ORCHESTRATION działa dopiero po admission. |
| --- |


| Element | Aktualny anchor | Znaczenie |
| --- | --- | --- |
| PNROM | 0xF0000 | 64 KiB reset ROM |
| Reset vector | 0xFFFF0 / offset 0xFFF0 | pierwsze wejście wykonania |
| PNMap root | CR3 / 0x7000 | anchor mapowania x86 |
| PNVector | 0x5000 | firmware→PNCore state carrier |
| Sigma₀ | 0x5200 | pierwszy admitted state candidate |
| Transition evidence | 0x5300 | świadectwo przejścia |
| PNMap evidence | 0x5400 | świadectwo mapowania |


| Dlaczego PNMap jest ważny Klasyczna tablica stron opisuje fizyczne mapowanie x86. PNMap dodaje do tego warstwę relacyjną i evidence. Dzięki temu późniejszy PNObject/PNFS może operować na relacjach, podczas gdy x86 page walk pozostaje konkretną realizacją resolvera. |
| --- |


| Pasmo | Częstotliwość | Okres | Przykładowa rola |
| --- | --- | --- | --- |
| B0 | 7.830000 Hz | 127.714 ms | bounded service lane |
| B1 | 3.915000 Hz | 255.428 ms | queue/admission/light I/O |
| B2 | 1.957500 Hz | 510.856 ms | GREMLIN microstep/candidate |
| B3 | 0.978750 Hz | 1021.711 ms | critic/relational graph |
| B4 | 0.489375 Hz | 2043.423 ms | bounded numerics/slices |
| B5 | 0.2446875 Hz | 4086.845 ms | bounded persistence/serialization |
| B6 | 0.12234375 Hz | 8173.691 ms | bounded visualisation |
| B7 | 0.061171875 Hz | 16347.382 ms | bounded heavy build/package |


| Obszar | Zakres | Rola |
| --- | --- | --- |
| superblock | 0x0000–0x01ff | geometry + CRC32C |
| HEAD_A | 0x0200–0x03ff | odd generation publication |
| HEAD_B | 0x0400–0x05ff | even generation publication |
| reserved | 0x0600–0x0fff | bounded reserved space |
| generation log | 0x1000–0xffff | 15 × 4096 B immutable extents |


| Profil | Cel | Authority / weryfikacja |
| --- | --- | --- |
| PAUX-EXACT | byte-exact materialization | exact identity + integrity |
| PAUX-C | lossless compression | exact decode + identity/integrity verify |
| PAUX-R | orbital/relational reconstruction | RECONSTRUCTION_ONLY + quality metrics |


| Najważniejsza zmiana po Stage 3 Pamięć przestaje być zbiorem niezależnych pasm. Staje się grafem relacji harmonicznych, w którym krawędź ma exact ratio m:n, coherence R oraz phase offset Δ. |
| --- |


| Kanał | Znaczenie | Tryb użycia |
| --- | --- | --- |
| phi | 36 faz oscylatorów QHTRI | DIRECT_PHASE, read-only |
| omega | 36 naturalnych częstotliwości kątowych | DIRECT_OMEGA, read-only |
| tick | autonomous evolution counter | window ordering / freshness |
| tau (runtime) | 36 per-oscillator sync coupling strengths | osobny namespace od τ_ij |


| Dozwolone ścieżki writer principal |
| --- |
| active_head |
| orchestration_status.json |
| surface_A.json |
| surface_B.json |


| Jedno zdanie o całym BioOS Budujemy system, który od pierwszej instrukcji po resecie aż do decyzji o kolejnym działaniu utrzymuje jawny związek pomiędzy stanem, relacjami, czasem, uprawnieniem, efektem i pamięcią. |
| --- |


| Warstwa | Wybrane evidence | Aktualny status |
| --- | --- | --- |
| PNROM/bootstrap | 64 KiB ROM, reset offset, relocations=0 | HOST BUILD PASS |
| PNR/PNMap | content identity + x86 page-walk binding | PHYSICAL BINDING IMPLEMENTED |
| Scheduler | 1,048,576 tick classifications | PASS |
| PNClock | 224,576 host checks; exact rational mapping | PASS / exact source gate |
| PNStore | 118/118 host block-image conformance | PASS |
| PAUX v0.2.4–0.2.5 | exact round-trip + 24/24 codec checks | PASS |
| Harmonic memory v0.2.6 | 19+20+18+24+21 | 102/102 PASS |
| Torsion memory v0.2.7 | dynamics + orchestration + optimization + telemetry + writer | 120/120 PASS |
| Live writer installation | owner-side runtime realization | PENDING_RUNTIME_INTEGRATION |
| Runtime emulation bootstrap | full PNROM→PNCore execution | PENDING |
| Physical-machine boot | hardware execution | PENDING |


| Obszar | Artefakt |
| --- | --- |
| Bootstrap | arch/x86_64/BOOTSTRAP_CONTRACT.md |
| PNVector | spec/PNVECTOR_HANDOFF_V0_1.md |
| PNR | spec/PN_REALIZATION_V0_1.md |
| PNMap | spec/PNMAP_X86_PAGEWALK_REALIZATION_V0_1.md |
| Scheduler | spec/PN_HARMONIC_SCHEDULER_V0_1.md |
| PNClock | spec/PN_CLOCK_TSC_DEADLINE_V0_1.md |
| PNStore | spec/PNSTORE_MEDIA_REALIZATION_V0_1.md |
| AUX binding | spec/PNSTORE_AUX_BINDING_V0_1.md |
| PAUX | spec/PAUX_CODEC_PROFILES_V0_1.md |
| Harmonic memory | spec/PAUX_HARMONIC_ORBITAL_MEMORY_V0_1.md |
| Resonance | spec/PAUX_HARMONIC_RESONANCE_GRAPH_V0_1.md |
| Torsion surface | spec/NOEMA_TORSION_MEMORY_SURFACE_V0_1.md |
| Kuramoto | spec/QHTRI_KURAMOTO_TORSION_FLOW_V0_1.md |
| Live telemetry | spec/NOEMA_QHTRI_DIRECT_TELEMETRY_BIND_V0_1.md |
| Orchestration | spec/NOEMA_MEMORY_ORCHESTRATION_BIND_V0_1.md |
| Writer principal | spec/NOEMA_TORSION_SURFACE_WRITER_PRINCIPAL_V0_1.md |


| Termin | Znaczenie |
| --- | --- |
| PNROM | minimalna resetowa realizacja firmware/boot dla PNCore |
| PNCore | native core systemu po bootstrap admission |
| PNV | native program/witness surface |
| PNR | architecture-specific physical realization binding |
| PNVector Handoff | dokładny 36D firmware→PNCore state carrier |
| PNMap | relacyjny resolver/mapowanie związane z fizycznym page walk |
| PNObject | generation-bound relacyjny obiekt systemu |
| PNFS | widok relacyjnej przestrzeni obiektów |
| PNCAP | exact capability admission |
| AUX | granica efektów i adapter dispatch |
| PNStore | append-only generation persistence z dual HEAD |
| PAUX | persistent AUX carrier |
| B-band | scheduler admission lane |
| H-band | harmonic memory band |
| Resonance edge | relacja m:n + coherence + phase offset |
| τ_ij | torsion-memory edge transport |
| QHTRI | live oscillator dynamics wykorzystywana przez torsion memory |
| Memory epoch | atomowo publikowana generacja working memory surface |
| Recall basin | stabilny klaster pamięci używany do rankingu candidate |
| GREMLIN | bounded candidate generator i structural critic |


| Obecny obraz PNCore-BioOS Od resetu do recall system konsekwentnie buduje relację: SOURCE → IDENTITY → ADMISSION → TRANSITION → STATE → EVIDENCE. v0.2.7 rozszerza ten sam wzorzec na pamięć: SOURCE TELEMETRY → HARMONIC RELATION → TORSION SURFACE → RECALL CANDIDATE → PNCAP → ACTION. |
| --- |
