# Math publication artifacts

The authoritative contract is [Required Math File Format](https://studio.engine.io/docs/math/math-file-format). One mode needs a manifest entry, a CSV lookup table, and a Zstandard-compressed JSONL book. A schematic example:

```json
{
  "modes": [
    {
      "name": "base",
      "cost": 1.0,
      "events": "books_base.jsonl.zst",
      "weights": "lookUpTable_base_0.csv"
    }
  ]
}
```

The documented CSV examples have no header; the helper enforces that shape: `simulation_id,weight,payout`. Each value is an unsigned 64-bit integer. The [overview](https://studio.engine.io/docs) describes sampling in proportion to weight; consequently weights are relative and their sum need not be one. Every book record requires integer `id`, array-of-object `events`, and integer `payoutMultiplier`. The CSV payout must exactly equal the corresponding book payout. In stored books, `1150` means `11.5×`, not 1,150 currency units. Do not confuse this representation with API/replay multipliers.

## Preflight sequence

Run from the installed skill directory:

```sh
python3 scripts/inspect_math.py /path/to/game/library/publish_files
python3 scripts/inspect_math.py /path/to/game/library/publish_files --books
```

The first command checks the manifest, contained file paths, CSV structure/uniqueness, nonzero total weight, and weighted statistics. It does not decompress books. The second also checks every JSONL record and ID-to-payout equality, using a temporary SQLite database to avoid retaining millions of IDs in RAM. Install `zstandard` in the chosen Python environment to use `--books`; the script never installs packages for you.

Output is JSON. Exit `0` means the requested checks passed; exit `1` reports invalid input or an expected file/database failure (`kind: invalid`); argument errors exit `2`; unexpected helper failures exit `3` (`kind: internal_error`). The report states whether book verification ran. Weighted summaries include zero-weight record counts, recorded/reachable maximum payouts in hundredths and base-bet multiples, and population variance/standard deviation. `payout_std_dev_base_bets` uses payout divided by 100; `payout_std_dev_per_mode_cost` additionally divides by mode cost. These units are deliberately distinct. Duplicate JSON keys, including nested event keys, are rejected. Shared resolved book/table paths across modes produce `shared_artifact` warnings for review, without inventing a platform prohibition. Paths that resolve outside the publication directory, including escaping symlinks, are rejected as a local packaging safeguard.

## What the helper does not certify

- Individual event payload semantics, visual correctness, rulebook accuracy, and replay behavior.
- Approval RTP/risk thresholds, jurisdiction suitability, platform file limits, or operator exposure rules. Re-read current requirements separately.
- Correct rounding of every monetary calculation in the frontend or exact parity with Studio statistics.
- ZIP structure, upload integrity, remote processing, approval, or production availability.

It streams the full CSV and, when requested, the full decompressed books; large artifacts can require substantial time and temporary disk. It does not sample and then claim a full pass. Use a small fixture during development and the complete candidate before publication.

Keep the index and its referenced artifacts from the same generation. Build into a fresh output directory so stale bonus files cannot be mistaken for the selected release. Run the installed SDK's RGS verification routines as well when available; inspect their interface in the current checkout rather than importing a guessed entry point.
