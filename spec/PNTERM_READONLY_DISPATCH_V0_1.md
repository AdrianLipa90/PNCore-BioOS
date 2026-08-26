# PNTERM Read-Only Dispatch v0.1

Status: CANDIDATE / READ-ONLY REGISTRY

## Registry

```text
help              -> TERM.HELP.READ      -> TERMINAL_PUBLIC_READ
status            -> TERM.STATUS.READ    -> TERMINAL_STATUS_READ
clock.show        -> TERM.CLOCK.READ     -> TERMINAL_CLOCK_READ
store.show        -> TERM.STORE.READ     -> TERMINAL_STORE_READ
memory.show       -> TERM.MEMORY.READ    -> TERMINAL_MEMORY_READ
terminal.selftest -> TERM.SELFTEST.READ  -> TERMINAL_SELFTEST_READ
echo              -> TERM.ECHO.READ      -> TERMINAL_ECHO_READ
```

`DEFAULT_WRITE_COMMANDS = 0`.

## PNCAP binding

A dispatch grant must match all of:

```text
PRINCIPAL_ID
OPERATION
CAPABILITY_CLASS
SESSION_ID
TERMINAL_EPOCH
RX_SEQ
ADMITTED = TRUE
```

Any mismatch rejects dispatch.

## Result

A successful result contains:

```text
SCHEMA PNTERM_RESULT_V0_1
SESSION_ID
TERMINAL_EPOCH
RX_SEQ
TX_SEQ
COMMAND_ID
STATUS
PAYLOAD
PAYLOAD_SHA256
AUX_EFFECT
RESULT_ID
```

For Stage-1 verbs:

```text
AUX_EFFECT NONE
```

Text leaves the semantic terminal through `AUX.TERM.TX`; physical UART/framebuffer/PTY encoding is an adapter realization below AUX.

## Output bound

```text
payload bytes <= 4096
```

A larger response emits `OUTPUT_TOO_LARGE` / pagination requirement rather than silent truncation.
