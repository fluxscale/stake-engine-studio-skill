# Game development workflow

## Establish the contract before generating outcomes

Write down game mechanics, board geometry, symbol behavior, modes and costs, target RTP, maximum payout, and whether the frontend is SDK-based or custom. Identify who owns the math-to-frontend event schema. Keep this short for an existing game; inspect its implementation instead of making the user restate it.

Engine accepts compatible static outputs from custom toolchains. The RGS samples a precomputed outcome by weight and returns its events. A sequence can include cascades, free spins, and animations, but the wager outcome cannot depend on a later client decision. Do not design cross-bet accumulation, progressive jackpots, gamble extensions, or early cashout into a Studio submission without resolving the platform incompatibility. Sources: [overview](https://studio.engine.io/docs), [general requirements](https://studio.engine.io/docs/approval-guidelines).

## Choose a starting point

Use an official sample with the nearest win mechanism, then replace mechanics and assets deliberately. Sample categories include lines, ways, cluster/scatter cascades, expanding wilds, and the minimal fifty-fifty RGS example. Inspect the checkout for actual sample names; the docs' prose count does not necessarily match the current repository. Sources: [examples](https://studio.engine.io/docs/math/example-games), [RGS example](https://studio.engine.io/docs/rgs/example).

For a new math checkout, the documented starting commands are:

```sh
git clone https://github.com/engineio/math-sdk.git
cd math-sdk
make setup
make run GAME=0_0_lines
```

Read the selected game's `run.py` before running it: simulation count, optimization, threads, and compression determine cost and runtime. Python >=3.12 is required at the recorded SDK baseline. Rust/Cargo is needed for its Rust optimizer, not for every frontend task. `make setup` creates the environment; activate it in the current shell when running commands outside the Makefile. Sources: [setup](https://studio.engine.io/docs/math/setup), [SDK README](https://github.com/engineio/math-sdk).

## Develop in observable slices

1. Generate a small deterministic set of readable books; exercise loss, small win, feature entry, and cap behavior.
2. Validate the event schema and payout totals. Keep the same fixture usable by math diagnostics and frontend stories.
3. Implement playback and UI for that fixture. Add real RGS authentication only when the rendering boundary is understood.
4. Generate a diverse production candidate, optimize weights, and analyze the final selected tables.
5. Build static assets, test through a Studio test session, verify public replay, and prepare a submission report.

This is a development workflow, not a fixed platform sequence. Existing projects may start at any step. Never treat a tiny smoke dataset as production statistical evidence.

## Separate identities

| Identifier | What it identifies |
| --- | --- |
| Game ID | The game in Studio; different from a local folder/display title |
| Mode name | Exact key shared by published index, frontend selector, and play request |
| Math version | Published outcome population and weights |
| Frontend version | Rendering build submitted or launched |
| Simulation/event ID | A particular recorded outcome within a math mode/version |
| Active round | A wager lifecycle held by the RGS |

Track these in a release record. A working local game with the wrong published math version can fail even when both artifacts pass their own unit tests.
