# PAUX Codec Profiles v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false

## Scope

PAUX codec profiles transform the persistent AUX carrier while preserving the identity and lineage rules inherited from `PNV-State-Memory`.

The profile family is:

```text
PAUX-EXACT  -> exact persistent AUX state
PAUX-C      -> compressed lossless persistent AUX state
PAUX-R      -> relational reconstruction profile
```

`PAUX-EXACT` and `PAUX-C` share the exact recovery spine:

```text
SOURCE_STATE
 -> PNV_STATE_OBJECT
 -> ENCODE
 -> DECODE
 -> VERIFY_EXACT
 -> EVIDENCE
```

`PAUX-R` uses a reconstruction evidence spine:

```text
SOURCE_OBJECT_ID
 -> RELATIONAL_MODEL
 -> RECONSTRUCT
 -> VERIFY_RECONSTRUCTION
 -> RECONSTRUCTION_ID
 -> EVIDENCE
```

## PAUX-EXACT

The exact profile preserves admitted AUX channel payloads byte-for-byte. For the current T36 runtime binding, each channel payload is exactly 36 finite little-endian float64 values (288 bytes).

Candidate textual carrier encoding:

```text
PROFILE EXACT
ENCODING AUXHEX64/1
STATE_OBJECT <canonical PNV_STATE_OBJECT>
```

`AUXHEX64/1` is a host-visible exact textual realization. Physical media adapters may use another versioned encoding while preserving the same object identity and exact decoded payload.

## PAUX-C lossless

PAUX-C may use only reversible transforms whose decoded state passes the same exact identity/integrity verification as PAUX-EXACT.

Initial transforms:

```text
KEYSTATE      full exact state payload
REF           reference to a hash-equal channel/frame
RUN           repeat an exact previous frame
DELTA_XOR64   sparse XOR of little-endian 64-bit words against an admitted base
```

For `DELTA_XOR64`, changed-word indices and exact 64-bit XOR words are sufficient for reconstruction. No floating-point arithmetic participates in the lossless delta.

A PAUX-C descendant is recovery-capable only after exact decode, `OBJECT_ID` recomputation, integrity recomputation and lineage verification all pass.

## PAUX-R reconstruction

PAUX-R is the profile for MP3-like relational/state compression. It preserves a source reference and reconstructs an admitted approximation under explicit metrics.

Candidate components include:

```text
KEYSTATE
RELATION_MASK
T36_SALIENCE_MASK
QUANTIZED_RESIDUAL
PHASE_MODEL
RUN / PREDICTED_RUN
RECONSTRUCTION_METRICS
```

PAUX-R carries:

```text
SOURCE_OBJECT_ID      exact source provenance
RECONSTRUCTION_ID     content identity of the reconstruction representation
AUTHORITY_CLASS       RECONSTRUCTION_ONLY
```

Verification records explicit reconstruction metrics such as maximum absolute T36 error, RMS error, retained relation set and phase/coherence diagnostics appropriate to the source state.

## Live endpoint boundary

The current `/dev/shm/ciel_noema/aux_phi` and `aux_feedback_phi` files remain the live T36 transport bindings. PAUX materialization reads admitted snapshots from that live surface and writes persistent objects separately.

A restore candidate is first reconstructed into a shadow/admission surface, verified, then may be admitted into a live generation by the existing AUX/PNCAP authority path.

## Evidence from first live fixture

The first PAUX-EXACT live fixture restored both 288-byte T36 channels byte-identically into a shadow surface.

The first PAUX-C live observation fixture contained 64 frames in which the AUX state remained unchanged and `aux_feedback_phi` was byte-identical to `aux_phi`. `KEYSTATE + REF + RUN` reconstructed all 64 frames exactly. This measured fixture is recorded as a favorable live case rather than a general compression ratio.

## GREMLIN structural boundary

GREMLIN v0.5 relation comparison found:

```text
PAUX-EXACT <-> PAUX-C lossless          structurally_isomorphic=true
PAUX-EXACT <-> PAUX-R reconstruction    structurally_isomorphic=false
```

The PAUX-C hypothesis is recorded as `SUPPORTED_BY_DECLARED_TESTS`.
