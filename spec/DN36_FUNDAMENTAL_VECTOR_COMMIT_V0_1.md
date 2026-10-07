# DN36 Fundamental Vector Commitment v0.1

Status: `EXPERIMENTAL_CRYPTO_PRIMITIVE / CHYBA / canon_allowed=false`

This document defines a first BioOS-native 36-dimensional commitment candidate built from already existing DNCrypt, TIR and Resonant-Chemistry structures. It is deliberately **not** promoted as a secure replacement for SHA-256/BLAKE2/SHA-3. Its purpose is to create an executable object that can be benchmarked, attacked and optimized before any security claim is made.

## Source pins

### DNCrypt

Repository: `AdrianLipa90/DNCrypt`

Pinned main commit: `20f53a9b297b6208d74841aee7c3bb4b8b17ce2a`

Pinned native program:

`native/programs/DNCRYPT_NATIVE_PNCS_V0_3.pnv` @ blob `99df240db1db020dea24b51b160de90bce727eb2`

The candidate reuses the DNCrypt design separation between a 36D genome (`operator_vector36`, `route36`, `phase36`), resident state evolution, explicit entropy admission and conventional cryptographic anchors. The frozen DNCrypt AEAD protocol is not modified.

### TIR

Repository: `AdrianLipa90/The-Fundamental-Theory-of-Informational-Relations`

Pinned main commit: `45b54c0c8aa60ec92607e6132b69aca9ab766d75`

Pinned coding theorem:

`TIR/foundations/TIR_GOLDEN_MEAN_CODING_CONJUGACY_V0_1.md` @ blob `b07d0338aeb47ad548f8fd91495ec8b793d3c0e6`

Pinned transfer theorem:

`TIR/foundations/TIR_GOLDEN_MEAN_TRANSFER_KAPPA_V0_1.md` @ blob `8c9ac7116ace93b5f8a21e857441e57f8d8afb56`

The exact upstream object is the golden-mean language with forbidden word `11`, adjacency matrix

```text
A = [[1,1],[1,0]]
```

and exact symbolic coding/conjugacy. DN36 does **not** reinterpret this as cryptographic security. It uses the no-`11` language as a deterministic nonlinear scheduling constraint.

### Resonant Chemistry

Repository: `AdrianLipa90/Resonant-Chemistry`

Pinned main commit: `6a9f21678ba4f07e5bdbb1a98a0cafe5c4838697`

Pinned T36 Aufbau realization:

`reschem/atomic_t36_aufbau_v015.py`

Pinned tetrahedral inference geometry:

`reschem/tetrahedral_inference_v015.py` @ blob `93196ec38992881d38e9c6a82d82c434ce819946`

DN36 reuses the frozen 36-slot spin-orbital ordering and the tetrahedral sign frame only as a **lane geometry / coupling topology**. It does not claim that atomic physics proves cryptographic strength.

## 1. Architectural purpose

Current BioOS receipts frequently cross the boundary

```text
36D state -> canonical bytes -> conventional hash -> receipt
```

DN36 introduces an internal path

```text
36D / 288-byte block
 -> DNCrypt-derived genome constants
 -> TIR golden-mean constrained schedule
 -> Resonant-Chemistry 36-lane geometry
 -> DN36 ARX diffusion rounds
 -> 2304-bit resident state
 -> candidate 256-bit fold
 -> independent conventional anchor
```

The conventional anchor remains mandatory during the experimental phase.

## 2. 36-lane basis

The lane order is frozen to the Resonant-Chemistry Aufbau basis:

```text
1s, 2s, 2p, 3s, 3p, 4s, 3d, 4p
```

with each subshell expanded in ascending `m_l`, then spin `alpha`, `beta`, producing exactly 36 lanes.

A lane therefore has a stable tuple

```text
(index, n, l, m_l, spin)
```

which is used to derive rotation/coupling constants. The chemistry labels are structural coordinates, not secret material.

## 3. Golden-mean message schedule

The upstream TIR language is

```text
L_GM = { binary words with no substring 11 }.
```

For arbitrary input bits DN36 v0.1 defines a new BioOS-local injective morphism

```text
0 -> 0
1 -> 10
```

called `BIOOS_GM_INJECTIVE_MORPHISM_V0_1`.

The result always lies in the no-`11` language and can be decoded unambiguously. This morphism is **not** claimed as an upstream TIR theorem; it is a DN36 engineering construction that consumes the TIR language constraint.

