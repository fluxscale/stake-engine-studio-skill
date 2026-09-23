#!/usr/bin/env python3
"""Validate portable skill metadata, local links, and source inventories."""

import ast
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "stake-engine-studio"


def validate():
    errors = []
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    parts = text.split("---", 2)
    metadata = yaml.safe_load(parts[1]) if len(parts) == 3 and not parts[0].strip() else {}
    if metadata.get("name") != SKILL.name:
        errors.append("Skill name must match its containing folder")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", metadata.get("name", "")):
        errors.append("Invalid skill name")
    description = metadata.get("description")
    if not isinstance(description, str) or not 1 <= len(description) <= 1024:
        errors.append("Skill description missing or too long")
    if len(text.splitlines()) > 500:
        errors.append("Move detailed guidance into references; entrypoint exceeds 500 lines")
    ui = yaml.safe_load((SKILL / "agents/openai.yaml").read_text())["interface"]
    if not 25 <= len(ui["short_description"]) <= 64 or "$stake-engine-studio" not in ui["default_prompt"]:
        errors.append("Invalid agent UI description or invocation prompt")
    if (ROOT / "LICENSE").read_bytes() != (SKILL / "LICENSE").read_bytes():
        errors.append("Installed skill license must match the repository license")

    files = [*ROOT.glob("*.md"), *SKILL.rglob("*.md"), *ROOT.joinpath("tests").glob("*.md")]
    for file in files:
        content = file.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]\n]*\]\(([^)\s]+)\)", content):
            parsed = urlparse(target)
            if parsed.scheme or target.startswith("#"):
                continue
            destination = (file.parent / unquote(parsed.path)).resolve()
            if not destination.is_file():
                errors.append(f"Broken local link in {file.relative_to(ROOT)}: {target}")
            if file.is_relative_to(SKILL) and not destination.is_relative_to(SKILL):
                errors.append(f"Installed skill depends on file outside its bundle: {target}")
    for file in [*SKILL.joinpath("scripts").glob("*.py"), *ROOT.joinpath("scripts").glob("*.py")]:
        ast.parse(file.read_text(), filename=str(file))

    index = json.loads((SKILL / "references/docs-index.json").read_text())
    seen = set()
    markdown = (SKILL / "references/docs-index.md").read_text()
    for page in index["pages"]:
        key = (page["collection"], page["route"])
        if key in seen:
            errors.append(f"Duplicate documentation identity: {key}")
        seen.add(key)
        if page["collection"] == "studio":
            if page["url"] != "https://studio.engine.io" + page["route"]:
                errors.append(f"Invalid Studio URL: {page['url']}")
        elif page["collection"] == "source":
            expected = "https://github.com/engineio/docs/blob/main/" + page["path"]
            if page["url"] != expected or not page["path"].startswith("src/routes/") or ".." in Path(page["path"]).parts:
                errors.append(f"Invalid source path: {page}")
        else:
            errors.append(f"Unknown source collection: {page['collection']}")
        if f"]({page['url']})" not in markdown:
            errors.append(f"Markdown index missing: {page['url']}")

    lock = json.loads((SKILL / "references/upstream-lock.json").read_text())
    names = set()
    for repo in lock["repositories"]:
        if repo["name"] in names or not re.fullmatch("[0-9a-f]{40}", repo["commit"]):
            errors.append(f"Invalid repository evidence: {repo['name']}")
        names.add(repo["name"])
        if repo["url"] != "https://github.com/engineio/" + repo["name"]:
            errors.append(f"Unexpected upstream owner: {repo['url']}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Valid: {metadata['name']}; {len(index['pages'])} doc routes; {len(names)} upstream repos; local links and Python syntax checked.")
    return 0


if __name__ == "__main__":
    sys.exit(validate())
