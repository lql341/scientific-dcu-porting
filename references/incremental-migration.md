# Incremental version migration

A mature application moving to a new version is a new deployment target, not a
from-scratch kernel port.

- **One module per version**, with backend/target in the name (for example
  `dtk26.04-z100`). Backend/MPI variants are profiles, not new modules.
- **Pin the expected version** and keep the old module/evidence until the new
  candidate passes.
- **Separate build environment from application behaviour**: compiler/device
  compiler headers, CMake try-compile paths, FFT/MPI/DTK/architecture flags. A
  build failure is not an application regression.
- **Reuse the CPU oracle** and the same inputs/time/iteration grid. Re-baseline
  tolerances only from measured values; do not widen them silently.
- **Revalidate execution evidence**: device visible → backend selected →
  specific stage executed; observed ranks, PME ranks, GPU counts and topology.
- **Revalidate MPI/transport separately**: PMIx/launcher type, balanced
  `--ntasks-per-node`, HCOLL off when it fails or regresses, profile-driven UCX
  HCA/interface, PMPI/OB1 only as fallback. Do not blame the application version
  for a transport failure.
- **Performance is not implied**: small/mid systems may be sublinear; measure
  direct versus host-staged communication and state the untested boundaries.
- **Record** source/build options/module/target/coverage; keep private logs and
  paths out of public reports.

Checklist: source/build record, expected version, isolated build, same oracle,
execution evidence, transport check, measured tolerance, coverage boundaries.
