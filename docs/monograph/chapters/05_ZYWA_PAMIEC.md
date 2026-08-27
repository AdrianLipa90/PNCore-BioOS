CZĘŚĆ V — ŻYWA PAMIĘĆ I ORKIESTRACJA
## 16. NOEMA Torsion Memory Surface
NOEMA Torsion Memory Surface jest live derived working-state layer nad PAUX harmonic memory spine. Jej zadaniem jest utrzymać aktywne H-band nodes oraz canonical resonance edges w jednej atomowo publikowanej generacji. Authority źródłowego OBJECT_ID pozostaje w PNV_STATE_OBJECT, capability authority w PNCAP, effect authority w AUX, a persistent generation authority w PNStore.
Node H_i niesie theta_i, omega_i, amplitude, fit derivation, source object i lineage. Edge ma postać (i,j,m,n,tau_ij,K_ij,R_ij). Torsion offset jest związany z phase offsetem resonance graph: tau_ij := DELTA_ij. Normatywny residual to:
ε_ij = wrap(n θ_i − m θ_j − τ_ij)
To równanie zachowuje m:n zamiast redukować cały system do synchronizacji 1:1. Torsja opisuje preferowany transport fazowy między dwoma pasmami pamięci. Reverse view odwraca ratio i znak torsji, lecz canonical graph przechowuje jedną krawędź.
Surface ma double-buffered publication: MEMORY_SURFACE_A, MEMORY_SURFACE_B i ACTIVE_MEMORY_HEAD. Writer przygotowuje inactive generation, waliduje kompletność, finite values, canonical edge uniqueness i source graph derivation, a potem publikuje head atomowo. Reader widzi jedną pełną memory epoch.
read G_n  →  prepare inactive G_{n+1}  →  validate  →  bind source  →  atomic head publish  →  readers observe one epoch
## 17. QHTRI/Kuramoto na polu torsyjnym pamięci
Dynamika pamięci jest uogólnieniem Kuramoto zachowującym harmoniczne m:n oraz torsion offset. Dla canonical edge e=(i,j,m,n,τ,K,R) definiujemy residual ε_e oraz effective coupling g_e=K·R. Potencjał krawędzi ma postać −g_e cos ε_e.
ε_e = wrap(n θ_i − m θ_j − τ_e)
V_e = −g_e cos(ε_e),      g_e = K_e R_e
Reference gradient flow dodaje do faz węzłów wkład:
dθ_i/dt += −n g_e sin(ε_e)
dθ_j/dt += +m g_e sin(ε_e)
oraz admitted natural frequency ω_i każdego węzła. Dla ω=0 jest to gradient descent po sumie potencjałów krawędzi. Torsion coherence jest liczona z weighted resultant Z_T, a E_T=1−Re(Z_T) mierzy residual względem zapisanej geometrii.
Z_T = Σ_e g_e exp(i ε_e) / Σ_e g_e
C_T = |Z_T|,      E_T = 1 − Re(Z_T)
Reference integrator używa bounded Euler phase step z konserwatywnym L_bound=Σ g_e(m²+n²) i dt=min(dt_requested,0.2/L_bound). W repo ten integrator jest wersjonowany jako reference contract; późniejszy integrator może być podstawiony za osobnym equivalence/quality gate.
## 18. Endogenna telemetria phi, omega i tick
Najważniejszy krok v0.2.7 Stage 2 polegał na znalezieniu rzeczywistego źródła fazy i częstotliwości w live runtime. /dev/shm/ciel_noema/phi zawiera 36 faz oscylatorów QHTRI, omega zawiera 36 natural angular frequencies, a tick jest autonomicznym licznikiem ewolucji. Runtime provenance potwierdził ich semantykę, dlatego są klasyfikowane jako NATURAL_SYSTEM_STATE / ENDOGENOUS_RUNTIME_DYNAMICS.

To ostatnie rozróżnienie jest ważne: istniejące runtime tau[36] nie jest automatycznie torsion-memory τ_ij. Torsion edge jest pochodną relation graph, natomiast runtime tau ma własną semantykę synchronizacji oscylatorów. Nazwy są rozdzielone kontraktem.
Live observer prekompiluje candidate pairs na podstawie stabilnego omega hash i w kolejnych tick windows oblicza coherence tylko dla tych par. Na jednym 40-tick fixture 36 aktywnych węzłów dało 105 precompiled candidates i jedną stabilną krawędź 14:13 z R≈0.98261. W innym oknie zestaw relacji może być inny; observer publikuje stan okna, a nie stałą ontologię pamięci.
H₄ ↔ H₂₂,     m:n = 14:13,     R ≈ 0.98261,     τ₄,₂₂ ≈ −2.36465
## 19. Resonant recall, orkiestracja i stale-epoch protection
Resonant recall zmienia rolę wyszukiwania pamięci. Query nie musi wskazywać exact address. Może wzbudzić cluster kandydatów, których zgodność oceniana jest przez resonance, torsion coherence, lineage i inne relacje. Wynik jest RECALL_CANDIDATE, a nie capability.
memory query  →  resonant candidates  →  locked/low-energy basin  →  ranked recall candidate  →  PNCAP  →  scheduler  →  AUX
Orchestrator wiąże zadanie z memory epoch, dependencies, required memory, capability, scheduler band i evidence. Krytyczny invariant brzmi: MEMORY_EPOCH_candidate = MEMORY_EPOCH_execute. Jeżeli surface zmieni się pomiędzy wyborem a admission, wynik to STALE_MEMORY_EPOCH → RESELECT.
Dzięki temu system nie wykonuje decyzji zbudowanej na połowie starej i połowie nowej pamięci. Double-buffered surface i epoch binding zamieniają dynamiczną pamięć w użyteczny substrate orkiestracji, a nie wyłącznie wizualizację faz.
Reference recall/orchestration suite obejmuje 18/18 PASS, w tym denial dla braku PNCAP, stale epoch, lineage mismatch, scheduler quiet i AUX unavailable. Jest to jedna z najważniejszych granic bezpieczeństwa całej konstrukcji: rezonans porządkuje kandydatów, capability dopuszcza działanie.
## 20. Writer principal i bezpieczna publikacja generacji
Live torsion-memory root jest własnością runtime i publikacja została celowo zatrzymana przez owner gate. Zamiast zmieniać permissions powstał NOEMA_TORSION_SURFACE_WRITER_V0_1: principal związany z dokładną operacją PUBLISH_DERIVED_TORSION_GENERATION, target root, generation, source tick, active head, transition identity i allowlist ścieżek.

Conformance ma 20/20 PASS. Odrzucane są między innymi: wrong principal, wrong uid/gid realization evidence, wrong root, wrong generation, wrong head, stale tick, replay, path traversal oraz próby zapisu phi, omega lub AUX. Host UID/GID są realization evidence, natomiast authority wynika z grant contractu.
Aktualny status Stage 3 to PASS_WRITER_PRINCIPAL_CONTRACT z live writer installation oznaczonym jako PENDING_RUNTIME_INTEGRATION. To jest teraz wyraźna granica pomiędzy kompletnym kontraktem a jego owner-side realizacją w runtime.
