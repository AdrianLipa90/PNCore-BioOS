# PAUX Phase Source Contract v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: PNCore-BioOS v0.2.6 stages 1-2

## Purpose

Orbital memory uses phase only when phase provenance is explicit. The phase-source classifier has three states:

```text
DIRECT_PHASE
WINDOW_ANALYTIC
PHASE_UNKNOWN
```

## DIRECT_PHASE

`DIRECT_PHASE` requires an admitted versioned source that supplies exactly 36 finite phase values for the T36 memory projection.

```text
WIDTH 36
FINITE TRUE
SOURCE_REF REQUIRED
```

The phase values are carried as evidence inputs to the derived harmonic index.

A time series of direct-phase records may support a later direct phase-slope estimator. A single direct-phase record supplies phase but does not by itself supply frequency.

## WINDOW_ANALYTIC

The phase-source classifier admits a timestamped AUX window when:

```text
SAMPLES >= 4
CHANNEL_WIDTH 36
TIMESTAMPS STRICTLY_INCREASING
VALUES FINITE
SAMPLING_REF REQUIRED
```

Stage 2 implements bounded harmonic phase/frequency fitting for `WINDOW_ANALYTIC` in `PAUX_HARMONIC_ESTIMATOR_V0_1`. The estimator itself requires at least eight samples and may return `FREQUENCY_UNRESOLVED` without invalidating the underlying PAUX state.

## PHASE_UNKNOWN

`PHASE_UNKNOWN` is the admitted result for a state snapshot that carries no direct phase source and no valid analytic window.

A single T36 amplitude/state snapshot therefore classifies as:

```text
PHASE_SOURCE_MODE PHASE_UNKNOWN
```

This state remains persistable through PAUX according to its existing profile semantics.

## AUX feedback channel

`aux_feedback_phi` retains its live feedback-channel role.

A quadrature role requires an explicit versioned admission contract and evidence reference before it can participate in phase construction.

## Fail-closed classifier

The classifier emits exactly one source mode.

```text
DIRECT_PHASE      -> validate direct source -> emit direct evidence
WINDOW_ANALYTIC   -> validate window contract -> emit window evidence
PHASE_UNKNOWN     -> emit unknown-phase evidence
invalid declaration -> fail closed
```

No source mode is inferred from filename, channel adjacency or numerical resemblance.
