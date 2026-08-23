# Methods and scientific contract

## State variable

The workbench evolves the spatially averaged *intensity contrast*, not the complex focal-plane field. Exponential intensity decay is a compact surrogate for a well-behaved linear controller.

## Floor

The `Nact⁻⁴` scaling is an illustrative steep dependence on spatial degrees of freedom, chosen to make a controllability regime visible. It is not a universal DM law. The physical floor depends on influence functions, pupil geometry, dark-hole region, estimator covariance, model mismatch, bandwidth, and hardware.

## Observed series

The speckle estimate adds a decaying deterministic sinusoid to the envelope. It exists to distinguish estimated structure from the controller model without adding irreproducible randomness.

## Acceptance checks

- the controller envelope must be monotonic for non-negative gain;
- increasing actuator count must lower the coded floor at fixed parameters;
- zero gain must preserve initial contrast.

## Upgrade validation

A full implementation should verify energy normalization, conjugation conventions, Jacobian dimensions, regularisation sweep, probe observability, and broadband performance against a published benchmark before making instrument claims.
