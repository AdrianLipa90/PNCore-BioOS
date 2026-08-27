# BioOS <-> PNCS Resident Hot Path Binding v0.1

Status: IMPLEMENTED BINDING CANDIDATE / CHYBA / canon_allowed=false

## Source pin

Repository: `AdrianLipa90/PhaseNav-Natural-Coding-System`
Branch: `feat/pncs-v0.30-resident-hotpath`
Current source head at binding creation: `5e132141c503081f53791b73d9c9e24263891f4f`
Contract: `PNCS_RESIDENT_HOTPATH_V0_30`

The source branch contains implementation, native PNV witness, tests and a dedicated CI workflow. At binding creation GitHub had not yet produced a workflow run, therefore test promotion remains pending.

## Motivation from measured BioOS/Linux reference

The same-host 288-byte reference benchmark measured:

- BioOS direct `PHASENAV_HASH_BATCH`: 1.16939588 us median.
- BioOS full `Terminal36D.execute()`: 38.880157 us median.
- Linux native C SHA256: 0.508216 us median.
- Linux persistent pipe process: 26.514094 us median.
- Linux shared-mmap process: 37.462712 us median.
- Linux Unix-socket process: 38.055401 us median.
- Linux fork/exec `sha256sum`: 1981.076184 us median.

Reference receipt: `provenance/BIOOS_LINUX_HEAD_TO_HEAD_V0_1.json`, receipt SHA-256 `71660810c8685402271fa49afdf346e13c6529111ba2f7694df4f3f1454840ba`.

The optimization target is repeated authority reconstruction, not the 36D primitive itself.

## BioOS binding

```text
PNCore / PN Transition Spine
  -> PNCAP EXECUTE_PROGRAM
  -> PNCS v0.25 full resident admission
  -> PNCS v0.30 hot token
  -> live /dev/shm/ciel_noema guard
  -> resident control transition
  -> exact v0.20 execution receipt
  -> exact v0.22 inverse lineage
  -> content-addressed dispatch receipt
```

BioOS does not duplicate the PNCS implementation. PNCS remains execution authority; BioOS binds its capability/admission spine to the PNCS contract.

## Invalidation requirements

Any change in resident program, handle, active pointer, startpoint, CURRENT memory, fast-admission seal or operator-registry file identity invalidates the hot token. AUX/tether/AC heartbeat and PID checks remain per-dispatch. Token invalidation requires a fresh full admission; no static or automatic fallback is admitted.

## Promotion gate

This binding remains candidate until all are measured on one live generation:

```text
PNCS v0.30 tests PASS
v0.25 regression PASS
hot/full functional equivalence PASS
authority tamper invalidation PASS
heartbeat/generation invalidation PASS
p50 hot dispatch < v0.25 p50 admission/dispatch reference
no evidence-lineage regression
```

No main/canon promotion is performed by this binding.
