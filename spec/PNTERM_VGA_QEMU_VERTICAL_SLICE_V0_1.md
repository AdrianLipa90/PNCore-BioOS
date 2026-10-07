# PNTERM VGA QEMU Visible Vertical Slice v0.1

Status: IMPLEMENTED CANDIDATE / EPISTEMIC CHYBA / `canon_allowed=false`

## Purpose

This slice adds the first directly visible BioOS terminal surface in QEMU without changing the authority model proven by the preceding interactive PNTERM gate. UART16550 remains the bounded input/control transport; every admitted terminal output byte is additionally mirrored into legacy VGA 80x25 text memory at physical `0xB8000`.

Execution path:

```text
PNROM -> PN32 -> PN64 -> T36ID
 -> PNStore ATA-PIO exact DNCrypt recovery
 -> UART16550 COM1 probe + 115200 8N1 init
 -> VGA 80x25 deterministic clear
 -> bounded read-only PNTERM loop
 -> UART response + VGA text mirror
 -> QEMU physical-memory witness
 -> evidence
```

## VGA realization

The display plane is the classic 80 columns x 25 rows text buffer with two bytes per cell:

```text
byte 0: character
byte 1: attribute = 0x07
```

The surface is cleared to `0x0720` before the banner is emitted. Cursor state is held as bounded row/column counters. CR resets the column, LF advances a row, BS mirrors terminal editing, printable ASCII writes one cell, line wrap advances a row, and row overflow scrolls rows 1..24 upward and clears the final row.

The display is subordinate to terminal semantics: writing VGA memory cannot admit a command, create an effect, change PNCAP authority, or mutate PNStore.

## Persistent-state prerequisite

The prompt is not exposed until generation 1 is recovered and the complete pinned DNCrypt binary envelope is byte-for-byte verified against the embedded fixture:

- transition id: exact 32 bytes;
- object digest: exact `SHA-256(payload)`;
- payload length: exactly 2552 bytes;
- payload bytes: exact complete envelope;
- payload magic: `DNCB`.

The existing PNStore ordering remains unchanged: superblock -> FLUSH, extent -> FLUSH, HEAD_A -> FLUSH, device reread, recovery, exact payload verification.

## QEMU evidence

The conformance gate uses two independent QEMU processes against one raw IDE image. Input is synchronized on the actual `bioos> ` guest prompt. While each guest remains live, the QEMU human monitor executes:

```text
pmemsave 0xb8000 4000 <evidence file>
```

The gate parses all 2000 VGA cells from the physical-memory dump, requires attribute `0x07` on every cell, and requires the expected terminal transcript to be visible in order. Session 1 exercises `help`, `status`, `store.show`, `terminal.selftest`, and `echo`. Session 2 injects a write-like unknown command and a rejected control character before read-only inspection. The PNStore disk must remain byte-identical across the second process.

The inherited adversarial PNStore gate is also run against the VGA ROM; corrupt superblock, HEAD, extent payload, and extent seal cases must halt fail-closed before any successful terminal/VGA admission marker.

## Claim boundary

A PASS demonstrates actual QEMU execution of a read-only UART16550 PNTERM subset whose output is materially present in VGA 80x25 text memory and independently read back through QEMU physical-memory inspection, while exact DNCrypt-through-PNStore persistence remains intact.

It does not demonstrate a framebuffer, compositor, window manager, PS/2 keyboard path, full PNTERM UTF-8/token/envelope/PNCAP semantic conformance, physical display hardware, physical power-loss durability, or canon status.
