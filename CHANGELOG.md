# Changelog

## 0.4.0 (2026-10-22)

- Add offline tooling: `scripts/compare_oracle.py` (CPU-oracle comparison with
  finite/positivity/conservation invariants and JSON evidence reports),
  `scripts/check_evidence.py` (case-card lint), `scripts/validate.py` (repo
  self-checks) and the `scripts/probe_compute_node.sbatch` probe template.
- Add `assets/cases/` for measured porting case cards, with a template and
  lint-enforced evidence contract.
- Add unit tests (`tests/test_scripts.py`) and a cross-platform validate
  workflow.
- Add Claude Code plugin manifests and `scripts/install.sh` for Codex/Claude
  Code installation; the skill remains agent-neutral.

## 0.3.1 (2026-10-22)

- State the skill-role boundary: this is a porting/migration capability, not an
  application entry point; applications are authored with scnet-app and use
  scnet-hpc as the foundation.

## 0.3.0 (2026-10-22)

- Fold the reusable mature-application regression and same-basis performance
  checks from the retired standalone OneFLOW workflow into the porting playbook.
- Keep the capability abstract: CPU normal/strict oracles, target backend
  contract, separate build matrix, same-basis benchmark and explicit numeric
  comparison.

## 0.2.1 (2026-10-22)

- Condense the incremental version-migration guidance into a short checklist.

## 0.2.0 (2026-10-22)

- Add a version file.
- Add incremental version-migration guidance for mature applications, distinct
  from from-scratch kernel ports.
- Clarify user-level module naming, blank-account assumptions, local host
  platforms and MPI/transport revalidation.

## 0.1.0 (2026-10-19)

- Initial scientific DCU porting skill.
