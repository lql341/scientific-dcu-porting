---
name: scientific-dcu-porting
description: Plan, implement, validate, and document migrations of CFD/PDE/scientific-computing codes to Hygon DCU/DTK/HIP, using a CPU numerical oracle and target-compute-node evidence. Use for DCU porting, HIP migration, accelerator backend seams, or scientific-kernel validation; do not infer support for CUDA, Kokkos, or another cluster.
metadata:
  short-description: Port and validate scientific codes on Hygon DCU
---

# Scientific DCU Porting

Use this skill for CFD, PDE, finite-volume, finite-difference, finite-element, and other
scientific-computing migrations to Hygon DCU/DTK/HIP.

## Outcome

Produce a reproducible port with:

- a CPU reference/oracle and explicit numerical acceptance checks;
- a backend-neutral lifecycle seam where practical;
- target compute-node evidence for runtime, kernel, numerical, integration, and performance layers;
- sanitized engineering notes that separate measured facts from unverified capability.

## Workflow

1. Read the selected `scnet-hpc` cluster profile before choosing partition, memory, GRES, module, or architecture. Use the target compute node as the source of truth.
2. Establish or preserve a CPU oracle. Fix initial conditions, boundary conditions, timestep, iteration count, output precision, and deterministic comparison rules before optimizing.
3. Validate in increasing-cost layers: toolchain/runtime probe; minimal device kernel; one-step or one-stage numerical comparison; lifecycle reuse; NoTrace/FullTrace; MPI/device mapping; end-to-end performance.
4. Keep CPU and device implementations behind an explicit seam. Useful lifecycle operations include `CreateState`, `Upload`, `Advance`, `Download`, optional trace, and optional timing stats. Do not remove the CPU path while it is the oracle.
5. Check physical invariants in addition to elementwise error: finite values, positive density/pressure, conservation, boundary semantics, and stability/CFL assumptions.
6. Treat production and diagnostic data movement separately. FullTrace may copy intermediate arrays; NoTrace should keep state resident and minimize H2D/D2H and synchronization.
7. Make failures observable. Missing devices, HIP initialization errors, invalid API inputs, kernel/runtime errors, failed tests, and timeouts must propagate as nonzero workload and Slurm exit codes.
8. Compare both scheduler state and workload exit code. A skipped test, empty CTest discovery, warning-only output, or login-node package visibility is not validation success.
9. Record versions, target architecture, visible device count, test summary, resource tuple, and untested boundaries. Never commit credentials, internal hostnames, job IDs, private paths, or raw scheduler logs.

## DTK-specific cautions

- Resolve CMake/CTest/compiler paths before `module purge`, or load an explicit approved CMake module; DTK module setup can shadow a modern CMake with an old system binary.
- Set `CMAKE_HIP_ARCHITECTURES` from the target-node probe or cluster profile. Do not copy architecture assumptions from another cluster.
- Do not transfer upstream ROCm/CUDA claims about Triton, FP8/INT8, collectives, or kernel availability to DTK without a target-node probe.
- Use profile-generated Slurm resources and shared-storage job temp directories; do not invent GRES or memory tuples.

## References

Read [references/porting-playbook.md](references/porting-playbook.md) for the reusable
numerical, memory, build, test-registration, evidence, and scope checklist.

Use the `scnet-hpc` skill for SSH, Slurm, profile, module, and compute-node operations.
