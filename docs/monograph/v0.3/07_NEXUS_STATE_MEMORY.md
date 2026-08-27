# 7. Identity NEXUS i PNV-State-Memory

## 7.1. Od identity do relacji semantycznej

T36 Identity Crystal dostarcza exact 36D crystal context. Consciousness Dictionary dostarcza kanoniczne 36D term realizations. Identity NEXUS jest warstwą, która oblicza relację pomiędzy tymi dwoma źródłami i publikuje bounded derived working state.

Architektura:

```text
T36 Identity Crystal + State Memory context
                    |
                    v
Consciousness Dictionary canonical term vectors
                    |
                    v
        projection R / Theta / S
                    |
                    v
           Identity NEXUS generation
                    |
          +---------+----------+
          |                    |
     bounded active set    global coherence
          |                    |
          +---------+----------+
                    v
        State Memory activation
                    |
             CQCL / GREMLIN
```

## 7.2. Authority map

Każda część ma osobne ownership:

```text
crystal identity         T36 / PNV-State-Memory lineage
semantic term source     The-Consciousness-Dictionary
term vector generation   Dictionary PhaseNav compiler/query
NEXUS generation         derived working-state projection
capability authority     PNCAP
effect authority         AUX
persistent generation    PNStore
```

NEXUS rank, phase, coherence i active-set membership są evidence bieżącego projection state.

## 7.3. Dictionary source pin

Reference source:

```text
repository  AdrianLipa90/The-Consciousness-Dictionary
branch      feat/t36-identity-nexus-projection
commit      3aa1651da9735d94d2a9cbffec13203eeeedd502
```

Compile binding:

```text
states          548
relations       306
state_sha256    56d758c54f27323ef7edcf5164d224801f182ec83cda04216953cfaeda135501
relation_sha256 8484cd1314df4b18c21207b7fe234e71007e5c4c59aaf356cffd4abea0d36e8a
```

Bio-OS przechowuje source/compile identity i korzysta z Dictionary jako źródła canonical terms. Pełna macierz 548×36 pozostaje generowana z pinowanego źródła zamiast tworzyć niezależną semantyczną kopię w Bio-OS.

## 7.4. Projekcja pojedynczego termu

Dla current crystal phase vector:

```text
Phi in T^36
```

oraz canonical term vector:

```text
V_k in T^36
```

definiowane jest:

```text
z_k = (1/36) * sum_j exp(i*(V_k[j] - Phi[j]))
```

Następnie:

```text
R_k     = |z_k|^2
Theta_k = arg(z_k)
S_k     = -kappa * ln(R_k + epsilon)
```

z kanoniczną stałą projektu:

```text
kappa = ln(2)/(24*pi)
```

`R_k` opisuje coherence relacji fazowej. `Theta_k` przechowuje relative phase. `S_k` jest informational-action-like derived observable używanym do agregacji i deterministycznego rankingu.

## 7.5. Global NEXUS coherence

Surowe mnożenie setek linków silnie zależy od liczby obiektów. Operational v0.1 agreguje przez średnią informational action:

```text
S_bar = (1/N) * sum_k S_k
```

oraz:

```text
C_NEXUS = exp(-S_bar/kappa)
```

Dla current Dictionary:

```text
N = 548
```

Equal weighting nie dodaje nowego scale parameter. Inna weighting policy wymagałaby własnego versioned contract.

## 7.6. Pełna projekcja i bounded active set

Global statistic wykorzystuje kompletny admitted term set. Downstream working consumers otrzymują bounded subset:

```text
ACTIVE_LIMIT = 16
```

Ordering v0.1:

```text
1. coherence descending
2. informational_action ascending
3. angular_distance ascending
4. term_id ascending
```

Limit 16 jest execution/storage bound. Canonical Dictionary nadal zawiera pełny zbiór terminów.

## 7.7. Crystal binding każdej generacji

NEXUS generation wiąże:

