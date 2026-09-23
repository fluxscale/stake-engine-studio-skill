# RGS game-client integration

## Startup and transport

Parse `sessionID`, `rgs_url`, `lang`, `device`, and social/replay parameters from the launch URL. Use the supplied RGS host rather than a hardcoded example. Validate URL structure, preserve the intended host, and keep tokens out of logs or public reproduction URLs. Detect public replay before creating a client that authenticates or polls. Source: [RGS details](https://studio.engine.io/docs/rgs).

Normal play authenticates first. A resumed `round` can be active or merely the last completed round; check state rather than assuming any returned round needs settlement. Source: [wallet](https://studio.engine.io/docs/rgs/wallet).

| Operation | Method/path | Request fields | Result to handle |
| --- | --- | --- | --- |
| Authenticate | `POST /wallet/authenticate` | `sessionID` | Balance, bet configuration, jurisdiction flags, prior/active round |
| Balance | `POST /wallet/balance` | `sessionID` | Authoritative balance |
| Play | `POST /wallet/play` | `sessionID`, integer `amount`, exact `mode` | Balance and selected round |
| End active round | `POST /wallet/end-round` | `sessionID` | Settlement balance |
| Record progress | `POST /bet/event` | `sessionID`, `event` | Saved progress marker |

Treat the table as a route map; read current schemas and installed types for optional fields. A play call changes wallet state; documentation research does not authorize placing a wager.

## Units and configuration

Wallet amounts use six decimal places: `1_000_000` represents one currency unit, including currencies whose display has zero or three decimals. Bet-mode cost changes the debit: base amount × mode cost. Stored book multipliers use hundredths; API multipliers are a separate representation. Trace conversions once at each boundary and guard JavaScript safe-integer limits. Sources: [RGS money and modes](https://studio.engine.io/docs/rgs), [math artifacts](math-artifacts.md).

Use returned `minBet`, `maxBet`, `stepBet`, `defaultBetLevel`, and `betLevels` to populate/validate controls. Test a non-USD configuration and the smallest bet. Do not treat sample JSON amounts as production defaults or multiply cost twice.

## Round lifecycle and recovery

Model authentication, idle, submitting, animating, settling, recovery, and error states explicitly. Only one play request should be in flight. A timeout does not establish whether the server accepted a bet: stop additional wagers and reconcile using the supported session/round flow before retrying.

End-round timing depends on active state and resumability. The generic docs describe closing after playback, while SDK flows can close some single-round wins earlier and retain bonus rounds through playback. Inspect the installed `createPrimaryMachines`/client implementation. Do not double-close auto-closed losses or close a resumable bonus merely to enable the next spin. Sources: [web SDK lifecycle code](https://github.com/engineio/web-sdk/blob/main/packages/utils-xstate/src/createPrimaryMachines.ts), [client implementation](https://github.com/engineio/ts-client/blob/main/src/client.ts).

`/bet/event` records presentation progress; it does not select a different outcome or settle a wager. Reconcile displayed counters and authoritative balance after reconnect. See [replay and recovery](replay.md).

## Errors and useful diagnostics

| Signal | Investigation |
| --- | --- |
| `ERR_IS` / `ERR_ATE` | Session lifecycle, authentication order, expired or incorrect launch parameters |
| `ERR_VAL` | Body schema, amount units, allowed step/range, mode name/version |
| `ERR_IPB` | Authoritative balance and total mode cost |
| `ERR_GLE` / `ERR_LOC` | Limits or location decision; communicate it rather than bypassing it |
| `ERR_GEN` / `ERR_MAINTENANCE` | Service state; stop play and present recovery options |
| Network failure after play | Unknown wager outcome; reconcile before a new request |

Capture the actual HTTP status and structured error; docs variants differ on status examples. Do not reduce all failures to “try again.” Redact tokens while retaining mode, build versions, endpoint, timestamp, request amount, and response error code. Sources: [wallet errors](https://studio.engine.io/docs/rgs/wallet), [source play page](https://github.com/engineio/docs/blob/main/src/routes/docs/api/play/+page.svx).

## TypeScript client

The npm package is `stake-engine`; the repository is `engineio/ts-client`. Inspect `src/index.ts` or installed `.d.ts` before importing helpers. The recorded source exports `RGSClient`, `DisplayAmount`, `ParseAmount`, and `parseBalance`; README helper lists are not identical to public exports. At that revision the balance event is `balanceUpdate`. Track listener cleanup and polling ownership. Source: [client exports](https://github.com/engineio/ts-client/blob/main/src/index.ts).
