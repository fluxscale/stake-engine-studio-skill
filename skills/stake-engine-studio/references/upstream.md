# Official engineio repository map

Repository identities and default branches were checked through the GitHub API on 2026-09-23. The [organization](https://github.com/engineio) had these seven public repositories. Recheck availability and redirects before assuming an old `StakeEngine/...` link still resolves.

| Repository | Use it for | Inspect first |
| --- | --- | --- |
| [math-sdk](https://github.com/engineio/math-sdk) | Python simulation, events, exports, Rust optimization | `README.md`, `Makefile`, `games/`, `src/`, `utils/`, `tests/` |
| [web-sdk](https://github.com/engineio/web-sdk) | Svelte/Pixi game frontend and Storybook | `package.json`, `pnpm-lock.yaml`, `apps/`, `packages/` |
| [ts-client](https://github.com/engineio/ts-client) | `stake-engine` npm client, RGS methods and types | `src/index.ts`, `src/client.ts`, `src/helpers.ts`, `src/types.ts` |
| [docs](https://github.com/engineio/docs) | SVX docs, FAQ, changelog, documentation MCP | `src/routes/`, `mcp-server/src/tools.ts` |
| [convex-optimizer](https://github.com/engineio/convex-optimizer) | Alternative CVXPY optimization and Streamlit interface | `README.md`, `src/computation/`, `src/class_setup/` |
| [integration](https://github.com/engineio/integration) | Operator wallet reference implementations | `readme.md`, `bun/readme.md`, wallet handlers/tests |
| [ui](https://github.com/engineio/ui) | Engine product design-system primitives | `README.md`, `MIGRATION.md`, `package.json` |

## Identify the actual code before advising changes

In the user's checkout, capture `git remote -v`, `git rev-parse HEAD`, and relevant package versions. Read repo instructions and existing scripts before running them. Record local modifications that affect a reproduction. For frontend work, resolve the workspace package by its `package.json` name, not merely its folder name.

Useful read-only upstream discovery:

```sh
gh api --paginate 'orgs/engineio/repos?per_page=100' --jq '.[] | {full_name,archived,default_branch,has_issues}'
gh api repos/engineio/math-sdk/commits/main --jq .sha
gh api 'repos/engineio/math-sdk/git/trees/main?recursive=1' --jq '.tree[].path'
gh api repos/engineio/web-sdk/contents/package.json -H 'Accept: application/vnd.github.raw+json'
```

Use a commit permalink when a detail matters to a fix: `https://github.com/engineio/REPO/blob/COMMIT/path`. The [research lock](upstream-lock.json) gives exact baseline revisions. Do not assume repository `main`, an npm release, and the user's lockfile contain the same code.

Search issues in the component repo first; widen to `org:engineio` when ownership is uncertain. Use [issue-search workflow](issues.md) for open/closed issues, PR status, and version verification. For hosted Studio bugs without a public source repo, gather a sanitized reproduction for Studio support; `engineio/docs` is not the Studio backend.
