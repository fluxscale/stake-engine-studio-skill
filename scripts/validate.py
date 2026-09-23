#!/usr/bin/env python3
"""Validate skill metadata, bundle links, and inventories; optionally check GitHub."""

import argparse
import ast
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]


def online_errors(targets):
    """Check official blob paths against GitHub trees; never fetch private audit files."""
    errors = []
    grouped = {}
    for repo, ref, path in targets:
        grouped.setdefault((repo, ref), set()).add(path)
    for (repo, ref), paths in sorted(grouped.items()):
        try:
            result = subprocess.run(
                ["gh", "api", f"repos/engineio/{repo}/git/trees/{ref}?recursive=1"],
                capture_output=True, text=True, encoding="utf-8", timeout=45, check=True,
            )
            tree = json.loads(result.stdout)
            if not isinstance(tree, dict) or tree.get("truncated") or not isinstance(tree.get("tree"), list):
                raise ValueError("GitHub returned an incomplete tree")
            existing = {entry["path"] for entry in tree["tree"] if entry.get("type") == "blob"}
            for path in sorted(paths - existing):
                errors.append(f"Missing upstream file: engineio/{repo}@{ref}/{path}")
        except (OSError, subprocess.SubprocessError, ValueError, KeyError) as exc:
            detail = (exc.stderr or str(exc)) if isinstance(exc, subprocess.CalledProcessError) else str(exc)
            errors.append(f"Online verification failed for engineio/{repo}@{ref}: {detail.strip()}")
    return errors


