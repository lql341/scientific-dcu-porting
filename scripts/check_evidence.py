#!/usr/bin/env python3
"""Lint porting case cards in assets/cases/ (offline, stdlib only).

A case card records one measured port or migration. The required fields are
exactly the evidence contract from SKILL.md step 9 and the playbook's
"Evidence and scope" section. Cards record measured facts only: private
paths, job IDs and internal hostnames are hard errors, matching the
"never commit credentials/job IDs/private paths" rule.

Files whose name starts with "_" (e.g. _template.json) are parsed but not
field-checked. Exit code is nonzero on any error.
"""

import argparse
import json
import pathlib
import re
import sys

SCHEMA_VERSION = 1
EVIDENCE_LEVELS = ("device-visible", "backend-selected", "stage-on-device")
NODE_CONTEXTS = ("compute-node", "login-node")

REQUIRED_STRING = (
    "application",
    "upstream_version",
    "dtk_version",
    "target_arch",
    "test_summary",
    "tolerance_baseline",
)
REQUIRED = REQUIRED_STRING + (
    "node_context",       # compute-node | login-node
    "visible_devices",    # non-negative int
    "resource_tuple",     # non-empty dict or string
    "evidence_level",     # device-visible | backend-selected | stage-on-device
    "untested_boundaries"  # list of strings, may be empty
)

PRIVATE_PATH = re.compile(r"/public/home/|/home/[A-Za-z0-9_.-]+/")
FORBIDDEN_KEY = re.compile(r"(^|_)(job_?id|slurm_?job|hostname)($|_)", re.IGNORECASE)

# A tolerance baseline must cite a measured numeric limit tied to an error
# metric (e.g. 'max_rel=2e-12 over 500 steps, CPU oracle gcc build'). A
# baseline without a number is an unmeasured - and therefore self-set -
# threshold, which the playbook forbids.
TOLERANCE_METRIC = re.compile(
    r"(atol|rtol|max_?(abs|rel)|rel_?error|tolerance)\S*\s*[=:≤<]?\s*\d"
    r"|\d+(\.\d+)?[eE][+-]?\d+")
SELF_SET_WORDS = re.compile(
    r"\b(tbd|todo|guess(?:ed)?|assum(?:ed|ption)|self[- ]?set|arbitrary)\b",
    re.IGNORECASE)

errors = []
warnings = []


def scan_strings(value, trail, where):
    """Recursively forbid private data inside any string value or key."""
    if isinstance(value, dict):
        for key, sub in value.items():
            if FORBIDDEN_KEY.search(str(key)):
                errors.append("%s: forbidden key %r (job IDs/hosts stay out of cards)"
                              % (where, key))
            scan_strings(sub, trail + "." + str(key), where)
    elif isinstance(value, list):
        for i, sub in enumerate(value):
            scan_strings(sub, "%s[%d]" % (trail, i), where)
    elif isinstance(value, str):
        if PRIVATE_PATH.search(value):
            errors.append("%s: %s leaks a private path" % (where, trail))


def check_card(path):
    where = path.name
    try:
        card = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append("%s: does not parse: %s" % (where, exc))
        return
    if not isinstance(card, dict):
        errors.append("%s: card must be a JSON object" % where)
        return

    if path.name.startswith("_"):
        return  # template: parse check only

    if card.get("schema_version") != SCHEMA_VERSION:
        errors.append("%s: schema_version must be %d, got %r"
                      % (where, SCHEMA_VERSION, card.get("schema_version")))

    for field in REQUIRED:
        if field not in card:
            errors.append("%s: missing required field %r" % (where, field))
    for field in REQUIRED_STRING:
        if field in card and not (isinstance(card[field], str) and card[field].strip()):
            errors.append("%s: field %r must be a non-empty string" % (where, field))

    if "node_context" in card and card["node_context"] not in NODE_CONTEXTS:
        errors.append("%s: node_context must be one of %s, got %r"
                      % (where, "/".join(NODE_CONTEXTS), card["node_context"]))
    if "evidence_level" in card and card["evidence_level"] not in EVIDENCE_LEVELS:
        errors.append("%s: evidence_level must be one of %s, got %r"
                      % (where, "/".join(EVIDENCE_LEVELS), card["evidence_level"]))
    if "visible_devices" in card:
        devices = card["visible_devices"]
        if not isinstance(devices, int) or isinstance(devices, bool) or devices < 0:
            errors.append("%s: visible_devices must be a non-negative integer" % where)
    if "resource_tuple" in card:
        rt = card["resource_tuple"]
        if not rt or not isinstance(rt, (dict, str)):
            errors.append("%s: resource_tuple must be a non-empty object or string" % where)
    if "untested_boundaries" in card:
        ub = card["untested_boundaries"]
        if not isinstance(ub, list) or any(not isinstance(x, str) for x in ub):
            errors.append("%s: untested_boundaries must be a list of strings" % where)

    if card.get("node_context") == "login-node" and \
            card.get("evidence_level") == "stage-on-device":
        errors.append("%s: stage-on-device evidence cannot come from a login node" % where)

    baseline = card.get("tolerance_baseline")
    if isinstance(baseline, str) and baseline.strip():
        if SELF_SET_WORDS.search(baseline):
            errors.append("%s: tolerance_baseline reads as self-set/unmeasured: %r"
                          % (where, baseline))
        elif not TOLERANCE_METRIC.search(baseline):
            errors.append("%s: tolerance_baseline has no measured numeric limit "
                          "tied to an error metric: %r" % (where, baseline))

    scan_strings(card, "$", where)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=pathlib.Path,
                        default=pathlib.Path(__file__).resolve().parent.parent,
                        help="skill repository root (default: parent of scripts/)")
    args = parser.parse_args(argv)

    cases = args.root / "assets" / "cases"
    if not cases.is_dir():
        warnings.append("assets/cases/ does not exist; nothing to lint")
    else:
        cards = sorted(cases.glob("*.json"))
        if not cards:
            warnings.append("assets/cases/ has no .json cards")
        for path in cards:
            check_card(path)

    for msg in warnings:
        print("WARN: %s" % msg)
    for msg in errors:
        print("ERROR: %s" % msg)
    if errors:
        print("evidence lint: %d error(s), %d warning(s)" % (len(errors), len(warnings)))
        return 1
    print("evidence lint: ok (%d warning(s))" % len(warnings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
