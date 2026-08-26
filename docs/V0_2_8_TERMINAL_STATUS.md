# PNCore-BioOS v0.2.8 Terminal Status

Current branch: `feat/bioos-v0.2.8-terminal-core`

## Implemented stages

- Stage 1 — PNTERM bounded terminal core: 47/47 PASS.
- Stage 2 — x86_64 UART16550 physical adapter candidate: 35/35 PASS; physical/emulator execution pending.
- Stage 3 — Terminal36D V8 standard vector environment bridge: 38/38 PASS.

Total declared v0.2.8 checks: 120/120 PASS.

## Active architecture

```text
UART16550 / future terminal adapter
 -> AUX.TERM.RX/TX
 -> PNTERM line discipline
 -> PNTERM session/envelope
 -> Terminal36D V8 exact hash profile
 -> typed operation / concept gate
 -> PNCAP where authority is required
 -> AUX
 -> evidence/result
```

Terminal36D V8 is the standard 36D vector environment for this development line. PNTERM is the bounded transport/session front-end.

## Profile identity

- vector dimension: 36
- typed capabilities: 29
- exact V8 roundtrip receipt: `1cc2cd64b53e158d4bf0e144ff3ef5dca851cefc094f62901d5042b6155ed2d7`
- `terminal36d.py`: `78082702c4b7a17a061ca7b9b83f4c21765307c70dfbefd301466224389cce9b`
- `vector_kernel.py`: `68663aea2c188b77b46e5ecf2488bfdfb27a7f2cd8387fb78b6bc5dce6de0e14`
- `concept_gates.py`: `a3aeda6f1ca0c445767bba8176c5b6c7d791bd97e03b33fe2ed8dccb9c97bc49`

The repository carries the full readable BioOS monograph source plus a v0.2.8 terminal addendum under `docs/monograph/`; generated PDF/DOCX hashes are pinned in the same directory.
