# Stake Engine Studio Skill

A comprehensive agent skill for building, debugging, validating, and preparing games for [Engine Studio](https://studio.engine.io/docs), also known as Stake Engine. Grounded in the official [engineio repositories](https://github.com/engineio): math, frontend, RGS client, docs, optimization, operator integrations, and UI.

Independent community skill maintained by FluxScale; not an official Engine product. It supports Claude Code, Codex, and other agents that read `SKILL.md`.

## Install

### 1. skills.sh

Run in the project where you want the skill available:

```sh
npx skills add fluxscale/stake-engine-studio-skill --skill stake-engine-studio
```

Choose your agent in the installer. Add `--global` for a user-wide installation. Preview available skills without installing:

```sh
npx skills add fluxscale/stake-engine-studio-skill --list
```

See the [skills.sh documentation](https://skills.sh/docs) and [CLI options](https://github.com/vercel-labs/skills#usage). These remote commands require the skill files to be published to the repository; for an unpublished checkout, use `npx skills add . --skill stake-engine-studio` from this repo.

### 2. Claude Code

Install directly for Claude Code:

```sh
npx skills add fluxscale/stake-engine-studio-skill --skill stake-engine-studio --agent claude-code
```

Then invoke:

```text
/stake-engine-studio Review this game's math, frontend, and replay support before submission.
```

Manual alternative, from this repository after cloning it:

```sh
mkdir -p ~/.claude/skills
cp -R skills/stake-engine-studio ~/.claude/skills/stake-engine-studio
```

Use a fresh destination; update an existing installation through its original installer. For project-only manual installation, copy the folder to your game's `.claude/skills/stake-engine-studio/`. Copy the entire skill, including references and scripts. See [Claude Code skills](https://code.claude.com/docs/en/skills).

### 3. Codex

Install directly for Codex:

```sh
npx skills add fluxscale/stake-engine-studio-skill --skill stake-engine-studio --agent codex
```

Then invoke:

```text
$stake-engine-studio Find the relevant engineio issues and fix this RGS integration.
```

Manual alternative, from this repository after cloning it:

```sh
mkdir -p ~/.agents/skills
cp -R skills/stake-engine-studio ~/.agents/skills/stake-engine-studio
```

Use a fresh destination. For project-only manual installation, use your game's `.agents/skills/stake-engine-studio/`. Current official Codex guidance documents `~/.agents/skills` for user-authored skills; the skills CLI may use its own supported compatibility location. Start a new session if the skill does not appear. See [Codex skill discovery](https://developers.openai.com/codex/skills/).

## What it covers

| Area | Included guidance |
| --- | --- |
| Documentation | 158 indexed routes: 64 deployed Studio routes plus 94 official source/FAQ/changelog pages; source selection, freshness, MCP, and known discrepancies |
| Math SDK | Configuration, reels, symbols, modes, distributions, simulation acceptance, wins, events, and forced outcomes |
| Optimization | Weighted RTP, hit rates, mode-cost normalization, Rust and convex optimizers, statistical evidence |
| Math files | Manifest, uint64 lookup tables, JSONL/Zstandard books, exact ID/payout matching, read-only preflight |
| Frontend | Svelte/Pixi architecture, event handlers, Storybook, state, layout, assets, and custom renderers |
| RGS | Authentication, wallet units, bet configuration, errors, settlement, and recovery |
| Replay | Session-free startup, disabled wagering, reproducible outcomes, and replay fixtures |
| Approval | Current guidelines, originality, math/risk checks, social copy, tiles, quality, and evidence reports |
| Publishing | Static packaging, version pairing, upload/test/submission stages, post-release constraints |
| Issue research | Component-specific searches across open/closed issues and PRs, version applicability, sanitized reports |
| Ecosystem | Official docs MCP, operator wallet integrations, Engine product UI, and payment-document routing |

The entrypoint loads only the references relevant to a task. This is a curated workflow and source index, not a copy of the upstream manuals. Coverage and upstream revisions were verified on **2026-09-23**. Live policy, installed source, and authenticated team requirements can differ; the skill explicitly handles those gaps.

## Example requests

```text
Build a new lines game using the engineio math and web SDKs.
Trace this payoutMultiplier from the published CSV through the frontend animation.
Find open and closed upstream issues matching this payout hash mismatch.
Add a new book event and test it in Storybook and full-round replay.
Audit normal play, recovery, social mode, and public replay against Studio guidelines.
Prepare our static frontend and math files for review, with evidence and blockers.
Explain the difference between game-client RGS calls and operator wallet callbacks.
```

## Helpers

The skill itself needs no runtime. Helpers use Python 3.10+. Read-only issue execution additionally needs authenticated [GitHub CLI](https://cli.github.com/); full compressed-book inspection needs the optional `zstandard` Python package. No credentials are required for local index searches or math checks.

From the repository root:

```sh
python3 skills/stake-engine-studio/scripts/docs.py search replay
python3 skills/stake-engine-studio/scripts/docs.py show /docs/api/play --collection source --fetch
python3 skills/stake-engine-studio/scripts/issues.py 'payoutMultiplier' --repo math-sdk
python3 skills/stake-engine-studio/scripts/issues.py 'payoutMultiplier' --repo math-sdk --run
python3 skills/stake-engine-studio/scripts/inspect_math.py /path/to/publish_files --books
```

Issue searches preview by default. `--run` only reads GitHub. Math checks never edit artifacts or publish anything. Without `--books`, the report explicitly says book contents were not verified. See [helper scope and limits](skills/stake-engine-studio/references/math-artifacts.md).

## Repository guide

- [Skill entrypoint](skills/stake-engine-studio/SKILL.md)
- [Complete documentation index](skills/stake-engine-studio/references/docs-index.md)
- [Official repository map](skills/stake-engine-studio/references/upstream.md) and [recorded revisions](skills/stake-engine-studio/references/upstream-lock.json)
- [Source policy and known inconsistencies](skills/stake-engine-studio/references/sources.md)
- [Release-review template](skills/stake-engine-studio/assets/release-review.md) and [issue-report template](skills/stake-engine-studio/assets/issue-report.md)
- [Publish this skill on skills.sh](PUBLISHING.md)
- [Contribute and refresh sources](CONTRIBUTING.md)
- [Behavioral evaluation scenarios](tests/scenarios.md)

## Development checks

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/validate.py
.venv/bin/python -m unittest discover -s tests -v
DISABLE_TELEMETRY=1 npx skills add . --list
```

Windows: use `.venv\Scripts\python.exe` instead of `.venv/bin/python`.

Original skill content and helpers are [MIT licensed](LICENSE). Linked upstream documentation, code, names, and assets remain subject to their respective licenses and ownership.