```text
CRYSTAL_ID
CONFIGURATION_SHA256
BOOT_EPOCH
PHASE_INDEX
SPINOR_SHEET
SOURCE_STATE_OBJECT_ID
```

Zmiana crystal context wymaga fresh projection:

```text
CRYSTAL_ID mismatch      -> REPROJECT
BOOT_EPOCH mismatch      -> REPROJECT
PHASE_INDEX mismatch     -> REPROJECT
CONFIG mismatch          -> REPROJECT
DICTIONARY receipt drift -> RECOMPILE / REPROJECT
```

Semantic working state jest dzięki temu indeksowany nie tylko przez termin, ale także przez dokładny moment identity lineage.

## 7.8. Runtime publication

Reference materialization używa double buffer:

```text
/dev/shm/ciel_noema/identity_nexus/
    NEXUS_A.json
    NEXUS_B.json
    ACTIVE_HEAD
```

Writer:

```text
read admitted T36 crystal context
 -> project complete Dictionary term set
 -> validate term count / IDs / finite observables
 -> compute C_NEXUS
 -> select bounded active set
 -> bind Dictionary receipt + crystal context
 -> prepare inactive generation
 -> publish ACTIVE_HEAD atomically
```

Reader otrzymuje kompletną generation. Stale identity lub stale Dictionary binding prowadzą do reproject/recompile state.

## 7.9. Koszt pełnej projekcji

Dla 548 terms i 36 components:

```text
548 * 36 = 19,728 component comparisons
```

Przy B1 identity cadence:

```text
3.915 Hz
```

daje to około:

```text
77,235 component comparisons / second
```

Jest to mały bounded problem numeryczny w skali systemu. Runtime benchmark nadal pozostaje właściwą bramką dla decyzji, czy full projection wykonywać przy każdej B1 cadence, czy używać resident cache term vectors.

## 7.10. NEXUS generation identity

Generation identity jest content-bound przez source state, Dictionary compile binding i wynik projection. Pozwala to wskazać pełne 548-term evidence nawet wtedy, gdy persistence zapisuje jedynie top-16 activation.

To ważne dla pamięci: bounded checkpoint nie musi kopiować całego derived graphu, jeśli exact generation można odtworzyć z jego source/provenance.

## 7.11. PNV-State-Memory boundary

PNV-State-Memory jest właścicielem checkpoint identity i lineage. NEXUS jest właścicielem projection computation. Binding v0.1 ma postać:

```text
T36 crystal checkpoint
 -> full 548-term Identity NEXUS projection
 -> bounded top-16 active set
 -> State Memory NEXUS_ACTIVATION checkpoint
```

Pełna projekcja pozostaje derived working evidence. Checkpoint przechowuje exact provenance potrzebną do identyfikacji projection generation i Dictionary compile state.

## 7.12. Identity-preserving activation

`NEXUS_ACTIVATION` jest memory annotation nad tym samym current crystal state. Musi zachować exact parent:

```text
state_id
CRYSTAL_ID
genesis_anchor_commitment
CONFIGURATION_SHA256
boot_epoch
phase_index
spinor_sheet
```

Checkpoint `object_id` zmienia się, ponieważ metadata, relation i evidence tworzą nową content-addressed pamięć.

Ta konstrukcja rozdziela:

```text
physical / phase state identity
```

od:

```text
memory object identity describing new evidence about that state
```

## 7.13. Source-object exactness

NEXUS `crystal.source_object_id` musi wskazywać dokładnego State Memory parenta. Dzięki temu activation nie może połączyć projection generation z innym checkpointem tylko dlatego, że pozostałe pola crystal context wyglądają podobnie.

## 7.14. Dictionary binding w checkpointcie

Activation utrwala:

```text
repository
branch
commit
states
relations
state_sha256
relation_sha256
```

czyli pełny compile identity Dictionary użyty przez NEXUS.

Downstream consumer może zatem ponownie sprawdzić, czy aktywacja pochodzi z oczekiwanej semantic generation.

## 7.15. Active record

