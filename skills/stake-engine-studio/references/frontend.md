# Frontend SDK and custom renderers

## Start with the actual workspace

[engineio/web-sdk](https://github.com/engineio/web-sdk) uses Svelte 5, PixiJS 8, and Turborepo. At the recorded revision its root manifest requires Node >=22.16.0 and specifies pnpm 10.5.0; the older Studio setup page differs. Honor the checkout's `engines`, `packageManager`, and lockfile.

```sh
pnpm install
pnpm run storybook --filter=lines
pnpm run dev --filter=lines
pnpm run build --filter=lines
```

`lines` is a sample workspace package name. Inspect the target `package.json` before using it. Root commands delegate through Turbo; check which package scripts actually exist before promising lint/typecheck/test coverage. Source: [getting started](https://studio.engine.io/docs/front-end/getting-started), [upstream package manifest](https://github.com/engineio/web-sdk/blob/main/package.json).

## Trace an outcome through the renderer

```text
Published math book / RGS round.state
  -> ordered book events
  -> playBookEvents / bookEventHandlerMap
  -> synchronous or awaited emitter events
  -> component subscriptions
  -> animations, counters, and final presentation
```

A book event describes the recorded game outcome. An emitter event coordinates local UI work; it must not alter the payable result. Wait for animations only where ordering requires it. A handler that never resolves can stall the next event or round completion. Sources: [flowchart](https://studio.engine.io/docs/front-end/flowchart), [task breakdown](https://studio.engine.io/docs/front-end/task-breakdown).

## Add an event end to end

1. Capture a real math event and its surrounding book; specify fields, units, and ordering.
2. Add it to `typesBookEvent.ts` and the handler map.
3. Add required component emitter types and include them in the game emitter union.
4. Implement subscriptions with mount/unmount ownership and completion behavior.
5. Add an isolated event story and a full-book story using the captured fixture.
6. Exercise normal speed, turbo/skip if supported, replay, and interrupted-round recovery.

Example filenames are relative to `apps/<game>/src/`; confirm them in the checkout. Do not copy placeholder event data with a missing `index` into a schema that requires it. Source: [adding new events](https://studio.engine.io/docs/front-end/adding-new-events).

## State, layout, and assets

The SDK's contexts cover event emission, layout, game state machines, and app/assets. Canvas positions depend on container coordinates and anchors; viewport resize does not reflow Pixi components like HTML. Use state-machine state to disable invalid controls, not scattered booleans that can disagree during resume. Source: [context](https://studio.engine.io/docs/front-end/context).

Inspect app-specific code under `apps/` and shared helpers under `packages/`. Keep a one-game mechanic local unless multiple games need it. Source: [file structure](https://studio.engine.io/docs/front-end/file-structure).

UI packages are starting points. Replace sample artwork and establish the game's own presentation before submission. A custom React, vanilla, or other renderer remains valid if it exports static files and honors the RGS contract. Do not install Svelte solely to comply with this skill. Source: [UI](https://studio.engine.io/docs/front-end/ui).

## Verify at the appropriate level

| Check | What it catches |
| --- | --- |
| Component and emitter story | Geometry, animation completion, reset behavior |
| Single book-event story | Payload wiring, field units, sequencing |
| Full recorded book | Cumulative wins, feature transitions, cap handling |
| Static local build | Missing files, nested base paths, external asset dependencies |
| Studio test session | Authentication, bet levels, active rounds, real payload shape |
| Session-free replay | Startup branching and repeatable presentation |

Storybook is explicitly designed to test components, individual events, and complete books. A passing story alone does not validate wallet integration. Source: [Storybook](https://studio.engine.io/docs/front-end/storybook). For production checks use [approval](approval.md) and [publishing](publishing.md).
