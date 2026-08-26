# PAUX-C Harmonic Base Selection v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: PNCore-BioOS v0.2.6 stage 4

## Purpose

Stage 4 uses the harmonic-orbital derived index only to propose earlier exact PAUX frames as candidate bases for the existing lossless `DELTA_XOR64` transform.

The harmonic layer does not synthesize PAUX-C payloads. Exact target bytes remain authoritative.

## Candidate production

For target frame `F_t`, a derived phase-revisit candidate `F_c` must satisfy:

```text
c < t
AGE = t-c <= 64
COMMON_RESOLVED_H_BANDS >= 2
MEAN_WRAPPED_PHASE_DISTANCE <= 0.20 rad
LINEAGE_SERIES_REF compatible
```

The phase-revisit gate is only a bounded candidate generator. False candidates cannot acquire authority.

If no harmonic candidate exists, PAUX-C keeps the existing previous-frame base.

## Exact base-selection cost

The baseline base `F_(t-1)` is always included.

For every admitted candidate base `F_c`, compute the exact little-endian 64-bit XOR delta:

```text
X_i = WORD_i(F_c) XOR WORD_i(F_t)
CHANGED_WORDS(c,t) = count(X_i != 0)
```

The chosen base minimizes:

```text
(CHANGED_WORDS, AGE, FRAME_INDEX)
```

lexicographically.

Therefore harmonic selection cannot increase changed-word cost relative to the existing previous-frame baseline.

## Transform routing

After base selection:

```text
base == target and base == previous -> RUN
base == target and older            -> REF
otherwise                           -> DELTA_XOR64
```

`DELTA_XOR64` remains exact sparse XOR of 64-bit words plus changed indices. No floating-point arithmetic participates in the lossless delta or decode.

## Decode and authority

```text
TARGET
 -> candidate discovery
 -> exact cost selection
 -> RUN / REF / DELTA_XOR64
 -> exact decode
 -> OBJECT_ID recomputation
 -> INTEGRITY recomputation
 -> lineage verification
 -> evidence
```

A decode is recovery-capable only after the same exact verification required by existing PAUX-C.

## Fail-closed conditions

```text
future base reference       -> excluded
candidate age > 64          -> excluded
duplicate candidate         -> canonicalized
invalid XOR word index      -> reject
repeated XOR index          -> reject
corrupted exact delta       -> exact verification failure
harmonic candidate worse    -> baseline remains selected
unresolved phase signature  -> no harmonic candidate
```

## Live-static behavior

The current live AUX fixture is static. Existing `RUN` semantics are already optimal, so Stage 4 does not replace that path with a harmonic base.

## Evidence boundary

The measured dynamic reduction in the Stage-4 receipt comes from a `SYNTHETIC_REFERENCE` periodic fixture used to test the selector. It is not a measured live compression ratio.

## Authority boundary

```text
harmonic phase index        DERIVED_INDEX
harmonic candidate refs     DERIVED_INDEX
PAUX-C decoded bytes        exact verification required
OBJECT_ID authority         PNV_STATE_OBJECT
capability authority        PNCAP
effect authority            AUX
```
