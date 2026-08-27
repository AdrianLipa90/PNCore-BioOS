# PNVector Handoff Block v0.1

Status: CANDIDATE / TEST-BOUND / FAIL-CLOSED
Epistemic operator: CHYBA
Canon promotion: explicit authority only

## Purpose

PNVector Handoff is the single firmware-to-PNCore state carrier for the current BioOS bootstrap candidate. It carries an exact ordered 36D float64-compatible vector plus deterministic basis and source-context bindings.

## Binary layout

The v0.1 block is exactly 416 bytes: 128-byte identity/provenance header followed by 36 ordered little-endian float64 values.

The exact byte layout consumed by `pncore_entry.S` is:

```text
offset  size  field
0       4     magic0 = ASCII "PNVH"
4       4     magic1 = ASCII "36\0\0"
8       2     version_major = 1, little-endian
10      2     version_minor = 0, little-endian
12      4     header_bytes = 128
16      4     total_bytes = 416
20      2     vector_dim = 36
22      2     scalar_bytes = 8
24      4     endian_marker = 0x01020304
28      4     flags; current physical witness requires low bits 0x7
32      32    basis_binding[32]
64      32    SHA256(exact 288-byte vector payload)
96      32    source_context_sha256
128     288   vector payload = 36 finite float64-le values
```

`basis_binding[32]` is an exact opaque versioned binding for the current `PNCS_36D_BASIS_V0_1` authority. A reproducer must supply the exact 32 bytes used by the admitted witness; it must not infer or silently regenerate those bytes from a label.

Header fields bind magic `PNVH36`, version `1.0`, total bytes `416`, dimension `36`, scalar width `8`, endian marker `0x01020304`, flags, basis binding, exact vector SHA-256 and source-context SHA-256.

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

## Reproducibility rule

A PNROM build that uses `arch/x86_64/pncore/pnvh_template.S` must materialize `build/x86_64/pnvector_handoff_test.bin` from exact provenance-bearing source bytes before assembly.

The deterministic host utility `tools/pnvector_handoff_builder_v01.py` requires:

```text
exact 288-byte vector payload
exact 32-byte basis binding
exact source-context SHA-256
flags
```

and verifies the resulting 416-byte block before writing it. When an expected historical handoff SHA-256 is supplied, any byte mismatch fails closed.

A receipt/hash without the exact source vector and basis-binding bytes is evidence of a historical witness, not sufficient material to reproduce its ROM byte-for-byte.
