# PN Clock / x86 TSC-Deadline Realization v0.1

Status: ARCHITECTURE CANDIDATE / FAIL-CLOSED CLOCK ADMISSION

Base scheduler frequency:

```text
f0 = 7.83 Hz = 783/100 Hz
T0 = 100/783 s
```

The preferred x86 realization uses one invariant TSC timeline and absolute TSC-deadline events. It is admitted only when the hardware explicitly provides TSC, TSC-deadline, invariant-TSC semantics, and a complete CPUID.15 denominator/numerator/crystal-frequency tuple.

No CPU base-MHz estimate is accepted as clock authority.

## Exact rational mapping

For CPUID.15 values:

```text
d = denominator
u = numerator
c = nominal crystal frequency in Hz
```

TSC frequency is represented as the rational `c*u/d`. The BioOS base period is therefore represented without floating point as:

```text
N = c * u * 100
D = d * 783
offset(n) = floor(n * N / D)
deadline(n) = base_tsc + offset(n)
```

The tick index `n` is the phase coordinate. There is no independent timer per scheduler band.

## No-catch-up rule

Given current TSC value `now`, the next logical tick is computed directly:

```text
n_next = floor((now - base_tsc) * D / N) + 1
```

The physical deadline is then `deadline(n_next)`. If integer flooring lands exactly on `now`, `n_next` is advanced once.

This directly skips missed phase windows. Missed ticks are counted as evidence but are never replayed as a burst.

## Clock-source admission

Preferred source candidate:

```text
TSC_DEADLINE_EXACT
  requires TSC
  requires TSC-deadline capability
  requires invariant TSC
  requires CPUID.15 d != 0, u != 0, c != 0
```

Fallback candidates remain separate future realizations:

```text
HPET_ABSOLUTE
APIC_ONESHOT_CALIBRATED
```

A missing exact source leaves timed admission quiet rather than silently estimating a frequency.

## Jitter evidence

For an armed deadline `D_n` and interrupt-observed timestamp `T_n`:

```text
J_n = T_n - D_n
```

The state records the latest signed jitter, maximum absolute jitter, current phase index, and total skipped windows.

Jitter evidence may later drive bounded demotion `B_k -> B_{k+1}`. It does not grant authority to promote a task to a faster band.
