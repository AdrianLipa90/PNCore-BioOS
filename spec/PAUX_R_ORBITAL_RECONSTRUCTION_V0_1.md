# PAUX-R Orbital Reconstruction v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: PNCore-BioOS v0.2.6 stage 5

## Purpose

Stage 5 materializes the first executable harmonic-orbital reconstruction profile for `PAUX-R`.

The profile remains `AUTHORITY_CLASS RECONSTRUCTION_ONLY`. Source identity is referenced by exact `SOURCE_OBJECT_ID`; reconstructed representation identity is carried separately as `RECONSTRUCTION_ID`.

## Source model

For resolved H-band `j`, Stage-2 evidence supplies

```text
p_j:q_j
mean_j
a_j
b_j
```

with exact reference frequency

```text
f_j = (783 * p_j) / (100 * q_j) Hz.
```

The orbital reconstruction model is

```text
x_model,j(t) = mean_j
             + a_j*cos(2*pi*f_j*(t-t0))
             + b_j*sin(2*pi*f_j*(t-t0)).
```

An unresolved band uses its admitted mean as the model component and relies on the residual layer for reconstruction quality.

## Residual profiles

Stage 5 evaluates three reconstruction representations:

```text
MODEL_ONLY
MODEL_QR8
MODEL_QR16
```

For residual

```text
e_j(t) = x_source,j(t) - x_model,j(t)
```

and integer limit `L` (`127` for QR8, `32767` for QR16), define per-band scale

```text
scale_j = max_t |e_j(t)| / L
```

with exact constant residual using a positive neutral scale when the residual is identically zero.

Quantized residual:

```text
q_j(t) = round(e_j(t) / scale_j)
```

Reconstruction:

```text
x_recon,j(t) = x_model,j(t) + q_j(t)*scale_j.
```

## Candidate quality gate v0.1

A representation passes the first PAUX-R orbital quality gate when all declared metrics satisfy:

```text
NRMSE <= 0.02
MAX_ABS_NORM <= 0.02
0.98 <= BAND_ENERGY_RATIO <= 1.02
RELATION_RETENTION >= 0.95
PHASE_MEAN_ERROR_RAD <= 0.05
```

The thresholds are versioned candidate gates and may be changed only through a new recorded validation gate.

## Profile selection

The Stage-5 selector chooses the smallest logical representation among profiles that pass the quality gate.

The logical reference accounting is:

```text
MODEL PARAMETERS per band:
  mean f64
  cosine coefficient f64
  sine coefficient f64
  ratio p u16
  ratio q u16

QR8 / QR16:
  one f64 residual scale per band
  one signed residual integer per sample per band
```

The measured size ratios in the reference receipt apply only to the declared synthetic fixture.

## Reconstruction metrics

The receipt records at least:

```text
NRMSE
MAX_ABS_NORM
BAND_ENERGY_RATIO
RELATION_RETENTION
PHASE_MEAN_ERROR_RAD
LOGICAL_REPRESENTATION_BYTES
```

Relation retention is measured by re-estimating the reconstructed trajectory and comparing admitted rational H-band ratios with the source fit set.

## Identity

```text
SOURCE_OBJECT_ID    exact source provenance
RECONSTRUCTION_ID   content identity of model + profile + residual representation
AUTHORITY_CLASS     RECONSTRUCTION_ONLY
```

Mutation of the representation changes `RECONSTRUCTION_ID`.

A reconstructed state does not inherit source `OBJECT_ID` as its authority identity.

## Fail-closed conditions

```text
non-finite source               -> reject
invalid residual scale          -> reject
quality gate failure            -> profile not admitted
representation hash mismatch    -> reject
missing source reference        -> reject
```

## Exact-profile precedence

If an exact PAUX-C representation is already smaller or otherwise preferred for the observed state, PAUX-R does not replace it.

The current live AUX fixture is static and remains on the exact `PAUX-C RUN` path.

## Authority boundary

```text
SOURCE_OBJECT_ID authority       PNV_STATE_OBJECT
RECONSTRUCTION_ID authority      representation identity only
capability authority             PNCAP
effect authority                 AUX
live restore mutation            separately gated
```
