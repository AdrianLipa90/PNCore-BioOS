# GREMLIN Round 21 — Torsion Surface Writer Principal

Status: SUPPORTED_BY_DECLARED_TESTS
Epistemic: CHYBA
Canon allowed: false

Candidate:

```text
semantic writer principal
 -> exact PNCAP generation grant
 -> source-tick freshness
 -> active-head binding
 -> bounded derived path set
 -> single-use transition
 -> atomic publish contract
```

Critic requirements:
- host UID/GID is realization evidence, not semantic authority;
- no generic root authority;
- no parent traversal;
- no QHTRI source-channel writes;
- no AUX source-channel writes;
- stale tick/head/generation denies;
- transition replay denies;
- chmod/chown permission workaround remains denied.

Current live owner evidence is compatible with a future root-owned writer realization, but runtime writer installation is still pending.

GREMLIN has no execution or canon-promotion authority.
