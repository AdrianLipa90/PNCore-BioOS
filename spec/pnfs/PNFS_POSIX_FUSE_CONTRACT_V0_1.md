# PNFS POSIX/FUSE Compatibility Contract v0.1

Status: `NORMATIVE CANDIDATE`

## 1. Deployment boundary

PNFS v0.x SHALL expose its first general filesystem surface through a userspace engine and FUSE-compatible adapter.

The initial stack is:

```text
application
-> POSIX/VFS call
-> FUSE adapter
-> PNFS engine
-> existing host filesystem
-> physical device
```

## 2. Namespace mapping

A POSIX path SHALL resolve through:

```text
path -> namespace entry -> FILE_ID -> PNODE
```

Rename and directory movement MUST update namespace bindings while preserving FILE_ID.

## 3. Open

`open()` MUST resolve the path, load or reconstruct the selected PNODE head, and validate the checkpoint required by the requested access mode.

Read-only open MAY use an already verified cached head when its freshness contract is satisfied.

## 4. Read

`read(offset, length)` is a compatibility projection over the logical content state selected by the open file handle.

The adapter MUST translate the byte range into the realization/index representation required to reconstruct the requested bytes.

A read handle SHOULD remain bound to one checkpoint unless the application explicitly opts into a live-head mode.

## 5. Write

POSIX writes SHALL map into PNFS liminal write transactions.

The adapter MUST preserve application write ordering required by the selected file handle semantics.

A successful write acknowledgement MUST correspond to an admitted candidate state according to the configured write-back policy.

## 6. fsync

`fsync()` is a durability barrier.

For the current file handle, `fsync()` MUST drive all admitted writes through:

```text
liminal seal
-> checkpoint crystallization
-> required physical realization persistence
-> durability-policy verification
-> head publication
```

Success MUST be returned only when the configured durability policy is satisfied.

## 7. close

`close()` MUST release the handle and surface any deferred write or persistence failure required by the active compatibility mode.

A close operation MAY trigger checkpoint crystallization according to policy, while `fsync()` remains the explicit durability barrier.

## 8. truncate

`truncate()` SHALL create a new logical content state and MUST preserve FILE_ID.

The resulting checkpoint MUST bind the new content commitment.

## 9. unlink

`unlink()` SHALL remove the selected namespace binding.

Object reclamation is governed by the PNFS retention/GC contract and reference state.

## 10. link and symlink

A hard-link-compatible operation SHALL create another namespace binding to the same FILE_ID where policy permits.

A symbolic-link-compatible operation SHALL create a PNODE relation of type `LINKS_TO` or an equivalent registered namespace-link object.

## 11. rename atomicity

A namespace rename within one PNFS namespace MUST be atomic from the perspective of namespace readers.

## 12. File handles

A file handle MUST bind at least:

```text
FILE_ID
opened checkpoint
access mode
write transaction identity when writable
namespace generation or equivalent freshness token
```

## 13. Error translation

PNFS internal failure classes MUST map deterministically to host-visible errno values while retaining the richer PNFS error in structured logs/receipts.

No PNFS validation error may be silently converted to success.

## 14. Initial exclusions from v0.1 compatibility guarantee

The v0.1 contract guarantees regular files, directories, rename, unlink, link projection, read, write, truncate, flush/close, and fsync semantics.

Additional special-node semantics SHALL be introduced by later explicit contracts.
