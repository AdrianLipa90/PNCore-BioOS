# PNTERM QEMU Interactive Vertical Slice v0.1

Status: IMPLEMENTED CANDIDATE / EPISTEMIC CHYBA / `canon_allowed=false`

## Purpose

This slice is the first directly interactive BioOS execution surface in QEMU. It binds the existing x86_64 UART16550 adapter to a deliberately narrow read-only terminal loop after the exact DNCrypt binary envelope has been recovered from PNStore.

Execution path:

```text
PNROM -> PN32 -> PN64 -> T36ID
 -> PNStore ATA-PIO load / exact DNCrypt recovery
 -> UART16550 COM1 probe + 115200 8N1 init
 -> bounded line input
 -> exact read-only command selection
 -> serial response
 -> evidence
```

## Realization subset

The full PNTERM v0.1 semantic specification remains authoritative for the terminal design. This ROM does **not** claim full UTF-8, quoted tokenizer, command-envelope, session-bound PNCAP, or Terminal36D semantic conformance.

The executable realization is intentionally narrower:

- input encoding: printable ASCII plus CR/LF/TAB/BS/DEL editing controls;
- TAB is normalized to one ASCII space;
- line bound: 255 bytes;
- other controls and non-ASCII bytes: fail-closed rejection;
- registry: `help`, `status`, `store.show`, `terminal.selftest`, `echo`;
- unknown verbs, including write-like names such as `store.write`, reject;
- default write commands: zero;
- no shell, redirection, wildcard expansion, process launch, or arbitrary execution.

This narrower bound is a physical/emulator realization subset, not a silent replacement for the broader PNTERM v0.1 bounds.

## Persistent-state binding

Before the prompt is exposed, the ROM requires a valid PNStore generation 1 and verifies all of the following against the pinned DNCrypt fixture:

```text
transition_id     exact 32 bytes
object_digest     exact SHA-256(payload)
payload_length    exactly 2552 bytes
payload_bytes     exact full binary envelope
payload magic     DNCB
```

First use requires an all-zero medium and preserves the existing PNStore durability order:

```text
superblock -> FLUSH
extent     -> FLUSH
HEAD_A     -> FLUSH
reread from device -> recover -> exact payload verify
```

On an existing medium, the same stable transition must resolve to `ALREADY_COMMITTED`; the terminal is not exposed until the exact payload binding is reverified.

## Interactive conformance

The QEMU gate runs two independent processes against the same raw IDE image.

Session 1 must expose the prompt and execute the read-only command set, including exact store and self-test responses.

Session 2 supplies a write-like unknown command and a rejected control character, then performs read-only inspection. The raw PNStore image must remain byte-identical to the image after session 1.

The gate records:

- QEMU version and binary SHA-256;
- ROM SHA-256 and build receipt;
- exact input scripts and their SHA-256 values;
- serial transcript and debugcon transcript hashes;
- PNStore parser result;
- exact DNCrypt payload binding checks;
- disk SHA-256 after each independent process.

## Claim boundary

A PASS demonstrates an executable QEMU UART16550 read-only interactive surface joined to exact DNCrypt-through-PNStore persistence under the tested PIIX IDE/ATA-PIO model. It does not demonstrate full PNTERM semantic conformance, bare-metal hardware compatibility, physical power-loss durability, DN36 cryptographic authority, or canon status.
