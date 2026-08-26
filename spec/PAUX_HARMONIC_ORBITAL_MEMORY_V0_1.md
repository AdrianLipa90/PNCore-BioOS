# PAUX Harmonic Orbital Memory v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: PNCore-BioOS v0.2.6 stage 1

## Scope

This layer derives a harmonic-orbital memory index from an admitted PAUX / `PNV_STATE_OBJECT` source while preserving the existing PAUX identity, lineage, PNCAP and AUX persistence spine.

The source state remains identified by:

```text
OBJECT_ID
INTEGRITY_HASH
LINEAGE_PARENT
```

The harmonic layer produces a separate derived index:

```text
HARMONIC_ORBITAL_INDEX
SOURCE_OBJECT_ID
DERIVATION_ID
BAND_SET
RESONANCE_EDGE_SET
EVIDENCE_REF
```

`SOURCE_OBJECT_ID` binds the index to the canonical state object. `DERIVATION_ID` identifies the versioned derivation.

## Memory-band namespace

Scheduler admission lanes retain `B0..B7`.

Harmonic memory bands use the distinct namespace:

```text
H0, H1, ..., H35
```

The two namespaces compose through scheduling policy while retaining separate semantics.

## Exact rational harmonic descriptor

A harmonic band descriptor is

\[
H_k=(p_k,q_k,N_k,\theta_k,A_k,Q_k),
\]

with positive coprime integers

\[
p_k>0,\qquad q_k>0,\qquad \gcd(p_k,q_k)=1,
\]

and positive winding number

\[
N_k\in\mathbb N_{>0}.
\]

Relative to the reference frequency \(f_0\),

\[
\boxed{\frac{f_k}{f_0}=\frac{p_k}{q_k}}.
\]

Therefore the wavelength ratio is exact:

\[
\boxed{\frac{\lambda_k}{\lambda_0}=\frac{q_k}{p_k}}.
\]

The orbital closure relation is

\[
\boxed{2\pi r_k=N_k\lambda_k}.
\]

The normalized sphere-radius ratio is represented without floating-point arithmetic:

\[
\boxed{
\frac{r_k}{r_0}
=
\frac{N_k q_k}{N_0 p_k}
}
\]

for the reference band \(p_0=q_0=1\). More generally, for bands \(i,j\),

\[
\boxed{
\frac{r_i}{r_j}
=
\frac{N_i q_i p_j}{N_j p_i q_j}.
}
\]

The canonical stored ratio is the reduced integer pair `(radius_num, radius_den)`.

## Descriptor fields

```text
BAND_ID             H0..H35
RATIO_P             positive u64
RATIO_Q             positive u64
WINDING_N           positive u64
RADIUS_RATIO_NUM    positive u64
RADIUS_RATIO_DEN    positive u64
PHASE_SOURCE_MODE   DIRECT_PHASE | WINDOW_ANALYTIC | PHASE_UNKNOWN
PHASE_REF            versioned phase evidence reference
AMPLITUDE_REF        versioned amplitude evidence reference
COHERENCE_REF        versioned coherence evidence reference
SOURCE_OBJECT_ID     canonical PNV_STATE_OBJECT.object_id
DERIVATION_ID        content-addressed derivation identity
```

The ratio fields are reduced before admission.

## Authority boundary

Canonical recovery authority remains:

```text
PNV_STATE_OBJECT
 -> PNCAP
 -> AUX
 -> PNStore
```

`HARMONIC_ORBITAL_INDEX` carries `AUTHORITY_CLASS DERIVED_INDEX`.

Resonance and orbital proximity provide candidate-selection evidence. Exact capability admission remains bound to PNCAP.

## PAUX profile binding

`PAUX-EXACT` may carry or omit the harmonic index while preserving exact recovery.

`PAUX-C` may use the harmonic index to select an exact historical base frame. The encoded delta remains one of the admitted reversible exact transforms, including `DELTA_XOR64`.

`PAUX-R` may use orbital ratios, phase anchors and resonance edges as reconstruction-model data and records reconstruction metrics under its existing `RECONSTRUCTION_ONLY` authority class.

## Stage-1 gate

Stage 1 admits only:

```text
exact rational band normalization
exact wavelength-ratio derivation
exact orbital radius-ratio derivation
positive winding validation
distinct H-band namespace
derived-index authority binding
phase-source classification
```

Frequency estimation, phase estimation from windows, resonance graph scoring, recall ranking and PAUX-R synthesis enter later v0.2.6 gates.
