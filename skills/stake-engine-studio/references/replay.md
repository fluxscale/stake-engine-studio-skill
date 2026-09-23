# Public replay and active-round recovery

These are separate features. Public replay reproduces a completed outcome without a player session. Recovery continues presentation/settlement of the authenticated player's active round.

## Public replay contract

The [Studio replay requirements](https://studio.engine.io/docs/approval-guidelines/game-replay-requirements) require replay for new game approval. Required launch parameters are `replay=true`, `game`, `version`, `mode`, `event`, and `rgs_url`; optional display parameters include `currency`, `amount`, `lang`, `device`, and `social`.

Fetch the selected outcome with:

```text
GET {rgs_url}/bet/replay/{game}/{version}/{mode}/{event}
```

The documented response contains `payoutMultiplier`, `costMultiplier`, and game-specific `state`. Read the matching schema before calculating display amounts. Load data automatically, then offer a replay-start control, full playback, final results, and replay-again. Disable wagers and wallet/session calls, and prevent transition into normal play.

## Implementation checks

Parse booleans explicitly: the string `"false"` is truthy in JavaScript. Validate required identifiers before fetching. Encode path segments individually. Keep replay state isolated from authenticated client initialization and balance polling. Use the same event renderer as live play so fixes improve both paths.

Before “play again,” reset presentation state, accumulated win counters, active animations, and transient audio. Do not fetch a new random book. Preserve the original math version and event ID. If optional amount/currency is missing, use a documented fallback or a multiplier-only display; do not invent a player's balance.

A useful fixture matrix covers loss, ordinary win, large win, cap, and feature entry for every mode. Include invalid/missing identifiers, unavailable math version, network failure, rapid replay-again clicks, and tiny viewports. Capture network traffic to prove that no `/wallet/*` call occurs. These are engineering checks, not additional platform rules.

## Active-round recovery

Authenticate and inspect `round.active`, its state, and progress marker. Decide whether to render from the beginning or resume according to the installed SDK's contract. Keep a recovered wager bound to its original mode/amount. Do not charge again or run browser RNG to reconstruct the result. Use the returned server balance and end-round response as monetary authority. Sources: [RGS flows](https://studio.engine.io/docs/rgs), [wallet event endpoint](https://studio.engine.io/docs/rgs/wallet).

Test disconnects before play response, during a cascade, in a feature, and around settlement. A client that animates correctly but can place another bet while settlement is uncertain is not ready. For issue reports, attach a synthetic or sanitized replay fixture, never a live session URL.
