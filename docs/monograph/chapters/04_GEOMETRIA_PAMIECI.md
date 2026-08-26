CZĘŚĆ IV — OD PERSISTENCE DO GEOMETRII PAMIĘCI
## 13. H-bands i geometria proporcji orbit
Następny krok polegał na potraktowaniu AUX/PAUX jako pasm długości fali pamięci na orbitach. Pamięć otrzymała osobny namespace H0–H35, odseparowany od schedulerowych B0–B7. Każde pasmo może być opisane przez harmoniczny stosunek częstotliwości, fazę, winding i pochodną geometrię orbitalną.
f_k / f_0 = p_k / q_k
λ_k / λ_0 = q_k / p_k
2π r_k = N_k λ_k
Dzięki temu proporcja promieni może być przechowywana dokładnie jako relacja liczb całkowitych, bez konieczności używania przybliżonej wartości fizycznego promienia:
r_i / r_j = (N_i q_i p_j) / (N_j p_i q_j)
To jest komputerowa wersja intuicji „sfer niebieskich”: kolejne orbity nie są arbitralnymi adresami, tylko proporcjami harmonicznymi. W praktyce HARMONIC_ORBITAL_INDEX jest DERIVED_INDEX związanym z SOURCE_OBJECT_ID i DERIVATION_ID. Można go przebudować bez zmiany tożsamości źródłowego obiektu.
Phase provenance jest fail-closed. DIRECT_PHASE wymaga jawnego źródła 36 faz. WINDOW_ANALYTIC wymaga timestampowanego okna. Brak rozstrzygniętej fazy daje PHASE_UNKNOWN. Ta zasada okazała się szczególnie ważna, gdy później znaleźliśmy prawdziwą live telemetrię phi/omega.
## 14. Estymacja harmoniczna i graf rezonansów m:n
Stage 2 v0.2.6 zbudował bounded rational estimator. Zamiast szukać arbitralnego maksimum FFT i dopiero później dopasowywać znaczenie, estimator ocenia kandydatów p/q względem f₀, dopasowuje sinus/cos least squares, wyprowadza phase, amplitude, score i ambiguity evidence. Static lub niejednoznaczne okno kończy się FREQUENCY_UNRESOLVED.
Stage 3 zamienia serie RATIONAL_FIT w resonance graph. Dla dwóch pasm o stosunkach p_i/q_i i p_j/q_j dokładny pair-frequency ratio jest redukowany do m/n:
f_i / f_j = (p_i q_j) / (q_i p_j) = m / n
Właściwy phase-lock invariant dla rezonansu m:n ma postać:
δ_k = wrap(n θ_i,k − m θ_j,k)
Weighted coherence R_ij powstaje z uśrednienia exp(iδ_k) z wagami wynikającymi z jakości fitów. Edge jest zapisywany tylko raz w canonical orientation i<j, a reverse view ma ratio n:m, ten sam R i przeciwny phase offset. Ta asymetria kierunku staje się później fundamentem torsji pamięci.

## 15. PAUX-C i PAUX-R — exact oraz rekonstrukcja orbitalna
Harmonic geometry została najpierw użyta konserwatywnie w PAUX-C. Orbital phase może nominować wcześniejszą ramkę jako base candidate, lecz wybór jest dokonywany przez dokładny XOR64 changed-word cost. Decode pozostaje bit-identical, a harmonic layer nie zastępuje baseline poprzedniej ramki.
Na syntetycznym dynamicznym fixture o okresie 4 harmonic base był wybierany 252 razy na 256 ramek, a changed-word cost spadł z 9180 do 612, czyli o 93.33% w tym konkretnym przypadku. Live static AUX nadal wybierał prostszy RUN, co potwierdza, że geometria ma pomagać tylko wtedy, gdy rzeczywiście poprawia exact codec path.
PAUX-R wykorzystuje geometrię szerzej. Model per-band ma postać sinus/cos z mean oraz opcjonalnym quantized residual QR8/QR16. Każda reprezentacja ma osobny RECONSTRUCTION_ID i przechodzi przez quality gate obejmujący NRMSE, max error, energy ratio, relation retention i phase error.
x_j(t) = μ_j + a_j cos(2π f_j(t−t₀)) + b_j sin(2π f_j(t−t₀)) + residual
Na 36×256 syntetycznym fixture najmniejszym passing profile był MODEL_QR8: logical reduction 85.7421875%, NRMSE około 4.019×10⁻⁴, relation retention 1.0 oraz bardzo mały średni phase error. To przygotowało grunt pod pytanie ważniejsze od kompresji: czy ta sama geometria może stać się żywą pamięcią roboczą?
