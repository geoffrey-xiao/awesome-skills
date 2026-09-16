#!/usr/bin/env python3
"""Validate the repository-level Agent Skill contract without third-party packages."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r'^  version: "(\d+\.\d+\.\d+)"(?:\s+#.*)?$', re.MULTILINE)
NAME_RE = re.compile(r'^name: ([a-z0-9]+(?:-[a-z0-9]+)*)$', re.MULTILINE)
DESCRIPTION_RE = re.compile(r'^description: .+$', re.MULTILINE)


def main() -> None:
    skill_dirs = sorted(path for path in (ROOT / "skills").iterdir() if path.is_dir())
    if not skill_dirs:
        raise SystemExit("No Skill directories found")

    errors = []
    for skill_dir in skill_dirs:
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"{skill_dir}: missing SKILL.md")
            continue
        text = skill_file.read_text(encoding="utf-8")
        name = NAME_RE.search(text)
        description = DESCRIPTION_RE.search(text)
        version = VERSION_RE.search(text)
        if not name:
            errors.append(f"{skill_file}: missing or invalid name")
        elif name.group(1) != skill_dir.name:
            errors.append(f"{skill_file}: name does not match directory")
        if not description:
            errors.append(f"{skill_file}: missing description")
        if not version:
            errors.append(f"{skill_file}: missing quoted metadata.version")
        if text.count("\n") + 1 > 500:
            errors.append(f"{skill_file}: exceeds 500 lines")

    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Validated {len(skill_dirs)} Skills")


if __name__ == "__main__":
    main()
