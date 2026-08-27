PNCore-BioOS
OD RESET VECTORA DO TORSYJNEJ PAMIĘCI
Architektura, czas, persistence, pamięć harmoniczna i orkiestracja QHTRI
Monografia techniczna v0.2.7
RESET @ 0xFFFF0  →  PNROM  →  PNCore  →  PNClock  →  AUX/PNStore  →  PAUX  →  H-bands  →  NOEMA torsion memory  →  QHTRI/Kuramoto  →  Orchestration
Adrian Lipa
PNCore-BioOS • 26 sierpnia 2026
Stan źródłowy monografii: feature commit e8134c7329799b593da53308eebc43a21e00050f

## Jak czytać tę monografię
Ta wersja opisuje PNCore-BioOS jako jeden system od pierwszej instrukcji po reset procesora aż do aktualnej warstwy pamięci i orkiestracji. Pamięć torsyjna stanowi końcową część opowieści, a nie jej punkt startowy. Wcześniejsze rozdziały pokazują, skąd bierze się authority, czas, adresowanie, persistence i fizyczna ścieżka efektów, bez których pamięć robocza byłaby tylko odizolowanym algorytmem.
Tekst ma dwa poziomy. Pierwszy jest architektoniczny: wyjaśnia po co istnieje dana warstwa i jakie miejsce zajmuje w systemie. Drugi jest formalny: podaje równania, dokładne kontrakty i wyniki testów. Statusy typu PASS, PENDING, CHYBA i RECONSTRUCTION_ONLY są traktowane jako część provenance, czyli zapisu tego, co dokładnie zostało zademonstrowane na danym etapie.

## Spis treści
CZĘŚĆ I — Narodziny systemu: reset, PNROM i wejście do long mode
1. Założenie BioOS: system ma opisywać własny stan
2. Reset vector i PNROM — pierwszy fizyczny most
3. PNVector Handoff — 36D stan przekazywany do PNCore
4. PN Realization i PNMap — semantyka związana z fizycznością
5. Sigma₀ i przejście do PNCore
CZĘŚĆ II — Rdzeń: obiekty, mapowanie, uprawnienia i czas
6. PNV, PNObject, PNFS i relacyjna przestrzeń systemu
7. PNCAP — authority jako dokładne dopuszczenie
8. Harmonic scheduler — organizacja pracy w pasmach B0–B7
9. PNClock — dokładny czas fazowy bez catch-up burstów
CZĘŚĆ III — Efekt i persistence
10. AUX jako granica fizycznego działania
11. PNStore — pokoleniowa, append-only persistence
12. PAUX — persistent AUX i trzy profile pamięci
CZĘŚĆ IV — Od persistence do geometrii pamięci
13. H-bands i geometria proporcji orbit
14. Estymacja harmoniczna i graf rezonansów m:n
15. PAUX-C i PAUX-R — exact oraz rekonstrukcja orbitalna
CZĘŚĆ V — Żywa pamięć
16. NOEMA Torsion Memory Surface
17. QHTRI/Kuramoto na polu torsyjnym pamięci
18. Endogenna telemetria phi, omega i tick
19. Resonant recall, orkiestracja i stale-epoch protection
20. Writer principal i bezpieczna publikacja generacji
CZĘŚĆ VI — Stan obecny i kierunek dalszej budowy
21. Optymalizacja sparse i coupling κ
22. Pełna ścieżka BioOS od resetu do działania
23. Macierz dowodów i aktualne granice realizacji
24. Następne bramki implementacyjne
Aneks A — Kluczowe równania
Aneks B — Mapa artefaktów repozytorium
Aneks C — Słownik pojęć
