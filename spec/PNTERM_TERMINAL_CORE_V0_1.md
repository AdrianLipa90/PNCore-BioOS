# PNTERM Terminal Core v0.1

Status: CANDIDATE / EPISTEMIC CHYBA / canon_allowed=false
Release target: PNCore-BioOS v0.2.8 stage 1

## Purpose

PNTERM is the first bounded terminal surface for PNCore-BioOS. It establishes a deterministic path from admitted text input to a versioned command envelope and read-only dispatch while preserving the existing PNCAP/AUX authority boundary.

```text
physical input adapter
 -> AUX.TERM.RX
 -> UTF-8 / line discipline
 -> deterministic tokenizer
 -> PNTERM_COMMAND
 -> exact registry selection
 -> PNCAP admission
 -> read-only resolver
 -> PNTERM_RESULT
 -> AUX.TERM.TX
 -> evidence
```

The terminal is a control surface over BioOS state and reuses the canonical PNCAP/AUX authority path.

## Stage-1 scope

Stage 1 admits only a bounded read-only registry:

```text
help
status
clock.show
store.show
memory.show
terminal.selftest
echo
```

Stage 1 grammar consists of exact registry selection plus opaque arguments. Metacharacters, wildcard-like text and redirection-like text are classified as argument data.

Characters such as `;`, `|` and `$` are ordinary token data when they occur in arguments.

## Authority

```text
OBJECT_ID authority = PNV_STATE_OBJECT
capability authority = PNCAP
effect authority = AUX
persistent authority = PNStore
terminal command identity = PNTERM_COMMAND.command_id
```

All dispatch operations require an exact session-bound PNCAP grant. The Stage-1 registry is the seven read-only verbs listed above; mutation verbs are reserved for a separately versioned gate.

## Layer split

```text
L0  PNTERM_AUX_TRANSPORT
L1  PNTERM_LINE_DISCIPLINE
L2  PNTERM_COMMAND_ENVELOPE
L3  PNTERM_READONLY_DISPATCH
L4  PNTERM_RESULT_EVIDENCE
```

A later physical realization may bind UART, keyboard/framebuffer or another device adapter below `AUX.TERM.RX/TX` while preserving the semantic command path.

## Bounds

```text
MAX_LINE_BYTES       1024
MAX_LINE_CODEPOINTS   512
MAX_TOKENS              32
MAX_TOKEN_BYTES         256
MAX_OUTPUT_BYTES       4096
DEFAULT_WRITE_COMMANDS    0
```

Every bound is fail-closed.
