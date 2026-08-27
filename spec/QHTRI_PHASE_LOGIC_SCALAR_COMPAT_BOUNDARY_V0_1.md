# QHTRI Phase Logic vs Scalar Compatibility Algebra v0.1

Status: AUDITED DISTINCTION / EPISTEMIC CHYBA / canon_allowed=false
Source: GREMLIN candidate scan + BELZEBUB counterexample

## Native QHTRI logic

Native relational logic is defined by phase geometry:

```text
C(delta) = (1+cos(delta))/2
NOT_PHASE(theta) = wrap(theta+pi)
XNOR_PHASE(a,b) = C(theta_a-theta_b)
XOR_PHASE(a,b) = 1-C(theta_a-theta_b)
```

This is the execution-facing logic for QHTRI.

## Scalar compatibility/gain algebra

The existing continuous scalar operators remain useful for admission and compatibility:

```text
AND_SCALAR(a,b) = ab
OR_SCALAR(a,b)  = a+b-ab
NOT_SCALAR(a)   = 1-a
XOR_SCALAR(a,b) = a+b-2ab
```

They reproduce Boolean truth tables exactly at `a,b in {0,1}`.

## Audit distinction

When scalar activations are derived independently from absolute phase coherence,

```text
a=C(theta_a)
b=C(theta_b)
```

then in general

```text
XOR_SCALAR(a,b) != XOR_PHASE(theta_a,theta_b).
```

Counterexample:

```text
theta_a=0.2
theta_b=1.1
XOR_SCALAR=0.27772280077618694
XOR_PHASE =0.1891950158646678
```

Therefore `XOR_SCALAR` is retained only as scalar compatibility/gain algebra. It does not identify the native QHTRI relational XOR away from the binary boundary.

## Compiler rule

```text
phase relation requested -> use XOR_PHASE / XNOR_PHASE / NOT_PHASE
admission/gain composition -> use scalar t-norm/t-conorm algebra
binary external adapter -> either representation may be projected after declared threshold/encoding
```

This distinction prevents a semantic collapse between relational phase geometry and independent scalar confidence channels.
