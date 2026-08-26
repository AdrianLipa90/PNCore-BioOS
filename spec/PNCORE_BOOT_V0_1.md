# PNCore Boot v0.1

Status: ARCHITECTURE CANDIDATE

## Boot boundary

The physical CPU begins in architecture-defined reset state. The architecture bootstrap has one job: establish the minimum execution environment required to enter the native PNCore admission path.

For x86_64 the bootstrap candidate is limited to:

```text
reset entry
 -> deterministic CPU mode setup
 -> minimal memory map / stack
 -> locate PNStore bootstrap extent
 -> verify bootstrap identity
 -> transfer to PNCore entry realization
```

## Semantic boot

Once PNCore is reachable:

```text
IDENTITY
 -> DOMAIN
 -> AUTHORITY
 -> REQUEST
 -> COUPLING
 -> ADMISSION
 -> mount/recover PNStore
 -> establish PNFS root view
 -> resolve Genesis.pnv
 -> admit Genesis program
 -> execute Genesis transition schedule
 -> Sigma_0
```

The Triple Pulse prefix is reused unchanged.

## No hidden fallback

If PNStore current generation, Genesis identity, admission evidence or required architecture realization does not verify, boot stops fail-closed.
