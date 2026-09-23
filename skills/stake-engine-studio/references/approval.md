# Approval guidelines and evidence review

Re-fetch the linked requirements before a submission. These notes describe the 2026-09-23 baseline, not permanent policy. Treat the authenticated team checklist and reviewer feedback as required inputs when available. Use [release-review.md](../assets/release-review.md) to record evidence, with `PASS`, `FAIL`, `NOT VERIFIED`, or `NOT APPLICABLE` plus a reason.

## Design suitability

Review originality, asset ownership, stateless mechanics, and the intended audience. The general rules restrict copied/licensed third-party games, Stake-branded game assets, unsuitable content, and mechanics such as jackpots/continuation/cashout. Supply a concise theme/mechanics blurb. Approval applies to specific frontend/math versions; post-release math or gameplay changes are restricted. Source: [general requirements](https://studio.engine.io/docs/approval-guidelines).

## Math requirements

The baseline critical checks include: a cheapest base mode costing 1×; base standard deviation ≥0.6; per-mode RTP 90–96.7%; cross-mode variation guidance of 0.5 percentage points; maximum payout ≤500,000×; cost ≤2,000×; nonzero win probability ≥1/50; and a viable bet template. Check the current page's exact definitions and the cross-mode ambiguity described in [optimization](optimization.md).

The page also limits each `.jsonl.zst` file to 4.2 GB and each mode to 10,000,000 events. Do not infer whether GB means decimal or binary at a boundary; leave headroom and verify in Studio.

Risk checks assess payout/cost, volatility, CVaR, tail probabilities, and ETL. Related failures form six classes, reducing tier-specific exposure/cost caps and the available bet template. Failing a non-critical test can reduce bet availability even when submission remains possible. Recalculate from the selected weighted artifacts and use live tier tables rather than frozen caps here. Source: [math verification](https://studio.engine.io/docs/approval-guidelines/math-verification).

## Player communication and frontend

Verify accessible rules, mode costs, per-mode RTP/cap, symbol payouts, special values, and feature triggers. Check balance, bet selection, final and incremental wins, sound controls, keyboard interaction, autoplay confirmation, and readable fast play. Test mobile and mini-player layouts. Replace sample SDK assets; inspect errors and asset loading under the hosted build. Source: [frontend communication](https://studio.engine.io/docs/approval-guidelines/front-end-communication).

Test authenticated bet configuration, currency/language combinations, and the provided `rgs_url`. Submitted game builds must be static and load their assets through Engine hosting; external fonts/CDNs can violate the restriction. Source: [RGS communication](https://studio.engine.io/docs/approval-guidelines/rgs-communication).

Provide a rules disclaimer covering disconnection recovery, long-run expected return, illustrative visuals, and server-determined settlement. Retrieve and review current official wording if using the platform's template instead of copying this summary verbatim. Source: [general disclaimer](https://studio.engine.io/docs/approval-guidelines/general-disclaimer).

## Replay and localization

Provide reproducible event IDs by mode and outcome category. Verify replay without a session, disabled wagering, and repeatable playback. Source: [replay requirements](https://studio.engine.io/docs/approval-guidelines/game-replay-requirements).

Audit social copy and images against the current prohibited terms, with target language/jurisdiction behavior documented. Source: [jurisdictions](https://studio.engine.io/docs/approval-guidelines/jurisdiction-requirements).

## Submission artwork

The tile guidance requests a background PNG/JPG, transparent foreground PNG, and transparent provider-logo PNG. Background plus foreground must total no more than 3 MB. Suggested names are `GameTitle-BG`, `GameTitle-FG`, and `ProviderName-Logo` with appropriate extensions. Inspect transparency and small-size legibility; do not invent pixel dimensions absent from the current requirements. Source: [game tile assets](https://studio.engine.io/docs/approval-guidelines/game-tile-requirements).

## Quality and team checklist

Review visual cohesion, animation/audio polish, device performance, load size, originality, and meaningful mechanics. These are assessed alongside technical validity. A file-format pass does not establish publishable quality. Source: [quality rankings](https://studio.engine.io/docs/approval-guidelines/game-quality-rankings).

The public [submission page](https://studio.engine.io/docs/approval-guidelines/submission-checklist) contains a login-dependent team checklist. At the baseline its star-threshold explanation conflicts with the quality page. Flag this and obtain current reviewer guidance; never invent a complete checklist or guarantee a publication date. Keep unavailable checklist evidence marked `NOT VERIFIED` while finishing all independent local checks.