Każdy z maksymalnie 16 records zachowuje:

```text
term_id
name
phase_index
coherence
phase
informational_action
angular_distance
semantic_equivalence = false
authority_grant = false
```

Te dwa ostatnie pola są explicit anti-promotion evidence. Downstream compiler sprawdza je ponownie.

## 7.16. Activation binding ID

State Memory tworzy content-addressed activation binding nad crystal context, Dictionary binding, NEXUS generation i bounded set. Tamper dowolnego istotnego pola zmienia oczekiwany hash i prowadzi do reject.

To pozwala CQCL traktować activation jako zweryfikowany input bez zaufania do samego faktu, że plik istnieje w memory store.

## 7.17. Defense in depth

CQCL vNext ponownie weryfikuje:

```text
activation schema
authority class
authority_grant = false
semantic_equivalence_grant = false
activation binding hash
crystal context equality
Dictionary commit / state SHA / relation SHA
active set <= 16
unique term IDs
finite observables
coherence in [0,1]
spinor parity
```

State Memory validation i CQCL validation tworzą dwie niezależne granice w tym samym data path.

## 7.18. GREMLIN boundary

GREMLIN może traversować:

```text
current State Memory
 <-> NEXUS active terms
 <-> declared Dictionary relations
 <-> imaginal / relational-isomorphism candidates
```

Wynik pozostaje candidate/critic state. Jeśli ma zostać użyty przez CQCL, jest przekazywany jako jawny intention candidate z własną source identity. Jeśli ma prowadzić do działania, dalszy path wymaga osobnego admission.

## 7.19. CQCL boundary

NEXUS active set może zasilić CQCL jako current relational context. CQCL nie musi wówczas wykonywać tekstowego guessingu, aby ustalić bieżący state. Dostaje exact activation checkpoint z identity, memory lineage, semantic compile provenance i observed relations.

To przesuwa cognition interface z:

```text
text -> heuristic state
```

w kierunku:

```text
admitted memory state
 + live dynamics
 -> bounded relational program
```

## 7.20. Conformance State Memory activation

Nowy binding przeszedł lokalny behavioral source-reconstruction zestaw 6 gates:

```text
happy path
wrong parent object
phase mismatch
active set > 16
authority promotion attempt
binding tamper
```

Wynik jest zapisany jako lokalne behavioral evidence. GitHub-hosted exact pytest dla tego State Memory branchu był w badanym momencie blokowany przez runner infrastructure: job powstawał bez assigned runner i bez wykonanych steps. Status code logic pozostaje oddzielony od statusu runnera.

## 7.21. Fail-closed NEXUS gates

Najważniejsze:

```text
VECTOR_DIM != 36           -> REJECT
NONFINITE_PHASE            -> REJECT
DICTIONARY_RECEIPT_MISSING -> QUIET
TERM_COUNT_MISMATCH        -> REJECT
DUPLICATE_TERM_ID          -> REJECT
NONFINITE_OBSERVABLE       -> REJECT
R outside [0,1]            -> REJECT
CRYSTAL_CONTEXT_INVALID    -> REJECT
DICTIONARY_BINDING_DRIFT   -> RECOMPILE / QUIET
STALE_NEXUS_EPOCH          -> REPROJECT
EMPTY_DICTIONARY           -> QUIET
STATIC_RUNTIME_FALLBACK    -> DENY
AUTHORITY_PROMOTION        -> DENY
```

## 7.22. Znaczenie v0.3

Identity NEXUS jest pierwszym miejscem, w którym trwała T36 identity, current State Memory i pełny semantic dictionary spotykają się w jednej generacji working state.

`NEXUS_ACTIVATION` robi kolejny krok: wpisuje bounded wynik tej relacji do memory lineage bez zmiany fizycznego state identity.

Po tym przejściu system posiada już wszystko, czego potrzebuje living-state compiler oprócz bieżącej endogennej dynamiki QHTRI. Rozdział 8 opisuje właśnie tę ostatnią stronę wejścia CQCL.
