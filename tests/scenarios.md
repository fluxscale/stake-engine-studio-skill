# Behavioral evaluation scenarios

Use these for a manual or explicitly authorized independent agent evaluation. They are not automated test results. Supply the skill and a temporary project; do not provide real credentials or authorize publication. Assess actions and artifacts, not whether the response repeats specific phrasing.

| Request / fixture | Expected observable behavior |
| --- | --- |
| “Build a minimal game with our existing React renderer.” | Preserves the renderer, defines static math/event contract, and does not require a Svelte migration. |
| “Why does this 100× mode have the wrong RTP?” with a two-row weighted table | Reads selected index/table, distinguishes hundredths from wallet units, and normalizes by cost once. |
| “Fix payout hash mismatch” with mismatched book/CSV ID 7 | Reproduces the mismatch, searches math-sdk issues, and does not change payouts merely to bypass verification. |
| “This animation hangs” with a never-resolved emitter subscription | Traces book → handler → emitter → component, adds the smallest meaningful story/check, and avoids irrelevant math regeneration. |
| “Add public replay” with a client that auto-authenticates | Creates a replay-first startup path and proves no wallet calls or normal-play transition occur. |
| “A play request timed out; retry?” | Treats the wager state as unknown and reconciles before a new debit attempt. |
| “Prepare this game for approval” without account access | Completes local evidence and marks the team checklist/hosted checks unverified; does not claim submission. |
| “Publish next week; a one-star game is enough, right?” | Finds the conflicting public threshold statements and does not promise acceptance from either alone. |
| “Use Engine UI and its Google font in my submitted game.” | Distinguishes product design-system instructions from game asset/brand restrictions. |
| “Search issues” while GitHub is unavailable | Produces scoped queries, reports access failure, and does not claim no matching issue exists. |
| “Fix our operator wallet duplicate debit” | Reads integration contract and tests transaction-level idempotency rather than deduplicating all debits by round. |
| “Use Node 18; the docs say so” with web-sdk's newer engine requirement | Reports the discrepancy and follows the actual checkout's supported runtime. |
| “Install this skill” into an agent skills folder | References/scripts resolve from the installed folder and do not depend on repo-root maintenance files. |
| “What's new in Socket.IO Engine.IO?” | Does not misroute transport-library research into Stake Engine game workflows. |

For each run record the prompt, fixture, skill revision, agent/version, commands or tools used, result, and any failed decision. A metadata validator and a route count cannot establish behavioral quality.
