# Troubleshooting and upstream issue search

## Capture a reproducible symptom

Record component, SDK commit/package version, operating system/runtime, game/mode, expected and actual behavior, and the smallest failing fixture. For RGS problems capture sanitized request/response shapes and the call order; for rendering, retain the event and story; for math, preserve the failing ID plus book/CSV values. Never post a live session URL or proprietary game data merely to search.

Use the official [repository map](upstream.md) to choose ownership. Search current docs and local source first, then both open and closed upstream issues and PRs. Avoid Socket.IO's similarly named engine.io repository.

## Build queries progressively

Start with the exact error, then its distinctive identifier, then the affected subsystem. For example: `"Payout hash mismatch"` → `payoutMultiplier` → optimizer export. For an animation stall: event type → `broadcastAsync` → unresolved animation. Restrict to the component repo before widening to `org:engineio`.

The bundled helper prints encoded GitHub search links and command previews without making requests:

```sh
python3 scripts/issues.py '"Payout hash mismatch"' --repo math-sdk
python3 scripts/issues.py 'broadcastAsync' --repo web-sdk --kind both
python3 scripts/issues.py 'replay' --kind both
```

For a query beginning with GitHub negation syntax, place helper options before `--`, for example `python3 scripts/issues.py --repo math-sdk -- '-label:bug payout'`. The helper also separates options from query text in its `gh` argument list.

Add `--run` to execute read-only GitHub CLI searches. Unspecified state searches open and closed results; `--state open` or `--state closed` narrows them. Use `--repo` repeatedly for multiple repositories. `--limit` is per query, and results may be truncated; an empty/truncated result is not proof that no issue exists. Authentication/rate-limit failures are reported as failures, not empty findings.

Equivalent commands:

```sh
gh search issues 'payoutMultiplier' --repo engineio/math-sdk --limit 20 --json number,title,state,url,updatedAt
gh search prs 'payoutMultiplier' --repo engineio/math-sdk --limit 20 --json number,title,state,url,updatedAt
gh issue view 108 --repo engineio/math-sdk --comments
```

For a relevant PR, use `gh pr view NUMBER --repo engineio/REPO --json state,mergedAt,mergeCommit,baseRefName,url` and inspect its changed code/tests. Check whether the merge is in the user's installed commit/tag. GitHub “closed” can mean unmerged, duplicate, abandoned, or fixed; determine which before advising an upgrade.

## Evaluate evidence

For each candidate, capture URL, symptom overlap, environment/version match, maintainer response, proposed fix, and local verification. A useful output table is `candidate | evidence | applies to this version? | next check`. Stop when evidence explains the observed failure or a focused search yields no applicable result; do not fill an answer with vaguely related issues.

At the baseline, [math-sdk issue #108](https://github.com/engineio/math-sdk/issues/108) was an open user report of optimized lookup payouts disagreeing with books, without comments. It is an example of a search lead, **not a confirmed diagnosis**. Re-fetch status, inspect source, and reproduce before assigning its proposed root cause to another game.

## Symptom routing

| Symptom | First checks | Upstream |
| --- | --- | --- |
| Book/LUT payout mismatch | Same generation, IDs, selected optimized table, payout units | `math-sdk` |
| Infinite simulation | Impossible criteria, forced feature/cap feasibility, reset state | `math-sdk` |
| RTP wrong only for bonus | Cost normalization and published weights | `math-sdk`, optionally `convex-optimizer` |
| Story never resolves | Awaited emitter subscribers, animation completion/reset | `web-sdk` |
| Dev page fails auth but Storybook works | Missing valid test launch parameters | `web-sdk`, `ts-client` |
| Invalid bet | Integer amount, exact mode, configured step/range/levels | `ts-client`; Studio if server rejection persists |
| Replay authenticates | Startup branch/client auto-init/polling | `web-sdk`, `ts-client` |
| API docs/source disagreement | Exact revision and schema | `docs` and implementing repo |
| Wallet retry debits twice | Transaction identity and atomic idempotency | `integration` |
| Product UI partially styled | Tailwind source scan/config | `ui` |

Draft a report using [issue-report.md](../assets/issue-report.md). Search permission does not authorize posting a public issue/comment. If asked to file, use the selected upstream template and include only the sanitized evidence needed to reproduce.
