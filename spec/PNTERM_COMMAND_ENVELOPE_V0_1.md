# PNTERM Command Envelope v0.1

Status: CANDIDATE / DETERMINISTIC

## Tokenizer

Outside double quotes, ASCII SPACE and TAB separate tokens.

Double quotes preserve spaces inside one token. Inside quotes the only admitted escapes are:

```text
\"  literal double quote
\\  literal backslash
\t  literal tab
```

Stage 1 uses the bounded registry grammar defined below; shell metacharacters remain ordinary argument data.

The first token is the command verb and must match:

```text
[a-z][a-z0-9._-]{0,63}
```

Upper-case or otherwise non-canonical verbs are rejected. Argument Unicode is preserved as the exact admitted UTF-8 sequence.

Bounds:

```text
token count <= 32
token bytes <= 256 each
```

## Envelope

An admitted command envelope contains:

```text
SCHEMA PNTERM_COMMAND_V0_1
SESSION_ID
PRINCIPAL_ID
TERMINAL_EPOCH
RX_SEQ
LINE_SHA256
VERB
ARGS
OPERATION
CAPABILITY_CLASS
COMMAND_ID
```

`COMMAND_ID` is the content address of the canonical envelope fields preceding the identifier.

## Replay / ordering

Within one terminal session:

```text
RX_SEQ <= LAST_ADMITTED_RX_SEQ -> RX_REPLAY_OR_REORDER
```

Sequence identity is included in the command identity. Reusing the same textual line at a new sequence therefore creates a different command transition identity.

## Registry selection

The verb maps by exact match to one versioned operation and one capability class. Unknown verbs are rejected before PNCAP admission.
