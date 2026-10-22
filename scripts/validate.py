#!/usr/bin/env python3
"""Cross-platform static validation for this skill repository.

Offline checks only; nothing here contacts a cluster:
1. SKILL.md frontmatter carries the expected name and a description.
2. Local Markdown links resolve to existing files.
3. VERSION matches .claude-plugin/plugin.json and has a CHANGELOG entry.
4. No private paths or private keys in committed text files.

Exit code is nonzero on any error.
"""

import argparse
import json
import pathlib
import re
import sys

SKILL_NAME = "scientific-dcu-porting"
PRIVATE_PATH = re.compile(r"/public/home/|/home/[A-Za-z0-9_.-]+/")
PRIVATE_KEY = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
TEXT_SUFFIXES = {".md", ".py", ".sh", ".sbatch", ".json", ".yaml", ".yml", ".txt", ".conf"}
SKIP_DIRS = {".git", "__pycache__", ".claude"}
# Scanner sources contain the private-path pattern literally; never scan them.
SCANNER_FILES = {"validate.py", "check_evidence.py"}

errors = []


def check_frontmatter(root):
    skill = root / "SKILL.md"
    if not skill.is_file():
        errors.append("SKILL.md is missing")
        return
    text = skill.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        errors.append("SKILL.md has no YAML frontmatter block")
        return
    fm = match.group(1)
    if not re.search(r"^name:\s*%s\s*$" % re.escape(SKILL_NAME), fm, re.MULTILINE):
        errors.append("SKILL.md frontmatter name must be %r" % SKILL_NAME)
    if not re.search(r"^description:\s*\S", fm, re.MULTILINE):
        errors.append("SKILL.md frontmatter needs a non-empty description")


def check_links(root):
    for md in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRS for part in md.parts):
            continue
        text = md.read_text(encoding="utf-8", errors="replace")
        for target in MD_LINK.findall(text):
            target = target.split("#", 1)[0].strip()
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            if not (md.parent / target).exists():
                errors.append("%s: broken link %r" % (md.relative_to(root), target))


def check_versions(root):
    version_file = root / "VERSION"
    if not version_file.is_file():
        errors.append("VERSION is missing")
        return
    version = version_file.read_text(encoding="utf-8").strip()
    if not version:
        errors.append("VERSION is empty")
        return

    plugin = root / ".claude-plugin" / "plugin.json"
    if plugin.is_file():
        try:
            data = json.loads(plugin.read_text(encoding="utf-8"))
            if data.get("version") != version:
                errors.append("plugin.json version %r != VERSION %r"
                              % (data.get("version"), version))
        except json.JSONDecodeError as exc:
            errors.append(".claude-plugin/plugin.json does not parse: %s" % exc)

    changelog = root / "CHANGELOG.md"
    if changelog.is_file():
        if not re.search(r"^##\s+\[?%s\]?\b" % re.escape(version),
                         changelog.read_text(encoding="utf-8"), re.MULTILINE):
            errors.append("CHANGELOG.md has no entry for version %s" % version)
    else:
        errors.append("CHANGELOG.md is missing")


def check_private_data(root):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        if path.name in SCANNER_FILES or any(part in SKIP_DIRS for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(root)
        if PRIVATE_PATH.search(text):
            errors.append("%s: leaks a private path" % rel)
        if PRIVATE_KEY.search(text):
            errors.append("%s: contains a private key" % rel)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=pathlib.Path,
                        default=pathlib.Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)
    root = args.root.resolve()

    check_frontmatter(root)
    check_links(root)
    check_versions(root)
    check_private_data(root)

    for msg in errors:
        print("ERROR: %s" % msg)
    if errors:
        print("validate: %d error(s)" % len(errors))
        return 1
    print("validate: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
