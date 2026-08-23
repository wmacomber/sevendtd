# ADR 0006: Evidence-gated map projection

Accepted. Raw coordinates remain neutral. Mosaic tooling precedes projection. Coordinate math ships
only after recorded experiments and independent holdouts prove axis, sign, origin, span, zoom, and
boundary behavior.

Evidence gate passed for game `V 3.1.0 (b14)`, dashboard bundle SHA-256
`22c85370a43570f19b62f2f6cc24a753bfec6503c0c8c451c4c02d94356b36b1`, source-map SHA-256
`b5610c71218134c1c884a606596c4fe17794bf23a4700300cd1030d40dee7eb8`, tile size 128, native zooms
0–4, and map dimensions 6144×255×6144. Dashboard source establishes the candidate transform. Axis,
quadrant, negative-flooring, zoom-scaling, boundary, and six independent live observations confirm
it. Stale dashboard-marker samples and exact rendered-edge DOM hit tests are excluded and recorded
as measurement limitations.

`MapProjectionSpec` stores configuration and evidence identity. `MapNamespace.projection()` returns
the projection only for `mapBlockSize=128` and `maxZoom=4`; unsupported configurations fail while
raw tile access remains available. Pixel mapping, cache semantics, and unexplored/out-of-bounds
classification remain deferred.
