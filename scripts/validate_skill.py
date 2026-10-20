#!/usr/bin/env python3
"""Validate this package's deliberately simple YAML frontmatter and local links."""
import argparse
from pathlib import Path
import re


def validate(root):
    root = Path(root).resolve()
    text = (root / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n(.+)\Z", text, re.S)
    if not match:
        raise ValueError("expected YAML frontmatter and nonempty body")
    # Portable subset used by this skill, not a general-purpose YAML parser.
    metadata = {}
    for line in match[1].splitlines():
        key, separator, value = line.partition(": ")
        if not separator or key in metadata or key not in ("name", "description", "license"):
            raise ValueError("unsupported or duplicate frontmatter entry")
        if value[:1] in "[{&*!|>'\"" or ": " in value or " #" in value:
            raise ValueError("plain scalar subset only; use a YAML validator for other forms")
        metadata[key] = value
    name, description = metadata.get("name", ""), metadata.get("description", "")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64 or name != root.name:
        raise ValueError("invalid name or directory/name mismatch")
    if not 1 <= len(description) <= 1024:
        raise ValueError("invalid description")
    if len(text.splitlines()) >= 500:
        raise ValueError("entrypoint exceeds progressive disclosure budget")
    for relative in re.findall(r"\]\(([^)]+)\)", match[2]):
        if relative.startswith("https://"):
            continue
        target = (root / relative).resolve()
        if not target.is_relative_to(root.resolve()) or not target.is_file():
            raise ValueError("broken or escaping local reference: " + relative)
    for required in ("LICENSE", "NOTICE", "scripts/quality.py", "references/configuration.md", "references/evidence-contract.md"):
        if not (root / required).is_file():
            raise ValueError("missing required file: " + required)
    return {"name": name, "descriptionLength": len(description), "lines": len(text.splitlines()), "valid": True}


if __name__ == "__main__":
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    print(json.dumps(validate(parser.parse_args().root), indent=2))
