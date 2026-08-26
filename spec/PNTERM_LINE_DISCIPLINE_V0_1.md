# PNTERM Line Discipline v0.1

Status: CANDIDATE / FAIL-CLOSED

## Input

The semantic input is an ordered byte stream received through `AUX.TERM.RX`.

UTF-8 decoding is incremental across transport chunks. A multi-byte codepoint may span multiple RX chunks.

## Canonical line termination

```text
LF    -> END_LINE
CR    -> END_LINE
CRLF  -> one END_LINE
```

The line hash is SHA-256 over the exact canonical UTF-8 line bytes excluding the terminator.

## Editing

Before line publication:

```text
BS 0x08 -> delete previous Unicode codepoint if present
DEL 0x7f -> delete previous Unicode codepoint if present
TAB      -> retained as U+0009 token separator
```

Other C0/C1 controls, including NUL and ESC, are rejected in v0.1.

Stage 1 classifies ANSI escape sequences under `CONTROL_CHAR_REJECTED`; a versioned terminal-control parser is reserved for a later gate.

## Bounds

```text
line bytes      <= 1024
line codepoints <= 512
```

An empty completed line emits `EMPTY_LINE_NOOP`; command dispatch receives only `LINE_READY` events.

## Failure states

```text
INVALID_UTF8
CONTROL_CHAR_REJECTED
LINE_BYTES_OVERFLOW
LINE_CODEPOINTS_OVERFLOW
DISCIPLINE_FAILED
```

After a fail-closed line-discipline error the affected discipline instance must be reset before further input.
