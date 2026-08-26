# PAUX Harmonic Estimator v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: PNCore-BioOS v0.2.6 stage 2

## Purpose

Stage 2 converts an admitted timestamped T36 AUX window into bounded harmonic-fit evidence for the derived `H0..H35` orbital-memory index.

The estimator does not change `PNV_STATE_OBJECT` identity, lineage, PNCAP authority, AUX effect authority or PNStore commit semantics.

## Inputs

`WINDOW_ANALYTIC` estimation requires:

```text
SAMPLES >= 8
CHANNEL_WIDTH 36
TIMESTAMPS STRICTLY_INCREASING
VALUES FINITE
SAMPLING_REF REQUIRED
SOURCE_OBJECT_ID REQUIRED
```

The Stage-1 phase-source classifier still admits a timestamped analytic window with at least four samples. Stage-2 frequency fitting requires at least eight samples.

## Exact harmonic reference

The reference frequency is represented exactly as

```text
f0 = 783 / 100 Hz
```

A candidate harmonic ratio is a reduced positive integer pair

```text
p:q
```

with Stage-2 reference bounds

```text
1 <= q <= 16
1/4 <= p/q <= 4
f0 * p/q < 0.48 * f_s
```

The bounded candidate frequency is therefore

```text
f_pq = (783 * p) / (100 * q) Hz
```

The integer pair is the persisted derived ratio descriptor. Floating-point evaluation belongs to fit evidence only.

## Window harmonic fit

For T36 component `j`, center the admitted scalar trajectory

```text
y_n = x_j(t_n) - mean(x_j)
```

and for each admitted ratio `p:q` construct

```text
A_pq(n) = [ cos(2*pi*f_pq*(t_n-t_0)), sin(2*pi*f_pq*(t_n-t_0)) ]
```

The two fit coefficients `(a,b)` are obtained by bounded least squares.

```text
amplitude = hypot(a,b)
phase     = atan2(b,a)
score     = 1 - SSE/SST
```

A pure trajectory `A*cos(2*pi*f*t - phi)` therefore reports phase `phi` under this convention.

## Resolution-aware ambiguity gate

For a window duration `T` define

```text
DELTA_F_WINDOW = 1 / T
```

The runner-up score used for ambiguity is the strongest candidate separated from the best candidate by at least `DELTA_F_WINDOW`.

Reference admission defaults are:

```text
MIN_FIT_SCORE 0.85
MIN_SCORE_MARGIN 0.05
```

A band fit is emitted only if both gates pass.

```text
PASS -> RATIONAL_FIT(p,q,phase,amplitude,score,margin)
FAIL -> FREQUENCY_UNRESOLVED
```

`RATIONAL_FIT` means that the bounded declared model selected `p:q` under the recorded window and thresholds. The evidence record carries the score and resolution margin.

## Low-information and invalid windows

The following cases fail closed for frequency assignment:

```text
ZERO_VARIANCE               -> FREQUENCY_UNRESOLVED
LOW_SCORE                   -> FREQUENCY_UNRESOLVED
AMBIGUOUS_MULTI_TONE        -> FREQUENCY_UNRESOLVED
TOO_SHORT                   -> reject estimator input
NON_MONOTONIC_TIMESTAMPS    -> reject estimator input
NON_FINITE                  -> reject estimator input
```

A static live AUX window therefore remains valid PAUX state evidence while producing no harmonic-frequency claim.

## H-band binding

Each T36 projection component retains its Stage-1 memory namespace identity `H0..H35`.

Stage 2 adds a derived fit record:

```text
H_BAND
SOURCE_OBJECT_ID
WINDOW_ID
PHASE_SOURCE_MODE WINDOW_ANALYTIC
RATIO_P
RATIO_Q
FIT_SCORE
FIT_MARGIN
PHASE
AMPLITUDE
WINDOW_RESOLUTION_HZ
DERIVATION_ID
```

The record remains `AUTHORITY_CLASS DERIVED_INDEX`.

## Runtime boundary

Harmonic fitting is computation over admitted AUX evidence. Any later restore, recall, persistence or physical effect remains behind the existing PNCAP/AUX path.

Scheduler bands `B0..B7` remain operational admission lanes and are not memory bands.
