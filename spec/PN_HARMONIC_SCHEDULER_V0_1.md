# PN Harmonic Scheduler v0.1

Status: ARCHITECTURE_CANDIDATE / HOST_BUILD_VALIDATED
Epistemic operator: CHYBA
Canon promotion: explicit authority only

## Base clock

The scheduler uses one base tick source:

```text
f0 = 7.83 Hz
T0 = 1/f0 = 127.7139208173691 ms
```

B0 is a bounded service lane evaluated on every base tick. It is not part of the mutually-exclusive admission partition.

## Dyadic admission partition

For every positive base-tick index n, define

```text
band(n) = 1 + nu2(n) = 1 + ctz(n)
```

where `nu2(n)` is the exponent of the largest power of two dividing n.

Therefore:

```text
B1: n = 1 mod 2
B2: n = 2 mod 4
B3: n = 4 mod 8
B4: n = 8 mod 16
B5: n = 16 mod 32
B6: n = 32 mod 64
B7: n = 64 mod 128
```

The classes B1..B7 are pairwise disjoint. Ticks with `nu2(n) >= 7` are RESERVED_QUIET in v0.1 and may be admitted by a later explicit band extension.

## Frequencies

```text
B0  7.830000000 Hz    127.713920817 ms   bounded service lane
B1  3.915000000 Hz    255.427841635 ms   queue/admission/light I/O
B2  1.957500000 Hz    510.855683269 ms   GREMLIN microstep/candidate
B3  0.978750000 Hz   1021.711366539 ms   critic/relational graph
B4  0.489375000 Hz   2043.422733078 ms   bounded numerics/slices
B5  0.244687500 Hz   4086.845466156 ms   bounded persistence/Git serialization
B6  0.122343750 Hz   8173.690932312 ms   bounded visualisation
B7  0.061171875 Hz  16347.381864623 ms   bounded heavy build/package
```

These are admission windows, not commands to execute periodically. An empty queue produces no work.

## Non-burst rules

```text
MISSED_WINDOW -> SKIP
RUNNING        -> SKIP
CATCH_UP       -> DENY
```

A task is never replayed merely because one or more prior windows were missed.

## Jitter / overload demotion candidate

A task may be demoted from Bk to B(k+1) only by explicit scheduler policy when its measured start jitter or execution overrun exceeds the configured bound. Promotion/demotion policy must use hysteresis and deterministic evidence; one isolated spike does not self-promote a policy decision.

```text
OVERLOAD_CONFIRMED(Bk) -> DEMOTE(Bk, Bk+1)
```

No scheduler task may self-promote to a faster band.

## O(1) physical selector

The x86_64 realization uses one monotonic tick counter and one trailing-zero selection operation. It does not instantiate seven independent periodic timers.

```text
n -> BSF/TZCNT -> 1+ctz(n) -> admission class
```

B0 service work is independently bounded and occurs before/alongside band selection under a fixed service budget.

## Evidence boundary

The current v0.1 implementation proves only deterministic classification and host-build integration. Timer interrupt delivery and measured real-time jitter remain separate runtime gates.
