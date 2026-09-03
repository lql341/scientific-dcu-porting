# Scientific DCU porting checklist

## Numerical contract

- Define a small deterministic case before a production case.
- Compare every meaningful intermediate (stage state, face state, flux, residual) when debugging.
- Use absolute and scaled relative error; add ULP only when it helps diagnose floating-point drift.
- Check finite values, positivity, conservation, boundary conditions, and stability constraints.
- Keep a final-state checksum/hash as an integration signal, not as the only correctness proof.

## Memory and execution structure

- Map all arrays and temporaries before writing kernels.
- Prefer SoA or another layout that matches the dominant access pattern, but preserve semantics first.
- Allocate persistent device state once; upload once; advance many steps; download only required outputs.
- Separate FullTrace/diagnostic mode from NoTrace/production mode.
- Count kernel launches, synchronizations, allocations, H2D, and D2H transfers.

## Build and runtime

- Probe the actual compute node: compiler, CMake, HIP runtime, architecture, visible devices, and a minimal kernel.
- Resolve absolute tool paths before `module purge` because module setup may shadow CMake.
- Configure explicitly with the project’s HIP and test options and the target architecture.
- Use the cluster profile to derive partition, CPU, memory, GRES, and timeout.
- Make the batch script return the workload rc and inspect Slurm State plus ExitCode.

## Test registration

- Run the test executable directly when CTest discovery is unreliable, and parse the expected GoogleTest summary.
- Treat `No tests were found!` with exit code 0 as a failure of the validation harness.
- Allow backend-specific test counts; a HIP device-visibility test may add one test.
- Run CPU tests in normal CI; run HIP tests on target nodes for HIP changes, scheduled checks, or release gates.

## Evidence and scope

Record toolchain versions, architecture, visible device count, resource tuple, test summary,
and untested boundaries. Distinguish login-node observations from compute-node evidence.
Keep raw logs and private identifiers outside maintained public reports.

Do not claim full CFD GPU completion from an isolated Euler port. Extend only after the
small-kernel, lifecycle, residual, MPI/halo, and performance gates pass.
