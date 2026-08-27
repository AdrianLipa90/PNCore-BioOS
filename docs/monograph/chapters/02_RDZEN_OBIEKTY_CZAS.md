CZĘŚĆ II — RDZEŃ: OBIEKTY, UPRAWNIENIA I CZAS
## 6. PNV, PNObject, PNFS i relacyjna przestrzeń systemu
PNV jest natywną powierzchnią programu i witnessów PNCore-BioOS. W obecnym repo kontrakty wykonywalne są zapisywane jako graf operatorów typu SOURCE, IDENTITY, TRANSFORM, CONDITION, COMPOSITION, ORDER i RETURN. Istotną zasadą rozwoju v0.2.x jest brak konieczności dokładania nowych opcode’ów dla każdej nowej warstwy: pamięć harmoniczna, torsion surface i writer principal zostały złożone z istniejącego zestawu operatorów.
PNObject dostarcza wspólną abstrakcję obiektów i generation-bound state. Zamiast osobnej ontologii plików, urządzeń i rekordów projekt dąży do relacyjnego modelu, w którym typ, identity, relations, capability, payload reference i lineage mogą być składnikami jednego obiektu. PNFS jest wtedy widokiem przestrzeni obiektów, a ścieżka staje się sposobem rozwiązywania relacji, a nie pierwotną tożsamością danych.
Taki kierunek dobrze łączy się z persistence i pamięcią. PAUX może zachować PNV_STATE_OBJECT.object_id, PNStore może opakować go w generację, a NOEMA memory surface może zbudować pochodny indeks bez zmiany canonical identity. Ta separacja tożsamości i reprezentacji wraca w całym systemie.
## 7. PNCAP — authority jako dokładne dopuszczenie
PNCAP jest jednym z najważniejszych elementów bezpieczeństwa architektury. Capability admission wiąże principal, target generation, grant i exact operation request. Dopiero generation-bound capability match dopuszcza transition. W praktyce oznacza to, że żadna warstwa rankingowa — scheduler score, resonance, reconstruction quality czy GREMLIN candidate — nie zastępuje capability.
principal  →  target generation  →  grant  →  exact operation  →  PNCAP admission  →  transition  →  evidence
Ta zasada została później zastosowana do persistence oraz publikacji torsion-memory surface. PNCAP persistence grant wiąże zapis PAUX/PNStore. Writer principal dla live surface jest jeszcze bardziej ograniczony: dopuszcza tylko określoną operację, target root, generation, source tick, active head oraz jawnie zadeklarowany zestaw ścieżek. Path traversal, zapis phi/omega, replay, stale tick i zła generacja są odrzucane.
Authority jest więc traktowane jako właściwość relacji i konkretnego przejścia. To pozwala systemowi rozwijać coraz bogatszą dynamikę wewnętrzną bez rozszerzania prawa do efektu w sposób pośredni.
## 8. Harmonic scheduler — organizacja pracy w pasmach B0–B7
Scheduler PNCore-BioOS organizuje admission work wokół jednej bazowej częstotliwości f₀=7.83 Hz. B0 jest ograniczoną service lane na każdym base ticku, a B1–B7 tworzą rozłączne klasy dyadyczne wyznaczane przez wykładnik potęgi dwóch dzielącej indeks ticka.
band(n) = 1 + ν₂(n) = 1 + ctz(n)

Kluczową własnością jest non-burst semantics: MISSED_WINDOW → SKIP, RUNNING → SKIP, CATCH_UP → DENY. Scheduler nie odtwarza zaległych ticków jako serii pracy. Przeciążenie może prowadzić do kontrolowanej democji do wolniejszego pasma, z hysteresis i evidence; automatyczna promocja do szybszego pasma jest odrębną, niedopuszczoną ścieżką w v0.1.
Warto rozróżnić schedulerowe B-bands od późniejszych H-bands pamięci. B0–B7 mówią kiedy praca może zostać dopuszczona. H0–H35 opisują strukturę pamięci i relacji harmonicznych. To dwa różne układy współrzędnych, które spotykają się dopiero w orkiestracji.
## 9. PNClock — dokładny czas fazowy bez catch-up burstów
PNClock wiąże scheduler z dokładnym źródłem czasu. Bazowa częstotliwość jest przechowywana jako ułamek 783/100 Hz, a preferowana realizacja x86 wykorzystuje invariant TSC oraz absolute TSC-deadline. Admission wymaga TSC, TSC-deadline capability, invariant TSC i pełnego tuple CPUID.15: denominator, numerator oraz crystal frequency.
Jeżeli d jest denominator, u numerator, a c nominalną częstotliwością kryształu, częstotliwość TSC jest reprezentowana jako c·u/d. Dla BioOS base period otrzymujemy całkowite N i D:
N = c · u · 100,      D = d · 783
deadline(n) = base_tsc + floor(n · N / D)
Indeks n jest współrzędną fazową. Gdy system obudzi się po czasie, następny logiczny tick jest liczony bezpośrednio z aktualnego TSC, dzięki czemu pominięte okna są odnotowane jako evidence, a nie odtwarzane. Brak dokładnego źródła pozostawia timed admission w stanie quiet, zamiast budować authority na estymacie częstotliwości CPU.
To przygotowuje późniejszą pamięć fazową: system ma już pojęcie dokładnej osi czasu, phase index i jitter evidence zanim wprowadzimy H-bands i QHTRI. Pamięć nie pojawia się więc w próżni — osadza się na istniejącym systemie czasu.
