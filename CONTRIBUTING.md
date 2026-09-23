# Maintaining the skill

Keep the skill practical, source-backed, and portable. The task router belongs in `SKILL.md`; conditional detail belongs in focused references. Preserve the README installation order: skills.sh, Claude Code, Codex.

## Refresh official sources

1. Inspect [engineio](https://github.com/engineio) for renamed/new/archived repositories.
2. Re-read relevant deployed Studio pages and compare the installed SDK's implementation. Use the [source hierarchy](skills/stake-engine-studio/references/sources.md); public docs source is not necessarily the deployed Studio revision.
3. Update the JSON route index and its Markdown companion together. Keep `studio` routes distinct from source-repo routes. Titles and metadata are navigational; do not vendor full manuals.
4. Record checked commits/dates in `upstream-lock.json`. Update freshness claims only for the scope actually rechecked. Keep unresolved disagreements visible until evidence resolves them.
5. Run validation, helper tests, and applicable [behavioral scenarios](tests/scenarios.md). Add a regression case when a real bug changes a helper's behavior.

Use primary documentation and source permalinks. Report an upstream issue as a hypothesis unless code/reproduction confirms it. Do not freeze issue statuses or approval thresholds without a date and refresh instruction.

## Editing helper scripts

Helpers should stay read-only against user artifacts and remote services, use explicit arguments, and fail visibly. No automatic dependency installation, credential capture, arbitrary shell execution, or external mutation. Keep offline navigation available when the network/`gh` is unavailable. Tests should demonstrate observable failures and invariants, not match prose headings.

## Scope

Game provider workflows, operator wallet integration, and Engine product UI have different contracts. Avoid transferring operator idempotency rules to undocumented client endpoints or product-brand/font instructions to game submissions. A helper report cannot replace Studio approval.

See [PUBLISHING.md](PUBLISHING.md) for distribution and release verification. Original contributions are licensed under the repository's [MIT license](LICENSE); preserve third-party attribution and do not copy proprietary game fixtures.