def validate(root=ROOT, online=False):
    root = Path(root).resolve()
    skill = root / "skills" / "stake-engine-studio"
    errors, targets = [], set()

    def read(path):
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"Cannot read {path.relative_to(root)}: {exc}")
            return ""

    def mapping(text, label, loader):
        try:
            value = loader(text)
        except (ValueError, yaml.YAMLError) as exc:
            errors.append(f"Invalid {label}: {exc}")
            return {}
        if not isinstance(value, dict):
            errors.append(f"{label} must be a mapping")
            return {}
        return value

    def array(data, key, label):
        value = data.get(key)
        if not isinstance(value, list) or not value:
            errors.append(f"{label} must contain a nonempty {key} array")
            return []
        return value

    text = read(skill / "SKILL.md")
    match = re.match(r"\A---\r?\n(.*?)^---[ \t]*(?:\r?\n|\Z)", text, re.M | re.S)
    if not match:
        errors.append("SKILL.md is missing YAML frontmatter delimiters")
    metadata = mapping(match[1] if match else "", "skill frontmatter", yaml.safe_load)
    name = metadata.get("name")
    if name != skill.name:
        errors.append("Skill name must match its containing folder")
    if not isinstance(name, str) or len(name) > 64 or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        errors.append("Invalid skill name (lowercase hyphenated name, at most 64 characters)")
    description = metadata.get("description")
    if not isinstance(description, str) or not 1 <= len(description) <= 1024:
        errors.append("Skill description missing or too long")
    if len(text.splitlines()) > 500:
        errors.append("Move detailed guidance into references; entrypoint exceeds 500 lines")
    config = mapping(read(skill / "agents/openai.yaml"), "agent configuration", yaml.safe_load)
    ui = config.get("interface")
    if not isinstance(ui, dict):
        errors.append("Agent configuration needs an interface mapping")
        ui = {}
    short, prompt = ui.get("short_description"), ui.get("default_prompt")
    if not isinstance(short, str) or not 25 <= len(short) <= 64 or not isinstance(prompt, str) or "$stake-engine-studio" not in prompt:
        errors.append("Invalid agent UI description or invocation prompt")
    try:
        if (root / "LICENSE").read_bytes() != (skill / "LICENSE").read_bytes():
            errors.append("Installed skill license must match the repository license")
    except OSError as exc:
        errors.append(f"Cannot read required license: {exc}")

    files = [*root.glob("*.md"), *skill.rglob("*.md"), *root.joinpath("tests").glob("*.md")]
    for file in files:
        for target in re.findall(r"\[[^\]\n]*\]\(([^)\s]+)\)", read(file)):
            parsed = urlparse(target)
            if parsed.scheme or target.startswith("#"):
                if parsed.netloc == "github.com":
                    link = re.fullmatch(r"/engineio/([^/]+)/blob/([^/]+)/(.+)", unquote(parsed.path))
                    if link:
                        targets.add(tuple(link.groups()))
                continue
            destination = (file.parent / unquote(parsed.path)).resolve()
            if not destination.is_file():
                errors.append(f"Broken local link in {file.relative_to(root)}: {target}")
            if file.is_relative_to(skill) and not destination.is_relative_to(skill):
                errors.append(f"Installed skill depends on file outside its bundle: {target}")
    for file in [*skill.joinpath("scripts").glob("*.py"), *root.joinpath("scripts").glob("*.py")]:
        try:
            tree = ast.parse(read(file), filename=str(file))
            if file.name == "docs.py":
                version = next((ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                                and any(isinstance(t, ast.Name) and t.id == "VERSION" for t in node.targets)), None)
                details = metadata.get("metadata")
                if not isinstance(details, dict) or version != details.get("version"):
                    errors.append("docs.py User-Agent version differs from skill metadata.version")
        except (SyntaxError, ValueError) as exc:
            errors.append(f"Invalid Python source {file.relative_to(root)}: {exc}")

    index = mapping(read(skill / "references/docs-index.json"), "docs index", json.loads)
    pages = array(index, "pages", "docs index")
    markdown = read(skill / "references/docs-index.md")
    seen, expected_rows, counts = set(), Counter(), Counter()
    for page in pages:
        if not isinstance(page, dict) or not all(isinstance(page.get(k), str) for k in ("collection", "route", "title", "url")):
            errors.append("Malformed documentation page entry")
            continue
        collection, route = page["collection"], page["route"]
        key = (collection, route)
        if key in seen:
            errors.append(f"Duplicate documentation identity: {key}")
        seen.add(key)
        counts[collection] += 1
        if collection == "studio":
            if page["url"] != "https://studio.engine.io" + route:
                errors.append(f"Invalid Studio URL: {page['url']}")
        elif collection == "source":
            path = page.get("path", "")
            if not isinstance(path, str) or not path.startswith("src/routes/") or ".." in Path(path).parts or page["url"] != "https://github.com/engineio/docs/blob/main/" + path:
                errors.append(f"Invalid source path: {route}")
        else:
            errors.append(f"Unknown source collection: {collection}")
        expected_rows[(route, page["title"].replace("|", " / "), page["url"])] += 1
    actual_rows = Counter(re.findall(r"^\| `([^`]+)` \| \[(.*?)\]\(([^)]+)\) \|$", markdown, re.M))
    if actual_rows != expected_rows:
        errors.append("Markdown index differs from JSON (missing, extra, duplicated, or changed rows/titles)")
    headings = re.findall(r"^## .+ \((\d+) routes\)$", markdown, re.M)
    if headings != [str(counts["studio"]), str(counts["source"])]:
        errors.append("Markdown index route counts differ from JSON")
    readme = read(root / "README.md")
    prose = re.search(r"(\d+) indexed routes: (\d+) deployed Studio routes plus (\d+) official source", readme)
    if not prose or tuple(map(int, prose.groups())) != (len(pages), counts["studio"], counts["source"]):
        errors.append("README route counts differ from JSON")

    lock = mapping(read(skill / "references/upstream-lock.json"), "upstream lock", json.loads)
    repositories = array(lock, "repositories", "upstream lock")
    baseline = index.get("verified_at")
    try:
        if not isinstance(baseline, str) or date.fromisoformat(baseline).isoformat() != baseline:
            raise ValueError("expected YYYY-MM-DD")
    except ValueError:
        errors.append("Invalid docs-index verified_at date")
    if lock.get("verified_at") != baseline:
        errors.append("Upstream lock and docs index baseline dates differ")
    # These prose dates describe the shared research snapshot, not historical events.
    baseline_checks = [
        (root / "README.md", r"verified on \*\*(\d{4}-\d{2}-\d{2})\*\*"),
        (skill / "references/docs-index.md", r"Verified (\d{4}-\d{2}-\d{2})"),
        (skill / "references/sources.md", r"(?:checked on|verified against public documentation modules on) (\d{4}-\d{2}-\d{2})"),
        (skill / "references/upstream.md", r"API on (\d{4}-\d{2}-\d{2})"),
        (skill / "references/approval.md", r"describe the (\d{4}-\d{2}-\d{2}) baseline"),
    ]
    for file, pattern in baseline_checks:
        matches = re.findall(pattern, read(file))
        if not matches or any(value != baseline for value in matches):
            errors.append(f"Research baseline date differs or is missing in {file.relative_to(root)}")
    names = set()
    for repo in repositories:
        if not isinstance(repo, dict) or not isinstance(repo.get("name"), str) or not isinstance(repo.get("commit"), str):
            errors.append("Malformed repository evidence")
            continue
        if repo["name"] in names or not re.fullmatch("[0-9a-f]{40}", repo["commit"]):
            errors.append(f"Invalid repository evidence: {repo['name']}")
        names.add(repo["name"])
        if repo.get("url") != "https://github.com/engineio/" + repo["name"]:
            errors.append(f"Unexpected upstream owner: {repo.get('url')}")
        if repo["name"] == "docs":
            for page in pages:
                if isinstance(page, dict) and page.get("collection") == "source" and isinstance(page.get("path"), str):
                    targets.add(("docs", repo["commit"], page["path"]))
    if online and not errors:
        errors.extend(online_errors(targets))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Valid: {name}; {len(pages)} doc routes; {len(names)} upstream repos; metadata, links, counts, dates, and index consistency checked." + (" GitHub files verified." if online else ""))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true", help="Read official GitHub trees using authenticated gh; fails if unavailable")
    args = parser.parse_args(argv)
    return validate(online=args.online)


if __name__ == "__main__":
    sys.exit(main())
