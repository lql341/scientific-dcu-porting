# Scientific DCU Porting

A reusable Codex skill and engineering playbook for porting CFD, PDE, and other scientific-computing codes to Hygon DCU/DTK/HIP.

## Contents

- `SKILL.md` — the Codex skill entry point.
- `references/porting-playbook.md` — the numerical, runtime, memory, testing, evidence, and scope checklist.
- `agents/openai.yaml` — UI metadata for skill discovery.

## Use

Install or copy this repository as a Codex skill package, then invoke it explicitly with `$scientific-dcu-porting`. Use the `scnet-hpc` skill alongside it for cluster profiles, Slurm, SSH, modules, and compute-node operations.

The guidance is intentionally evidence-driven: preserve a CPU numerical oracle, validate on the target compute node, separate diagnostic and production data paths, and keep unverified accelerator capabilities clearly marked.
