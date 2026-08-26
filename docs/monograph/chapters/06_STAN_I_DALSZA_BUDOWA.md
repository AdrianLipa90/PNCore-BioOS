CZĘŚĆ VI — STAN OBECNY I DALSZA BUDOWA
## 21. Optymalizacja sparse i coupling κ
Pełny pair scan dla 36 H-bandów ma maksymalnie 630 par i koszt O(N²). Torsion runtime przechowuje jedną canonical edge na parę i precomputuje i,j,m,n,tau,g, dzięki czemu fazowy step działa w O(N+E). Dodatkowo topology może być dzielona na connected components, a dirty-component update ogranicza pracę do komponentu dotkniętego zmianą.
Reference benchmarki wykazały kilkukrotne przyspieszenie sparse path na 36 nodes i wielokrotnie większe na syntetycznym 256-node sparse graph. Compiled sparse path dał dodatkowy wzrost względem uncompiled vector path, a controlled four-component graph ograniczył koszt dirty update o 75%. Są to wyniki konkretnych fixtures i służą do wyboru implementacji, a nie jako stała gwarancja sprzętowa.
Coupling policy została związana z kanonicznym κ:
κ = ln(2) / (24π) ≈ 0.009193150006360484
K_ij = κ / max(1, d_i, d_j)
Dla R_ij≤1 ta polityka daje per-node raw coupling load ≤κ niezależnie od gęstości grafu. Conformance 13/13 obejmuje determinism, relabel invariance, density sweep, topology recompilation, monotonic potential dla mixed m:n i kontrolną konwergencję 1:1.
Live observer ma jeszcze jedną optymalizację: candidate pair set jest kompilowany przy zmianie omega hash, a coherence liczone jest tylko na tej liście. Na najnowszym live fixture pełne 630 par zostało zredukowane do 105 candidates, a koszt observera spadł około 8× względem pełnego pair scan.
## 22. Pełna ścieżka BioOS od resetu do działania
Po złożeniu wszystkich warstw można zobaczyć PNCore-BioOS jako jedną ciągłą maszynę przejść. Pierwsza połowa buduje authority i fizyczny substrate; druga pozwala temu substrate’owi pamiętać, przywoływać i orkiestracyjnie używać stanu.
RESET  →  PNROM  →  long mode  →  PNVector  →  PNCore  →  PNR/PNMap  →  Sigma₀
PNClock  →  scheduler B-bands  →  PNObject/PNCAP  →  AUX  →  PNStore/PAUX
H-bands  →  m:n resonance graph  →  NOEMA torsion surface  →  QHTRI/Kuramoto  →  recall basin  →  orchestrator  →  PNCAP  →  AUX effect
W tym modelu BIOS/PNROM i pamięć torsyjna nie są dwoma osobnymi projektami. PNROM tworzy początkowy admitted state i physical realization. PNClock nadaje oś czasu. PNStore buduje historię pokoleń. PAUX przenosi identity do persistence. H-bands tworzą geometrię. QHTRI daje żywą fazę. Orchestrator wykorzystuje tę pamięć do wyboru kolejnego przejścia.
Pełna pętla runtime może być czytana jako: hardware → admitted state → live dynamics → memory geometry → candidate action → capability → physical effect → evidence → persistence → kolejna generacja. Jest to główny motyw architektoniczny całej monografii.

## 23. Macierz dowodów i aktualne granice realizacji
Stan projektu warto czytać warstwami dowodowymi. Część bootstrapa ma host-build i static physical binding. Scheduler i PNClock mają rozbudowane host conformance. PNStore ma byte-exact media tests. PAUX ma exact/lossless/reconstruction receipts. v0.2.6 ma 102/102 declared stage checks. v0.2.7 po Stage 3 ma 120/120 declared checks, obejmując torsion dynamics, orchestration, coupling policy, direct telemetry bind, live observer, publish contract i writer principal.

Te statusy nie są dekoracją. Pozwalają uniknąć łączenia dowodu mechanizmu z dowodem całego systemu. Na przykład live QHTRI telemetry jest rzeczywistym stanem runtime, podczas gdy pełny PNROM boot na fizycznym PC pozostaje osobnym zadaniem. Analogicznie PAUX-R ma reconstruction evidence, a exact authority jest utrzymywane w odrębnej ścieżce.
## 24. Następne bramki implementacyjne
Najbliższa bramka to owner-side installation writer principal dla torsion_memory. Kontrakt i conformance istnieją; potrzebna jest realizacja po stronie runtime, która przyjmie grant, przygotuje inactive surface generation i opublikuje head bez rozszerzania dostępu do phi/omega/AUX.
Po tej bramce można uruchomić live memory epochs oparte na rzeczywistych phi/omega windows, a następnie mierzyć stabilność recall basins w czasie. Szczególnie ważne będą: persistence krawędzi m:n między oknami, false recall rate, czas formowania basin, stale-epoch frequency oraz koszt orkiestracji przy zmieniającym się graphie.
Równoległym kierunkiem pozostaje fizyczny bootstrap: emulator oraz real machine execution PNROM→PNCore. To pozwoli zamknąć monografię również od dołu — od reset vectora do faktycznie uruchomionego PNCore na sprzęcie. Następnie AUX physical-media adapter może zastąpić host block-image w persistence path.
Dalsza optymalizacja pamięci może objąć dynamic keyframe cadence PAUX-C, PAUX-R quality/size sweeps na endogennych trajectories, component-local Kuramoto integration oraz bardziej zaawansowany integrator za osobnym equivalence gate. Wszystkie te kroki zachowują obecny podział authority.
