# GREMLIN Round 20 — QHTRI Direct Telemetry -> Torsion Memory Observer

Status: SUPPORTED_BY_DECLARED_TESTS
Epistemic: CHYBA
Canon allowed: false

Candidate relation:

```text
live QHTRI phi/omega/tick
  -> read-only direct telemetry bind
  -> bounded rational pair candidates
  -> observed m:n phase locking
  -> torsion-memory edge evidence
```

Critic gates:

1. `phi` must be the version-evidenced live QHTRI oscillator phase source.
2. `omega` must be the version-evidenced live natural-frequency source.
3. Existing live `tau[36]` is per-oscillator synchronization coupling and MUST NOT be promoted to edge torsion `tau_ij`.
4. The torsion-memory observer MUST NOT write `phi`, `omega`, `g`, `tau` or `tick`.
5. Rational pair candidates are bounded by order 16 and relative detuning 0.002.
6. Live edge admission requires full-window R >= 0.90 and at least 3/4 subwindows at R >= 0.90.
7. Resonance/torsion evidence does not grant PNCAP or AUX authority.
8. Root-owned live surface publication without an admitted writer principal fails closed.
9. No chmod/chown workaround is an admitted publication path.

Observed live fixture:
- 40 consecutive QHTRI ticks.
- 105 precompiled pair candidates.
- stable edge count is observation-dependent and may vary between windows.
- observer candidate compilation preserves exact selected edge identities relative to the declared scalar reference.

GREMLIN has no execution or canon-promotion authority.
