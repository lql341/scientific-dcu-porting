# Scientific DCU Porting

Version: 0.4.1

A reusable, agent-neutral skill and engineering playbook for porting CFD, PDE, and other scientific-computing codes to Hygon DCU/DTK/HIP. It works with any agent that supports the standard skill convention (Codex, Claude Code, and others).

This is a porting/migration capability, not an application entry point. Application
skills are authored with `scnet-app`, use `scnet-hpc` as the foundation, and remain
the single skill users load for normal workload execution.

## Contents

- `SKILL.md` — the skill entry point.
- `references/porting-playbook.md` — the numerical, runtime, memory, testing, evidence, and scope checklist, including mature-application regression checks folded in from the retired OneFLOW workflow.
- `references/incremental-migration.md` — how to migrate a mature application to a new version without treating it as a from-scratch port.
- `scripts/compare_oracle.py` — offline CPU-oracle vs device comparison (text or .npy) with finite/positivity/conservation invariants and a JSON evidence report.
- `scripts/check_evidence.py` — lints porting case cards in `assets/cases/` against the evidence contract.
- `scripts/validate.py` — offline repository self-checks.
- `scripts/probe_compute_node.sbatch` — target-compute-node probe template (toolchain, gfx architecture, minimal HIP kernel).
- `scripts/install.sh` — idempotent installer for Codex and Claude Code skill directories (`--codex`, `--claude`, `--project`, `--link`).
- `assets/cases/` — measured porting case cards; see its README and `_template.json`.
- `agents/openai.yaml` — Codex UI metadata; `.claude-plugin/` — Claude Code plugin manifests.
- `tests/` — unit tests; `.github/workflows/validate.yml` — cross-platform CI.

## Use

Install with `scripts/install.sh` (Codex or Claude Code), add the repository as a Claude Code marketplace plugin via `.claude-plugin/`, or copy the repository into any agent's skill directory. Invoke it explicitly with `$scientific-dcu-porting` or the agent's equivalent. Use the `scnet-hpc` skill alongside it for cluster profiles, Slurm, SSH, modules, and compute-node operations.

Validate a clone offline with:

```bash
python3 scripts/validate.py && python3 scripts/check_evidence.py && python3 -m unittest discover -s tests
```

The guidance is intentionally evidence-driven: preserve a CPU numerical oracle, validate on the target compute node, separate diagnostic and production data paths, and keep unverified accelerator capabilities clearly marked.
