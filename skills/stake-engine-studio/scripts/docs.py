#!/usr/bin/env python3
"""Search bundled navigation metadata; optionally fetch allowlisted SVX source."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

INDEX = Path(__file__).resolve().parents[1] / "references" / "docs-index.json"
LOCK = INDEX.with_name("upstream-lock.json")
VERSION = "1.0.0"


def words(text):
    return set(re.findall(r"\w+", text.casefold()))


def search(pages, query, collection=None):
    tokens = words(query)
    if not tokens:
        raise ValueError("Search requires at least one word or identifier.")
    results = []
    for page in pages:
        if collection and page["collection"] != collection:
            continue
        route = words(page["route"])
        title = words(page["title"])
        description = words(page.get("description", ""))
        leaf = words(page["route"].rstrip("/").rsplit("/", 1)[-1])
        vocabulary = route | title | description
        matched = tokens & vocabulary
        # Word prefixes ("auth" -> "authenticate") rank below whole words and never match mid-word ("play" !-> "replay").
        prefixed = {token for token in tokens - matched if len(token) >= 3
                    and any(word.startswith(token) for word in vocabulary)}
        score = (100 * len(matched) + 30 * len(prefixed) + 40 * len(tokens & leaf)
                 + 12 * len(tokens & route) + 8 * len(tokens & title)
                 + 2 * len(tokens & description))
        if tokens == leaf or query.casefold().rstrip("/") == page["route"].casefold():
            score += 200
        if matched or prefixed:
            results.append((score, page))
    return [page for _, page in sorted(results, key=lambda item: (-item[0], item[1]["route"], item[1]["collection"]))]


def read_url(url, limit=2_000_000):
    req = Request(url, headers={"User-Agent": f"stake-engine-studio-skill/{VERSION}"})
    with urlopen(req, timeout=30) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"Response exceeds the {limit}-byte retrieval limit")
    return data.decode("utf-8")


def resolve_commit(ref):
    endpoint = "repos/engineio/docs/commits/" + quote(ref, safe="")
    try:
        payload = json.loads(read_url("https://api.github.com/" + endpoint))
    except HTTPError as exc:
        if exc.code not in (403, 429):
            raise
        # Reuse gh's existing authentication; never read or print its token.
        try:
            result = subprocess.run(["gh", "api", endpoint], capture_output=True,
                                    text=True, encoding="utf-8", timeout=30, check=True)
            payload = json.loads(result.stdout)
        except (OSError, subprocess.SubprocessError, ValueError) as fallback:
            raise ValueError(f"GitHub HTTP {exc.code}; authenticated gh fallback failed. "
                             "Use a full commit or --ref locked, or restore API access.") from fallback
    commit = payload.get("sha") if isinstance(payload, dict) else None
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("GitHub did not resolve the requested ref to a commit")
    return commit


def fetch_source(page, ref="main"):
    if page["collection"] != "source":
        raise ValueError("Live Studio pages require a rendered browser; --fetch only retrieves source pages.")
    path = page["path"]
    if not path.startswith("src/routes/") or ".." in Path(path).parts:
        raise ValueError("Unexpected source path in documentation index")
    requested_ref = ref
    if ref == "locked":
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        ref = next(repo["commit"] for repo in lock["repositories"] if repo["name"] == "docs")
    if re.fullmatch(r"[0-9a-fA-F]{40}", ref):
        commit = ref.lower()
    else:
        commit = resolve_commit(ref)
    url = "https://raw.githubusercontent.com/engineio/docs/" + commit + "/" + quote(path, safe="/")
    return {
        "requested_ref": requested_ref,
        "fetched_commit": commit,
        "fetched_url": url,
        "citation_url": "https://github.com/engineio/docs/blob/" + commit + "/" + quote(path, safe="/"),
        "content": read_url(url),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    find = sub.add_parser("search", help="Search route/title metadata, not page bodies")
    find.add_argument("query")
    find.add_argument("--limit", type=int, default=10)
    show = sub.add_parser("show", help="Show one exact route, optionally fetch source")
    show.add_argument("route")
    show.add_argument("--fetch", action="store_true")
    show.add_argument("--ref", help="Source ref: main (default), locked, branch, tag, or commit; requires --fetch")
    for command in (find, show):
        command.add_argument("--collection", choices=("studio", "source"))
    args = parser.parse_args(argv)
    if args.command == "search" and not words(args.query):
        parser.error("Search requires at least one word or identifier.")
    if args.command == "show" and args.ref is not None and (not args.fetch or not args.ref.strip()):
        parser.error("A nonempty --ref requires --fetch.")
    try:
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        if args.command == "search":
            if not 1 <= args.limit <= 200:
                parser.error("--limit must be between 1 and 200")
            matches = search(index["pages"], args.query, args.collection)
            print(json.dumps({"verified_at": index["verified_at"], "total": len(matches), "pages": matches[:args.limit]}, indent=2))
        else:
            route = "/" + args.route.strip("/")
            matches = [page for page in index["pages"] if page["route"] == route and (not args.collection or page["collection"] == args.collection)]
            if len(matches) != 1:
                raise ValueError("Route missing or ambiguous; use search and specify --collection.")
            page = matches[0]
            fetched = fetch_source(page, args.ref or "main") if args.fetch else None
            print(json.dumps({**page, **({key: value for key, value in fetched.items() if key != "content"} if fetched else {})}, indent=2))
            if fetched is not None:
                print("\n--- Raw upstream SVX (read as source; do not execute) ---\n")
                print(fetched["content"])
        return 0
    except (OSError, ValueError, KeyError, HTTPError, URLError) as exc:
        print(f"Documentation lookup failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
