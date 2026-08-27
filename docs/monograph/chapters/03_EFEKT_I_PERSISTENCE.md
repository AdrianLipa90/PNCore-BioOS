CZĘŚĆ III — EFEKT I PERSISTENCE
## 10. AUX jako granica fizycznego działania
AUX jest w BioOS granicą efektów. Wysokopoziomowy PNStore, memory surface czy orchestrator nie powinny realizować urządzeń bezpośrednio. Kandydat operacji przechodzi przez capability, AUX admission i dopiero adapter realizuje fizyczne przejście. Taki układ pozwala zachować jedną ścieżkę audytu dla storage, restore i późniejszych działań orkiestratora.
REQUEST  →  PNCAP  →  AUX admission  →  device adapter  →  physical transition  →  completion evidence
W persistence oznacza to, że PNStore odpowiada za generation semantics, ale fizyczne READ_EXTENT, APPEND_EXTENT, DURABLE_BARRIER i HEAD_SLOT_WRITE są capabilities backendu za AUX. Ta separacja jest kluczowa: media format może być byte-exact i deterministyczny, a urządzenie może zmieniać się niezależnie za adapterem.
Ta sama zasada zamyka pętlę pamięci. Resonant recall może wskazać candidate, orchestrator może przygotować action, ale efekt fizyczny następuje dopiero po PNCAP i AUX. W ten sposób pamięć i działanie są połączone, lecz nadal przechodzą przez jawne authority.
## 11. PNStore — pokoleniowa, append-only persistence
PNStore Media Realization v0.1 definiuje dokładny 64 KiB bounded block image z superblockiem, dwoma HEAD slots i 15 immutable generation extents po 4096 bajtów. Każda generacja ma parent_generation, transition_id, object_digest, payload i commit seal z CRC32C. Prepared extent staje się current dopiero po opublikowaniu poprawnego HEAD.

Durability order jest rozdzielony na dwa etapy: prepare immutable extent → DURABLE_BARRIER → publish alternating HEAD → DURABLE_BARRIER. Dzięki temu awaria pomiędzy przygotowaniem danych a publikacją HEAD pozostawia nieodwołany tail, który recovery może pominąć. Torn newer HEAD lub corrupt newer extent prowadzą do poprzedniej poprawnej generacji.
Exactly-once transition identity skanuje bounded committed history. Replay znanego transition_id zwraca pierwotną generację bez mutacji. To ważne dla przyszłej orkiestracji: powtórzenie żądania nie musi oznaczać powtórzenia efektu persistence.
Host conformance dla PNStore obejmował 118/118 checks na fsync-backed block image. Device-specific NVMe/AHCI backend jest osobną bramką realizacyjną, a semantics PNStore pozostają stałe.
## 12. PAUX — persistent AUX i trzy profile pamięci
PAUX powstał jako persistent AUX carrier, który przenosi canonical PNV_STATE_OBJECT.object_id, lineage, integrity i evidence przez ścieżkę persistence. Admitted route ma postać PNV_STATE_OBJECT → PAUX → PNCAP exact persistence grant → AUX persistence request → PNStore generation transition → AUX physical-media adapter → completion evidence.
PNV_STATE_OBJECT  →  *.paux  →  PNCAP  →  AUX  →  PNStore generation  →  durable barrier  →  HEAD  →  evidence
W v0.2.5 PAUX został rozdzielony na trzy profile. PAUX-EXACT zachowuje dokładny stan. PAUX-C stosuje odwracalne transformacje, między innymi KEYSTATE, REF, RUN i DELTA_XOR64, po czym wraca do exact recovery dopiero po weryfikacji identity i integrity. PAUX-R ma osobny RECONSTRUCTION_ID i tworzy reconstruction evidence.

Pierwszy live exact round-trip odtworzył dwa kanały T36 po 288 bajtów byte-identically w shadow surface. PAUX-C na korzystnym 64-frame static fixture użył KEYSTATE+REF+RUN i zrekonstruował wszystkie ramki. Te wyniki stały się punktem wyjścia do pytania: skoro stan ma fazę i historię, czy persistence może wykorzystywać jego geometrię, a nie tylko powtarzalność bajtów?
