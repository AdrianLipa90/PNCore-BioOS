# PNFS Authority and Permissions Contract v0.1

Status: `NORMATIVE CANDIDATE`

## 1. Authority model

PNFS SHALL distinguish read visibility, mutation authority, checkpoint publication authority, realization administration, and reclamation authority.

Initial authority classes:

```text
READ
WRITE_LIMINAL
PUBLISH_CHECKPOINT
MANAGE_REALIZATIONS
MANAGE_NAMESPACE
MANAGE_SNAPSHOTS
RECLAIM
ADMIN
```

## 2. Principal binding

Every namespace-visible PNODE MUST have an access policy that can resolve the requesting principal and requested operation to an authority decision.

The first FUSE implementation SHOULD map host UID/GID and mode/ACL information into the PNFS policy layer.

## 3. Mutation separation

Permission to append a candidate liminal segment does not by itself grant `PUBLISH_CHECKPOINT`.

Permission to manage physical realizations does not by itself grant logical content mutation authority.

Permission to remove a namespace path does not by itself grant immediate physical reclamation authority.

## 4. Checkpoint publication

`PUBLISH_CHECKPOINT` MUST require:

```text
valid parent checkpoint
valid liminal segment
valid commitments
satisfied durability policy
principal authorization
serialization/head-conflict success
```

## 5. Namespace mutation

Namespace create, bind, unlink, link and rename operations MUST be authorized against the affected directory/namespace policy before publication.

## 6. Snapshot and retention authority

Snapshot creation and deletion MUST require `MANAGE_SNAPSHOTS` or an explicitly equivalent delegated capability.

A retained snapshot or policy root may block reclamation even when a namespace binding has been removed.

## 7. Reclamation authority

Physical reclamation MUST require both:

```text
GC eligibility == RECLAIMABLE
principal/service authority includes RECLAIM
```

## 8. Service components

Internal PNFS services MAY operate under narrowly scoped service capabilities.

Recommended service scopes:

```text
recovery_service: read + validate + candidate reconstruction
placement_service: manage realizations
index_service: metadata/index candidate publication
GC_service: reachability scan + reclaim under policy
FUSE_service: delegated per-request principal context
```

## 9. Audit

Every authoritative mutation MUST record:

```text
principal or service identity
requested authority class
FILE_ID or namespace target
parent checkpoint / metadata generation where applicable
resulting identity or state
verdict
```

## 10. Fail-closed rule

Missing principal context, unresolved policy, invalid capability, stale authority token, or validator failure MUST deny the authoritative mutation.

The denial MUST be observable in structured logs or receipts.

## 11. Capability freshness

Long-lived handles or service capabilities MUST carry an authority-policy generation or equivalent freshness token.

A policy change MAY invalidate previously issued mutation capabilities.

## 12. Required error classes

```text
PNFS_AUTHORITY_DENIED
PNFS_PRINCIPAL_UNRESOLVED
PNFS_POLICY_STALE
PNFS_CAPABILITY_INVALID
PNFS_NAMESPACE_AUTHORITY_DENIED
PNFS_PUBLISH_AUTHORITY_DENIED
PNFS_RECLAIM_AUTHORITY_DENIED
```
