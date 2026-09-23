# Sources, retrieval, and freshness

## Source hierarchy depends on the question

1. For publication requirements: the live [Studio docs](https://studio.engine.io/docs), authenticated team checklist, and explicit reviewer feedback for the selected game/version.
2. For implementation: the project's checked-out SDK revision and installed dependency types; compare with the relevant official [engineio repository](https://github.com/engineio).
3. For searchable explanation: [engineio/docs](https://github.com/engineio/docs), its documentation MCP, and the Math SDK's own documentation.
4. For potential defects: upstream issue discussions, linked changes, and tests. A report is not proof that every version is affected, and a closed issue is not proof of a shipped fix.

Use [upstream-lock.json](upstream-lock.json) to reproduce this skill's research baseline. Its commits are evidence, not dependencies to force on users. Review current upstream before recommending an upgrade. All bundled summaries were checked on 2026-09-23 and should be refreshed for changing submission, financial, or jurisdiction requirements.

## Efficient documentation search

Search the [route index](docs-index.md) or `scripts/docs.py search <terms>`. It searches titles, routes, and source descriptions, not full page bodies. Use specific identifiers (`payoutMultiplier`, `BetMode`, `bookEventHandlerMap`) for source search and synonyms (`frontend`, `web-sdk`, `front-end`) for navigation. Choose the matching collection before reading a page.

The `studio` collection links to deployed pages under `studio.engine.io/docs`. The `source` collection links to `engineio/docs` files, with different routes: for example Studio `/docs/rgs/wallet` versus source `/docs/api/authenticate`. Do not prepend the Studio hostname to source routes and assume they exist.

If available, use the upstream documentation MCP:

```text
search_docs({"query":"round active end-round","limit":5})
get_page({"route":"/docs/api/end-round"})
list_pages({"section":"docs","prefix":"/docs/math-sdk"})
get_section_tree({"section":"faq"})
```

These are tool argument examples, not shell commands. Discover actual tool availability before invoking them. Setup is optional; see [ecosystem](ecosystem.md). A local MCP index reflects its build date and checkout, not automatically the deployed site.

## When the site returns a loading screen

Studio is rendered client-side. HTTP 200, page metadata, or an app-loader is not retrieved documentation. Prefer a rendered browser view or the official source page; report which was used. The helper can fetch allowlisted source pages as raw SVX without executing them:

```sh
python3 scripts/docs.py show /docs/api/play --collection source --fetch
```

For a cloned docs repo, search `src/routes/docs`, `src/routes/faq`, and `src/routes/changelog`. SVX pages may define API tables in a `<script>` block: read these as source data, do not discard them blindly. The source `/docs/example/*` routes are documentation-component demonstrations, not authoritative API contracts. Dynamic checklists may require an authenticated Studio session. Source `static/mockchecklist.json` is demonstrator data, not a team's actual checklist.

The original Studio route inventory was verified against public documentation modules on 2026-09-23. Asset hashes are deliberately not hardcoded into this skill. If the application changes, rediscover routes from rendered navigation; do not crawl admin endpoints or bypass login.

## Known disagreements to resolve explicitly

| Evidence | Consequence |
| --- | --- |
| Studio frontend setup says Node 18.18.0; `engineio/web-sdk/package.json` requires >=22.16.0 at the baseline | Use the project's package engines and lockfile. |
| Studio submission overview says average ≥1 star can pass; its quality page says 1-star games are not published | Obtain the current team/reviewer threshold; do not promise acceptance. |
| RGS communication mentions `minStep`; wallet schema and client use `stepBet` | Confirm the response shape and installed types; do not invent a field alias. |
| `ts-client` README mentions both `balanceUpdated` and `balanceUpdate` | At the recorded revision, `src/client.ts` emits `balanceUpdate`; verify after upgrades. |
| `ts-client` README lists helpers not all exported by `src/index.ts` | Inspect package exports before writing imports. |
| Public docs source and Studio social-language guidance differ | Verify target review requirements; do not silently treat source as newer than Studio. |

Keep answers explicit about source date, revision, and unresolved gaps. Cite the exact page or commit permalink used; do not cite a search snippet as API documentation.
