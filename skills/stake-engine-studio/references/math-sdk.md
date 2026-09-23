# Math SDK implementation

## Locate responsibilities

Game-specific rules live under `games/<game>/`; common infrastructure lives under `src/` and `utils/`. Inspect the actual inheritance chain before overriding methods. The reference architecture separates configuration, orchestration, game calculations, and executables; forked SDKs may restructure them. Sources: [game structure](https://studio.engine.io/docs/math/high-level-structure/game-structure), [state machine](https://studio.engine.io/docs/math/high-level-structure/state-machine), [directory](https://studio.engine.io/docs/math/sdk-directory).

| Area | Inspect/change | Evidence to retain |
| --- | --- | --- |
| Configuration | `GameConfig`, reel strips, paytable, dimensions, special symbols | A compact mechanics table matching the in-game rules |
| Modes | `BetMode` cost, target RTP, cap, buy/feature/auto-close flags | Exact mode names shared with the frontend and index |
| Simulation | `run_spin`, reset/seed logic, acceptance conditions | A reproducible ID/seed and resulting book |
| Win evaluation | Lines/ways/clusters/scatters, multiplier ordering | Hand-computable board fixtures |
| Event output | Serializing board, wins, feature counters, final amounts | Ordered JSON events and cumulative totals |
| Publication | Books, lookup tables, manifest | ID and payout integrity report |

## Configuration and mode semantics

Define symbol names consistently across reels, paytables, and special-symbol attributes. The configuration documentation uses `(kind, symbol)` keys for payouts, optional grouped ranges, and per-game-type reel weights. A purchased mode is not the same concept as the internal `basegame`/`freegame` state. Sources: [configs](https://studio.engine.io/docs/math/game-state-structure/setup/configs), [BetMode](https://studio.engine.io/docs/math/game-state-structure/setup/betmode).

`is_feature` influences persistent mode selection; `is_buybonus` informs frontend presentation; `auto_close_disabled` affects whether even a zero-win round may need manual closure for resumability. Check the installed implementation and actual `round.active`; do not derive end-round behavior from payout alone.

Distributions partition simulation criteria and quotas. Quotas control generated coverage, not final player-facing probability after optimization. Conditions can bias reel selection and force feature/cap outcomes; impossible acceptance conditions can cause endless retries. The default forced flags may be omitted, but required reel conditions and criteria must be satisfied. Sources: [distribution](https://studio.engine.io/docs/math/game-state-structure/setup/distribution), [acceptance](https://studio.engine.io/docs/math/game-state-structure/simulation-acceptance).

## Board and symbol invariants

Inspect reel-major versus row-major layout and whether reveal payloads include padding symbols before translating coordinates. Update special-symbol indexes after a custom board mutation. Reusing a mutable symbol object across cells can leak attributes; verify each cell's identity and reset behavior. Sources: [active board](https://studio.engine.io/docs/math/game-state-structure/board), [symbols](https://studio.engine.io/docs/math/game-state-structure/symbols).

For cascades, check the remove/refill boundary, surviving top symbols, repeated scatter checks, and multiplier persistence. A board rendered with an off-by-one padding offset can appear to disagree with correct math. For each mechanic, use the actual calculator's documented semantics:

- [Lines](https://studio.engine.io/docs/math/source-files/calculations/lines): line eligibility, substitution, winning symbol choice, multiplier application.
- [Ways](https://studio.engine.io/docs/math/source-files/calculations/ways): reel eligibility, combinations, and duplicate counting.
- [Clusters](https://studio.engine.io/docs/math/source-files/calculations/cluster): adjacency, thresholds, and wild participation.
- [Scatter](https://studio.engine.io/docs/math/source-files/calculations/scatter): anywhere counts and payout bands.
- [Tumble](https://studio.engine.io/docs/math/source-files/calculations/tumble): removed symbols, refill, and termination.
- [Board utilities](https://studio.engine.io/docs/math/source-files/calculations/board): draw/force functions and geometry.

## Wins and events

Keep per-action, per-spin, and per-round amounts separate. A feature containing multiple spins accumulates into one round. Verify that caps, resets, and finalization produce the same payout in the book and CSV. Read [win manager](https://studio.engine.io/docs/math/source-files/win-manager), [game wins](https://studio.engine.io/docs/math/game-state-structure/wins), and [events](https://studio.engine.io/docs/math/game-state-structure/events).

Serialize only the data the renderer needs; do not mutate already-recorded events through shared object references. Keep event order/index conventions consistent. After introducing a new event, implement the corresponding [frontend handler and fixtures](frontend.md).

Use [force files](https://studio.engine.io/docs/math/game-state-structure/force-files) to locate rare criteria and record useful analysis keys. Force records, simulation IDs, and published books have different purposes; do not assume each auxiliary record maps by array position. Run small simulations first, inspect rejected criteria, then scale. Refer to [executables](https://studio.engine.io/docs/math/source-files/executables), [outputs](https://studio.engine.io/docs/math/source-files/outputs), and [utilities](https://studio.engine.io/docs/math/utilities) for the selected revision's pipeline.
