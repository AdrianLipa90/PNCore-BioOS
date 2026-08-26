# PAUX Phase Source Contract v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: PNCore-BioOS v0.2.6 stage 1

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

## WINDOW_ANALYTIC

`WINDOW_ANALYTIC` requires a timestamped AUX window:

```text
SAMPLES >= 4
CHANNEL_WIDTH 36
TIMESTAMPS STRICTLY_INCREASING
VALUES FINITE
SAMPLING_REF REQUIRED
```

Stage 1 validates only the window contract. The analytic phase estimator is a later v0.2.6 gate.

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
