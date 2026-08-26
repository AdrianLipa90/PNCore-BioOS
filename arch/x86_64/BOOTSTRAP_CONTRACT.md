# x86_64 Bootstrap Contract v0.1

Status: PHYSICAL BACKEND CANDIDATE

This layer is intentionally tiny. It is the unavoidable translation boundary between x86_64 reset semantics and PNCore native semantics.

Required outputs to PNCore:

```text
CPU_MODE = LONG_MODE
BOOT_MEMORY_MAP = verified map/reference
PNSTORE_BOOT_EXTENT = located extent/reference
ARCH_REALIZATION_ID = content identity of PNCore physical realization
BOOT_EVIDENCE = digest over exact handoff inputs
```

The bootstrap must not implement PNFS policy, process scheduling, user identity policy or general device management.

The physical realization is distinct from `.pnv` program semantic identity.
