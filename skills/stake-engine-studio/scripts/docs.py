#!/usr/bin/env python3
"""Search bundled navigation metadata; optionally fetch allowlisted SVX source."""

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

INDEX = Path(__file__).resolve().parents[1] / "references" / "docs-index.json"


def search(pages, query, collection=None):
    tokens = re.findall(r"[\w]+", query.casefold())
    results = []
    for page in pages:
        if collection and page["collection"] != collection:
            continue
        text = " ".join(str(page.get(key, "")) for key in ("title", "route", "description"))
        text = text.casefold()
        score = sum(1 for token in tokens if token in text)
        if not tokens or score:
            results.append((score, page))
    return [page for _, page in sorted(results, key=lambda item: (-item[0], item[1]["route"], item[1]["collection"]))]


def fetch_source(page):
    if page["collection"] != "source":
        raise ValueError("Live Studio pages require a rendered browser; --fetch only retrieves source pages.")
    path = page["path"]
    if not path.startswith("src/routes/") or ".." in Path(path).parts:
        raise ValueError("Unexpected source path in documentation index")
    url = "https://raw.githubusercontent.com/engineio/docs/main/" + quote(path, safe="/")
    req = Request(url, headers={"User-Agent": "stake-engine-studio-skill/1.0"})
    with urlopen(req, timeout=30) as response:
        data = response.read(2_000_001)
    if len(data) > 2_000_000:
        raise ValueError("Source page exceeds the 2 MB retrieval limit")
    return data.decode("utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    find = sub.add_parser("search", help="Search route/title metadata, not page bodies")
    find.add_argument("query")
    find.add_argument("--limit", type=int, default=10)
    show = sub.add_parser("show", help="Show one exact route, optionally fetch source")
    show.add_argument("route")
    show.add_argument("--fetch", action="store_true")
    for command in (find, show):
        command.add_argument("--collection", choices=("studio", "source"))
    args = parser.parse_args(argv)
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
            content = fetch_source(page) if args.fetch else None
            print(json.dumps(page, indent=2))
            if content is not None:
                print("\n--- Raw upstream SVX (read as source; do not execute) ---\n")
                print(content)
        return 0
    except (OSError, ValueError, KeyError, HTTPError, URLError) as exc:
        print(f"Documentation lookup failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