The resulting symbols select alternating branches of the round function. Their role is scheduling/diffusion, not entropy generation.

## 4. DNCrypt-derived genome constants

DN36 v0.1 uses a fixed domain-separated genome seed to derive:

```text
operator_vector36 : 36 uint8 values
route36           : permutation of 0..35
phase36_u64       : 36 uint64 values
```

The derivation follows the DNCrypt v0.3 structure. For the reference implementation, SHAKE256 is used only for deterministic constant derivation and for the independent external anchor path. Replacing that derivation is a later gate.

No runtime secret is implied by these constants.

## 5. Block geometry

The native block is exactly

```text
36 lanes x 64 bits = 2304 bits = 288 bytes.
```

This deliberately matches the existing BioOS 288-byte head-to-head benchmark payload.

Messages are domain-separated and length-bound before padding. Padding is deterministic and injective at the block layer.

## 6. DN36 round family

Each round combines:

1. modular 64-bit addition;
2. XOR;
3. lane-specific rotations;
4. DNCrypt `route36` permutation/cross-lane access;
5. DNCrypt `operator_vector36` constants;
6. TIR golden-mean schedule symbols;
7. Resonant-Chemistry lane coordinates;
8. tetrahedral four-class sign/coupling selection.

The reference implementation uses 12 rounds. This round count is a test parameter, **not a security claim**.

The internal state after absorption is 36 x uint64. No projection to binary process/IPC semantics is required inside the round family.

## 7. Outputs

DN36 emits three separately typed outputs:

```text
DN36_STATE2304
    complete 36 x uint64 post-mix state

DN36_FOLD256
    experimental 256-bit fold of the 36D state

DN36_ANCHOR256
    conventional BLAKE2b-256 anchor over the canonical DN36 state bytes
```

During v0.1:

```text
DN36_FOLD256 != trusted cryptographic digest
DN36_ANCHOR256 = required external integrity anchor
```

A BioOS receipt may carry both. `DN36_FOLD256` must never silently replace an existing SHA/BLAKE/SHA3 identity until promotion gates are satisfied.

## 8. Security and cryptanalysis gates

Promotion requires quantitative evidence, at minimum:

- deterministic known-answer vectors;
- one-bit input avalanche close to 50% over a preregistered population;
- per-output-bit bias and bit-independence measurements;
- differential tests across message, domain and length changes;
- reduced-round collision/preimage search;
- fixed-point and short-cycle search;
- route/operator symmetry tests;
- rotational and lane-permutation attack attempts;
- duplicate-state search across large random populations;
- scalar/reference versus native/SIMD exact equivalence;
- independent cryptanalytic review.

Failing any required gate leaves the primitive experimental.

## 9. Performance gates

The benchmark must compare the same payload and host for:

```text
SHA-256
BLAKE2b-256
SHA3-256
DN36 reference scalar
DN36 native/SIMD
DN36 batch-32
DN36 batch-256
full BioOS receipt with conventional hash
full BioOS receipt with DN36 + external anchor
```

Report at least ns/op, us/op, ops/s, GB/s, cycles/byte where available, batch scaling, and full receipt end-to-end latency.

A faster internal fold is irrelevant if the full receipt path becomes slower.

## 10. DNCrypt boundary

DNCrypt remains the security anchor for actual encryption in this stage:

```text
plaintext/state
 -> DN36 internal commitment candidate
 -> exact BioOS AAD
 -> DNCrypt HKDF-SHA3-512
 -> ChaCha20-Poly1305 AEAD
 -> DNCrypt receipt / standard anchor
```

DN36 therefore starts as a resident state commitment/mixing primitive, not a replacement AEAD.

## 11. Claim firewall

```text
vector-native 36D implementation       = TARGET / TESTABLE
TIR no-11 schedule                      = EXACT UPSTREAM + DN36 ENGINEERING USE
Resonant-Chemistry 36-lane basis        = PINNED STRUCTURAL REUSE
DNCrypt genome/route/phase architecture = PINNED STRUCTURAL REUSE
cryptographic security                  = NOT ESTABLISHED
replacement for SHA/BLAKE/SHA3          = NOT AUTHORIZED
physical quantum execution              = NOT CLAIMED
canon_allowed                           = false
```

The only valid v0.1 promotion target is `EXPERIMENTAL_MEASURED_CANDIDATE`.