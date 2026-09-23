#!/usr/bin/env python3
"""Preview or run read-only issue/PR searches against official engineio repos."""

import argparse
import json
import shlex
import subprocess
import sys
from urllib.parse import urlencode

REPOS = ("math-sdk", "web-sdk", "ts-client", "docs", "convex-optimizer", "integration", "ui")


def make_search(query, repos, kind, state=None, limit=20):
    qualifiers = [f"repo:engineio/{repo}" for repo in repos] if repos else ["org:engineio"]
    qualifiers += ["is:issue" if kind == "issues" else "is:pr"]
    if state:
        qualifiers.append(f"is:{state}")
    url = "https://github.com/search?" + urlencode({"q": " ".join([query, *qualifiers]), "type": "issues"})
    command = ["gh", "search", kind, query, "--limit", str(limit), "--json", "number,title,state,url,updatedAt"]
    for repo in repos:
        command += ["--repo", f"engineio/{repo}"]
    if not repos:
        command += ["--owner", "engineio"]
    if state:
        command += ["--state", state]
    return {"kind": kind, "url": url, "command": command, "preview": shlex.join(command)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Sanitized keywords or quoted exact error")
    parser.add_argument("--repo", choices=REPOS, action="append", default=[])
    parser.add_argument("--kind", choices=("issues", "prs", "both"), default="both")
    parser.add_argument("--state", choices=("open", "closed"))
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--run", action="store_true", help="Execute read-only gh searches")
    args = parser.parse_args(argv)
    if not args.query.strip() or args.query.startswith("-"):
        parser.error("Provide a nonempty query that does not start with '-'.")
    if not 1 <= args.limit <= 100:
        parser.error("--limit must be between 1 and 100")
    kinds = ("issues", "prs") if args.kind == "both" else (args.kind,)
    output = []
    failed = False
    for kind in kinds:
        item = make_search(args.query, list(dict.fromkeys(args.repo)), kind, args.state, args.limit)
        if args.run:
            try:
                result = subprocess.run(item["command"], capture_output=True, text=True, timeout=45, check=True)
                item["results"] = json.loads(result.stdout)
                item["possibly_truncated"] = len(item["results"]) >= args.limit
            except (OSError, subprocess.SubprocessError, ValueError) as exc:
                item["error"] = (exc.stderr or str(exc)).strip() if isinstance(exc, subprocess.CalledProcessError) else str(exc)
                failed = True
        output.append(item)
    print(json.dumps({"executed": args.run, "searches": output}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
