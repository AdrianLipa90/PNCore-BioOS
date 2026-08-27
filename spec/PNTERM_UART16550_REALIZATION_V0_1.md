# PNTERM x86_64 16550 UART Realization v0.1

Status: PHYSICAL BACKEND CANDIDATE / HOST BUILD VALIDATED / EXECUTION PENDING
Release target: PNCore-BioOS v0.2.8 stage 2
Epistemic operator: CHYBA
Canon allowed: false

## Purpose

This realization binds the semantic terminal transport

```text
AUX.TERM.RX
AUX.TERM.TX
```

to an optional x86 legacy 16550-compatible UART resource.

The UART layer sits below AUX. PNTERM command parsing, command identity and PNCAP command admission remain above this adapter.

## Resource identity

The default reference resource is:

```text
ADAPTER_ID UART16550_POLL_V0_1
ARCH x86_64
IO_BASE 0x03F8
REGISTER_SPAN 8
REFERENCE_INPUT_CLOCK_HZ 1843200
REFERENCE_BAUD 115200
FRAME 8N1
MODE BOUNDED_POLLING
```

A different I/O base is a different admitted resource binding.

## Register geometry

```text
+0 RBR / THR / DLL
+1 IER / DLM
+2 IIR / FCR
+3 LCR
+4 MCR
+5 LSR
+6 MSR
+7 SCR
```

## Reversible probe

The reference probe uses the scratch register:

```text
read SCR -> saved
write SCR = 0x5A
read SCR -> observed
restore saved SCR
observed == 0x5A -> PROBE_MATCH
```

The probe produces realization evidence before initialization.

## Reference initialization

For the admitted 1.8432 MHz input clock:

```text
divisor = 1843200 / (16 * 115200) = 1

IER = 0x00
LCR = 0x80    # DLAB
DLL = 0x01
DLM = 0x00
LCR = 0x03    # 8N1
FCR = 0xC7    # FIFO enable, clear RX/TX, 14-byte trigger
MCR = 0x0B    # DTR, RTS, OUT2
```

## Bounded polling

TX readiness is `LSR.THRE` bit `0x20`.
RX readiness is `LSR.DR` bit `0x01`.

Each polling operation carries a caller-supplied finite `SPIN_BUDGET`.

```text
budget exhausted -> TIMEOUT
TX timeout -> no THR write
RX timeout -> no RBR consumption
```

## AUX adapter admission

A physical call is admitted only for an exact adapter grant binding:

```text
ADAPTER_ID
RESOURCE_BASE
OPERATION = AUX.TERM.RX | AUX.TERM.TX
SESSION / TRANSITION EVIDENCE
PNCAP ADMITTED
```

The physical byte stream produced by this adapter enters PNTERM L0 as ordered transport chunks.

## Current evidence

```text
GNU as x86_64 build        PASS
global adapter functions   6
ELF relocations            0
model conformance          30/30 PASS
physical execution         PENDING
emulator execution         PENDING
```

The object file is a host build witness. Repository authority remains the assembly source plus versioned conformance receipts.
