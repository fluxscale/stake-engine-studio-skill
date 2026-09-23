# Studio game publishing

This reference concerns publishing a **game to Studio**. For publishing **this skill through skills.sh**, see the [repository's maintainer guide](https://github.com/fluxscale/stake-engine-studio-skill/blob/main/PUBLISHING.md).

## Establish a release candidate

Record team, game ID, target environment, frontend commit/build, math version, exact mode names, and requested action: local preparation, upload, test publication, approval submission, or production release. These are different milestones. Respect authorization already given; a request to prepare does not implicitly authorize every later milestone.

Create a fresh artifact directory and preserve the build log. Record SHA-256 checksums for the final manifest, tables, books, and frontend files. Generate the [review report](../assets/release-review.md) before any authorized external action so the selected files and versions are concrete.

## Prepare frontend files

Use the actual project's build command. The baseline web-sdk build places the prerendered `index.html` under `apps/<game>/.svelte-kit/output/prerendered/pages/` and client assets under `.svelte-kit/output/client/`; its README instructs combining them into one upload directory. This is SDK-specific, not a universal `dist/` convention. Source: [web-sdk build/launch](https://github.com/engineio/web-sdk#build-a-game).

The minimal Vite example instead uses `base: "./"` and uploads the contents of `dist/`. Source: [RGS example](https://studio.engine.io/docs/rgs/example). Inspect the installed adapter/output rather than assuming either layout.

Serve the final folder locally under a nested path. Confirm that `index.html`, scripts, textures, fonts, sounds, and animations load without a dev server. Inspect network requests for missing and external assets, and ensure source credentials or live launch URLs are absent. Static assets should be ready for Engine CDN hosting. Source: [communication rules](https://studio.engine.io/docs/approval-guidelines/rgs-communication).

## Prepare math files

Collect `index.json` and all selected mode books/tables from the current generation's `library/publish_files/`. Run structural and full-book checks, then the project's verification and statistical analysis. Keep mode costs, RTP, caps, and player rules consistent. Sources: [quick start](https://studio.engine.io/docs/math/quick-start), [required format](https://studio.engine.io/docs/math/math-file-format).

Preserve full-resolution artifacts; do not reduce file sizes by changing IDs or rounding payouts. If a cap/file limit is exceeded, fix generation/coverage and regenerate a coherent candidate. Never upload a half-updated combination of books and tables.

## Upload and test when requested

The SDK's documented Studio flow uploads through the game's Files page, selects frontend publication, and launches a developer/test session. UI labels may have changed; verify them in the live account. Uploading or creating a test version does not mean approval or public availability.

Select the intended frontend/math versions together. Confirm processing status, then test normal play, valid bet levels, each mode, currency/language variants, active-round recovery, and session-free replay. Record remote version IDs and sanitized evidence. Keep the launch query private because it can contain a session token.

No generic Studio deployment CLI or public upload API is established by these sources. Use the authorized UI or an explicitly documented integration; do not fabricate `stake-engine deploy` or infer internal endpoints from frontend code.

## Submit for review

Complete the authenticated checklist, attach the game blurb and tile assets, and supply replay IDs for representative outcomes per mode. Re-read [approval rules](approval.md), inspect unresolved reviewer feedback, and tie the submission to exact artifact versions. Report blockers clearly instead of describing a draft as submitted.

## After submission/release

Record the actual status returned by Studio. Keep “uploaded,” “testable,” “submitted,” “approved,” and “published” separate in status reports. Reproduce reviewer findings on the submitted versions before changing code. After release, verify the policy before changing math/modes/mechanics; the current general requirements normally permit only minor visual fixes unless the Engine team requests otherwise. Source: [post-release rules](https://studio.engine.io/docs/approval-guidelines).

For rollback or emergency replacement, verify current platform support and select a known compatible pair of frontend/math artifacts. A local Git revert alone does not roll back a hosted game.
