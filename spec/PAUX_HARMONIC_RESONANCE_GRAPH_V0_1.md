# PAUX Harmonic Resonance Graph v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: PNCore-BioOS v0.2.6 stage 3

## Purpose

Stage 3 converts repeated admitted Stage-2 `RATIONAL_FIT` records into a bounded derived resonance graph over memory bands `H0..H35`.

The graph is evidence/index state. It does not change `PNV_STATE_OBJECT`, lineage authority, PNCAP capability authority, AUX effect authority or PNStore commit semantics.

## Input fit history

A candidate pair `(H_i,H_j)` requires synchronized Stage-2 records satisfying:

```text
STATUS RATIONAL_FIT
SHARED_WINDOW_IDS >= 4
LINEAGE_SERIES_REF EQUAL
FIT_SCORE >= 0.85 for every participating record
PHASE FINITE
RATIO_P:RATIO_Q positive and reduced
```

Unresolved Stage-2 records do not participate in resonance-edge construction.

## Exact pair commensurability

Let the Stage-2 ratios relative to `f0` be

```text
r_i = p_i / q_i
r_j = p_j / q_j
```

Then the pair-frequency ratio is reduced exactly as

```text
f_i / f_j = (p_i * q_j) / (q_i * p_j) = m / n
```

Stage-3 reference admission requires:

```text
max(m,n) <= 16
```

Higher-order candidate relations remain outside the first resonance graph.

## Phase-lock invariant

For `f_i/f_j = m/n`, the invariant combination is

```text
delta_k = wrap( n*theta_i,k - m*theta_j,k )
```

because ideal resonance obeys

```text
n*f_i - m*f_j = 0.
```

This ordering is normative for Stage 3.

## Weighted lock coherence

For synchronized window `k`, let Stage-2 fit scores be `s_i,k` and `s_j,k` and define

```text
w_k = sqrt(s_i,k * s_j,k)
```

The phase-lock resultant is

```text
Z_ij = sum_k w_k * exp(i*delta_k) / sum_k w_k
R_ij = abs(Z_ij)
DELTA_ij = arg(Z_ij)
```

Reference edge admission:

```text
MIN_SHARED_WINDOWS 4
MIN_STAGE2_FIT_SCORE 0.85
MIN_PHASE_LOCK_R 0.90
MAX_RESONANCE_ORDER 16
```

An admitted relation is therefore

```text
RESONANCE_EDGE(H_i,H_j,m,n,R_ij,DELTA_ij)
```

## Canonical orientation

The stored graph uses one canonical edge per unordered band pair, ordered by H-band index.

If the stored orientation is `(H_i,H_j)` with ratio `m:n`, the reverse view is derived exactly as:

```text
ratio_reverse = n:m
R_reverse = R_ij
DELTA_reverse = -DELTA_ij mod 2*pi
```

No duplicate reverse edge is persisted.

## Fail-closed edge gates

```text
LINEAGE_MISMATCH            -> NO_EDGE
INSUFFICIENT_SHARED_WINDOWS -> NO_EDGE
LOW_STAGE2_SCORE            -> NO_EDGE
ORDER_BOUND                 -> NO_EDGE
LOW_PHASE_LOCK              -> NO_EDGE
UNRESOLVED_INPUT            -> EXCLUDED_BEFORE_PAIRING
```

A static live AUX window that produced no Stage-2 `RATIONAL_FIT` therefore produces an empty Stage-3 resonance graph rather than a guessed edge.

## Graph object

The derived graph carries:

```text
GRAPH_CLASS HARMONIC_RESONANCE_DERIVED_INDEX
SOURCE_LINEAGE_SERIES_REF
SOURCE_STAGE2_DERIVATION_IDS
EDGE_SET
GRAPH_DERIVATION_ID
EVIDENCE_REF
```

`GRAPH_DERIVATION_ID` identifies the derived representation. It does not replace any source `OBJECT_ID`.

## Runtime and authority boundary

Resonance edges may later rank codec bases or recall candidates. Any such downstream use remains separately gated.

```text
OBJECT_ID authority = PNV_STATE_OBJECT
capability authority = PNCAP
effect authority = AUX
scheduler lanes = B0..B7
memory bands = H0..H35
```
