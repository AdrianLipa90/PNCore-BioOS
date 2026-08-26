# PNVector Handoff Block v0.1

Status: CANDIDATE / TEST-BOUND / FAIL-CLOSED
Epistemic operator: CHYBA
Canon promotion: explicit authority only

## Purpose

PNVector Handoff is the single firmware-to-PNCore state carrier for the current BioOS bootstrap candidate. It carries an exact ordered 36D float64-compatible vector plus deterministic basis and source-context bindings.

## Binary layout

The v0.1 block is exactly 416 bytes: 128-byte identity/provenance header followed by 36 ordered little-endian float64 values.

Header fields bind magic `PNVH36`, version `1.0`, total bytes `416`, dimension `36`, scalar width `8`, endian marker `0x01020304`, flags, basis identifier, exact vector SHA-256 and source-context SHA-256.

The current physical witness uses flags `0x7`. Its vector is the exact admitted live `phi` snapshot used for bootstrap conformance. The basis identifier remains `PNCS_36D_BASIS_V0_1`, with semantic-axis promotion governed by the separate basis authority.

```text
PNROM identity
 + machine context
 + basis/source binding
 -> admission
 -> PNVector Handoff @ 0x5000
 -> PNCore
 -> PNR + PNMap admission
 -> Sigma_0
 -> evidence
```

The PNR header stays in immutable ROM. CR3 supplies the PNMap physical anchor directly. This keeps one runtime handoff object at the firmware-to-PNCore boundary.
