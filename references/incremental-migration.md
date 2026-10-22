# Incremental version migration

This is for a mature application moving from one installed version to the next.
It is not a from-scratch kernel port. The application, numerical method and most
of the runtime already exist; the work is to prove that the new target preserves
them.

## Treat the upgrade as a new target

- Keep one user-level module per application version; encode backend version and
  target in the name (for example `dtk26.04-z100`). Backend/MPI variants are
  profiles, not new module names.
- Pin the expected application version and fail early on mismatch.
- Keep the old module and evidence until the new candidate passes all gates.
- Do not silently replace a working target with an unverified build.

## Separate build compatibility from application behaviour

A version upgrade often fails first in the build environment, not in the
application:

- compiler vs device-compiler header/ABI compatibility;
- CMake find/try-compile paths for device SDK components;
- FFT, MPI, accelerator runtime and architecture flags;
- launcher and MPI transport configuration.

Record these as build-environment findings. A compiler/CMake failure is not
evidence that the new application version is wrong, and a successful build is not
application correctness.

## Re-run the same oracle, then re-baseline

- Reuse the same CPU oracle, inputs, time/iteration grid and comparison terms.
- Check finite values, physical invariants and stage-specific energy/numerical
  terms.
- Re-baseline tolerances only from measured values with a written rationale.
- Do not widen tolerances just to make a new version pass.

## Revalidate execution evidence

A version string or successful launch is insufficient:

- device visible;
- backend selected for the run;
- specific compute stage executed on the device (for example PME/offload);
- requested rank, PME-rank and GPU counts actually observed.

Re-run multi-rank, PME decomposition, multi-GPU and multi-node paths that matter
for the intended use.

## Revalidate MPI and transport separately

Version migration can expose environment issues that look like application
regressions:

- Slurm PMIx/MPI launcher type and balanced `--ntasks-per-node`;
- HCOLL disabled when it fails or regresses;
- UCX HCA/interface selection kept profile-driven;
- PMPI/OB1/TCP treated as a compatibility fallback, not the default.

Record launcher, transport, rank/GPU topology and allocation with any multi-node
result. Do not attribute a transport failure to the application version without
isolating it.

## Performance and scope

- A newer version does not imply better performance.
- Small and mid-size systems can show negative or sublinear multi-GPU scaling;
  report the measured reason instead of treating non-linearity as a defect.
- Detecting GPU-aware MPI is not a performance result; measure direct versus
  host-staged communication.
- State the untested boundaries: larger systems, more nodes/GPUs, production
  accuracy and other fabrics.

## Minimum checklist

1. Record source revision, build options, patches, compiler/DTK/MPI/FFT versions.
2. Pin the expected module/version and target architecture.
3. Build the candidate in an isolated prefix; use a private module path if needed.
4. Re-run the CPU oracle and the same comparison cases.
5. Revalidate device-stage, rank, PME-rank and GPU-count evidence.
6. Revalidate multi-rank and multi-node transport separately.
7. Re-baseline tolerances only from measured data.
8. Keep old evidence; publish a coverage matrix with explicit boundaries.
