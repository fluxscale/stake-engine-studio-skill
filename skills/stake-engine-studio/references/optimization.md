# Optimization and statistical verification

## Work from published weights

Let `w_i` be the integer weight, `p_i` the stored integer payout, and `c` the mode cost multiplier. Define `W = sum(w_i)`, `q_i = w_i / W`, and `x_i = p_i / 100` in base-bet multiples. For `W > 0`:

```text
Expected payout per base bet = sum(q_i * x_i)
RTP fraction                 = sum(q_i * x_i) / c
Non-zero hit probability     = sum(q_i where p_i > 0)
Hit interval                 = 1 / hit probability
Variance of base-bet payout  = sum(q_i * x_i²) - E[x]²
```

These are derived diagnostics, not a substitute for Studio's risk implementation. State the normalization and whether RTP is a fraction or percentage. With two equally weighted payouts of `0` and `190`, cost `1`, RTP is `95%`; with cost `100`, the same payouts yield `0.95%`. This synthetic example is an arithmetic check, not a publishable game.

Calculate using the files referenced by `index.json`, after optimization or lookup swapping. Unweighted simulation averages and the target RTP in configuration do not establish the published RTP. Positive-weight outcomes determine achievable wins; distinguish a book's largest recorded payout from the largest selectable payout. Sources: [static math model](https://studio.engine.io/docs/math), [file format](https://studio.engine.io/docs/math/math-file-format).

## Rust optimizer

The Math SDK optimizer adjusts outcome selection weights. Its conditions assign simulation IDs to exclusive groups in order, so put specific overlapping criteria, such as a win cap, before broader feature criteria. Check the relationship among RTP allocation, average win, and hit probability before tuning. Aggressive scaling can make a target infeasible. Rebuild the Rust binary when changing its source; inspect the checkout's `Cargo.toml` location before invoking `cargo build --release`. Source: [optimization algorithm](https://studio.engine.io/docs/math/optimization-algorithm).

When optimization fails or produces surprising results:

1. Check coverage of each required criterion and whether it contains suitable nonzero outcomes.
2. Verify mode cost and payout units in the target and input data.
3. Confirm the optimizer read the same generation of books and tables.
4. Compare each output ID/payout pair against the original books; weight changes must preserve payout identity.
5. Analyze the chosen candidate, rather than assuming the first generated candidate was selected.

If a mismatch appears, preserve both artifacts and a minimal failing ID. Do not repair it by rewriting the payout to silence a hash check. Search [upstream issues](issues.md) with the exact error and installed revision.

## Alternative convex optimizer

[engineio/convex-optimizer](https://github.com/engineio/convex-optimizer) is a separate CVXPY-based tool with a Streamlit UI. Its README starts with `make setup` and `streamlit run src/app.py`. Inspect its input loader, constraints, and exporter before passing Math SDK files to it. Do not assume it shares Rust configuration classes or emits the same manifest. Preserve the same ID/payout and unit invariants at the export boundary.

## Produce useful evidence

For every mode, retain cost, weighted RTP, supported positive-weight outcomes, nonzero hit rate, cap probability, distribution gaps, and payout standard deviation with units. Analyze tails and exposure using the current [math approval page](https://studio.engine.io/docs/approval-guidelines/math-verification); its CVaR, ETL, and tier penalty definitions are not interchangeable with ordinary variance.

Cross-mode RTP wording in the live page mixes a variation statement with a base-centered example. Calculate both base deviations and the full min-to-max spread, and report the actual numbers for review. Do not silently choose a permissive interpretation.

Use the SDK's PAR-sheet/analysis routines when their required records exist. Save the source artifact hashes and analysis command alongside the report so the results remain tied to a candidate version. Source: [analysis utilities](https://studio.engine.io/docs/math/utilities).
