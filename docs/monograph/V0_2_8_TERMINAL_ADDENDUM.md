# PNCore-BioOS v0.2.8 Terminal Addendum

This addendum extends the repository monograph `PNCore_BioOS_Od_BIOSu_do_Torsyjnej_Pamieci_v0.2.7` with the first terminal layers.

## Terminal architecture

The terminal line is now:

```text
UART16550 / later physical adapters
 -> AUX.TERM.RX/TX
 -> PNTERM bounded line discipline
 -> PNTERM session and deterministic command envelope
 -> hash-pinned Terminal36D V8 standard 36D vector environment
 -> typed concept/capability gate
 -> PNCAP for authority-bearing operations
 -> AUX effect boundary
 -> execution receipt and PNTERM result
```

Terminal36D V8 is pinned by the exact Library roundtrip profile. It preserves the V7 typed capability manifest with 29 operations and vector dimension 36. PNTERM is the transport/session front-end rather than a parallel execution environment.

The current x86_64 physical terminal candidate is a bounded 16550 polling adapter under `AUX.TERM`, configured for 115200 8N1 in the reference realization. Physical and emulator execution remain explicit later gates.

The bridge is intended to freeze Terminal36D semantics while equivalent typed primitives are progressively realized natively in BioOS PNV/assembly layers.
