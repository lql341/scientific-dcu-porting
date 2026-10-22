# Porting case cards

One JSON card per measured port or version migration. Cards are the skill's
accumulated evidence base: they let a later run reuse measured tolerance
baselines and known-good toolchain combinations instead of re-deriving them.

Rules:

- Copy `_template.json`, fill every field, name the file
  `<application>-<version>-<arch>.json` (files starting with `_` are
  parse-checked only).
- Record **measured facts from the target compute node** only. Login-node
  observations set `node_context: "login-node"` and can never claim
  `evidence_level: "stage-on-device"` — the linter rejects that combination.
- `evidence_level` is the highest level actually observed:
  `device-visible` < `backend-selected` < `stage-on-device`.
- Re-baseline `tolerance_baseline` only from measured values with a written
  rationale (see references/porting-playbook.md). The linter requires the
  field to cite a numeric limit tied to an error metric (e.g.
  `max_rel=2e-12, CPU oracle same grid`) and rejects self-set or unmeasured
  baselines; a surrogate result passed against a threshold you invented is
  not evidence.
- Never commit job IDs, node names, private paths or credentials. The linter
  blocks these.
- A card does not extend to other applications, versions, precisions or
  clusters; say so in `untested_boundaries`.

Lint with:

```bash
python3 scripts/check_evidence.py
```
