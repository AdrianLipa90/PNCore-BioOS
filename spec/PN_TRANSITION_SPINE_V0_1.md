# PN Transition Spine v0.1

Status: ARCHITECTURE CANDIDATE

## Purpose

Define one reusable transition shape for boot, execution, persistence, object mutation and recovery without collapsing their domain-specific semantics.

## Spine

```text
IDENTITY -----> GATE
                  ^
ENVIRONMENT ----->|
AUTHORITY -------->|
REQUEST -> COUPLING|
ENVIRONMENT -> COUPLING
COUPLING --------->GATE

GATE --ADMITS--> TRANSITION
TRANSITION --PRODUCES--> STATE
TRANSITION --RECEIPTED_BY--> EVIDENCE
STATE --EVIDENCED_BY--> EVIDENCE
IDENTITY --IDENTIFIES--> STATE
ENVIRONMENT --GENERATES--> STATE
```

## Canonical transition tuple

```text
T = (
  identity,
  environment,
  authority,
  request,
  coupling,
  admission,
  state_before,
  operator_schedule,
  state_after,
  evidence
)
```

`state_after` is immutable after admission. A later change creates a new generation.

## Domain specialization

Execution may realize TRANSITION as a KAKU schedule. Persistence may realize TRANSITION as append + COMMIT + HEAD advance. Boot may realize TRANSITION as admitted hardware/runtime state construction. PNFS may realize TRANSITION as creation of a new PNObject generation.

These transition realizations retain distinct contracts while sharing the same structural spine.

## Failure rule

Any mismatch among identity, environment generation, authority, coupling, admitted request or resulting evidence fails closed before promotion of `state_after` to current.
