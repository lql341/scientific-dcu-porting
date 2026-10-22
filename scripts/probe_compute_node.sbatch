#!/bin/bash
# Target-compute-node probe for DCU porting (template).
#
# Fill every <PLACEHOLDER> from the scnet-hpc cluster profile
# (clusters/<cluster>.conf). Never invent partition, GRES or memory values;
# use the profile or the live scheduler as the source of truth. This probe
# consumes scheduler resources: run it only when target-node evidence is
# required. Submit via scnet-hpc, not by hand, unless operating interactively.
#
#SBATCH --job-name=dcu-porting-probe
#SBATCH --partition=<PARTITION_FROM_PROFILE>
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=<CPUS_FROM_PROFILE>
#SBATCH --gres=<DCU_GRES_FROM_PROFILE>   # e.g. dcu:1
#SBATCH --time=00:10:00
#SBATCH --output=probe-%j.out

set -euo pipefail

# Load the site DTK toolchain from the profile; resolve tool paths BEFORE any
# later module purge, because DTK module setup can shadow a modern CMake with
# an old system binary. Fill this from the cluster profile, not from memory.
DTK_MODULE="<DTK_MODULE_FROM_PROFILE>"
module load "$DTK_MODULE"

emit() { echo "PROBE:$1=$2"; }

emit slurm_job_id "${SLURM_JOB_ID:-interactive}"
emit node_context compute-node
emit cmake_path "$(command -v cmake || echo MISSING)"
emit cmake_version "$(cmake --version 2>/dev/null | head -1 || echo MISSING)"
emit hipcc_path "$(command -v hipcc || echo MISSING)"
emit hipcc_version "$(hipcc --version 2>/dev/null | head -1 || echo MISSING)"

# Target architecture: derive CMAKE_HIP_ARCHITECTURES from the device itself,
# never copied from another cluster's profile.
arch="$(rocminfo 2>/dev/null | grep -o 'gfx[0-9a-f]*' | sort -u | paste -sd';' -)"
emit gfx_arch "${arch:-MISSING}"
emit cmake_hip_architectures "${arch:-MISSING}"

devices="$(rocminfo 2>/dev/null | grep -c 'gfx[0-9a-f]' || true)"
emit visible_devices "${devices:-0}"

# Minimal device-kernel evidence: compile and run a trivial HIP program so
# "device visible" is backed by an executed kernel, not an import success.
work="$(mktemp -d)"
cat > "$work/probe.hip" <<'EOF'
#include <hip/hip_runtime.h>
#include <cstdio>
__global__ void add_one(float* x) { x[threadIdx.x] += 1.0f; }
int main() {
    float* d = nullptr;
    if (hipMalloc(&d, 4 * sizeof(float)) != hipSuccess) return 1;
    add_one<<<1, 4>>>(d);
    if (hipDeviceSynchronize() != hipSuccess) return 2;
    float h[4];
    if (hipMemcpy(h, d, sizeof(h), hipMemcpyDeviceToHost) != hipSuccess) return 3;
    hipFree(d);
    std::printf("kernel_ok %.1f\n", h[0]);
    return 0;
}
EOF
if hipcc "$work/probe.hip" -o "$work/probe" --offload-arch="${arch%%;*}" 2>"$work/build.log"; then
    if "$work/probe"; then
        emit minimal_kernel ok
    else
        emit minimal_kernel "run_failed rc=$?"
        exit 1
    fi
else
    emit minimal_kernel build_failed
    cat "$work/build.log" >&2
    exit 1
fi
rm -rf "$work"
