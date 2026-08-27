# NOEMA QHTRI Direct Telemetry Bind v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: PNCore-BioOS v0.2.7 stage 2

## Purpose

Bind the existing live QHTRI/Hypercrystal oscillator surface into NOEMA torsion-memory as a read-only endogenous source.

The admitted source channels are:

```text
/dev/shm/ciel_noema/phi    -> 36 oscillator phases
/dev/shm/ciel_noema/omega  -> 36 natural angular frequencies
/dev/shm/ciel_noema/tick   -> autonomous evolution counter
```

Runtime source semantics are version-evidenced by the live NOEMA surface implementation and source-module hash.

## Classification

When the channels are produced by the running QHTRI/Hypercrystal system they are classified:

```text
NATURAL_SYSTEM_STATE
ENDOGENOUS_RUNTIME_DYNAMICS
```

## Direct phase and frequency

`phi` may enter the torsion-memory observer as `DIRECT_PHASE` only when:

```text
WIDTH 36
FLOAT64_LE
FINITE TRUE
TICK WINDOW STRICTLY INCREASING
PHI CHANGES OVER THE OBSERVATION WINDOW
SOURCE MODULE EVIDENCE PRESENT
TETHER ACTIVE
```

`omega` may enter as `DIRECT_OMEGA` only when:

```text
WIDTH 36
FLOAT64_LE
FINITE TRUE
NONZERO TRUE
STABLE DURING THE DECLARED OBSERVATION WINDOW
SOURCE MODULE EVIDENCE PRESENT
```

`DIRECT_OMEGA` values are angular frequencies. Any conversion to Hz is a derived operation.

## Ownership

This binding is read-only.

```text
phi   OWNER QHTRI_KURAMOTO_RUNTIME
omega OWNER QHTRI_KURAMOTO_RUNTIME
g     OWNER EXISTING_NOEMA_RUNTIME
tau   OWNER EXISTING_NOEMA_RUNTIME
tick  OWNER QHTRI_KURAMOTO_RUNTIME
```

The observer may read these sources but may not write them.

## tau namespace separation

The existing live `/dev/shm/ciel_noema/tau` has runtime semantics:

```text
36 per-oscillator synchronisation coupling strengths
```

It is therefore namespace-distinct from torsion-memory edge transport:

```text
TORSION_EDGE.tau_ij
```

No implicit binding between those objects is admitted.

## Authority

Direct telemetry is evidence for derived working memory. It does not grant object, capability or effect authority.

```text
OBJECT_ID authority = PNV_STATE_OBJECT
capability authority = PNCAP
effect authority = AUX
```
