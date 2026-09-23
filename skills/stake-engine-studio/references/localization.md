# Localization, social mode, and jurisdiction behavior

## Separate presentation from wallet arithmetic

Currency formatting does not change the RGS integer scale. Keep calculations in API units and format only at the display boundary. Test a zero-decimal currency, a three-decimal currency, a social token, and an unknown code fallback. Very small bet wins can require more displayed precision than the balance. Source: [RGS currency and minimum-bet guidance](https://studio.engine.io/docs/rgs).

Initialize bet controls from the authenticated currency configuration, not USD assumptions. The live response and installed types are authoritative for flags such as disabled fullscreen/turbo. Apply restrictions to keyboard shortcuts and autoplay paths as well as visible buttons. Source: [wallet configuration](https://studio.engine.io/docs/rgs/wallet).

## Social copy is a separate content variant

Studio signals social casino launch with `social=true`; it recommends separate `sweeps_<lang>` copy. The [public source social page](https://github.com/engineio/docs/blob/main/src/routes/docs/reference/social-mode/+page.svx) instead specifies English replacements regardless of `lang`. Verify the current target requirements before selecting a language strategy. Source: [Studio jurisdiction requirements](https://studio.engine.io/docs/approval-guidelines/jurisdiction-requirements).

Read the live restricted-phrase list when preparing a review. Common transformations include bet → play, money/cash → coins, and wager/gamble → play, but these examples are not the complete policy. Match full phrases before shorter words; a blind substring replacement can corrupt ordinary text. Prefer authored message catalogs and meaningful context rather than replacing words in rendered DOM.

Audit rules, paytables, buttons, tooltips, error messages, feature menus, autoplay confirmations, replay results, and text baked into images or audio. Search source strings and inspect visible output. A JSON translation scan cannot certify artwork.

## Language fallbacks

English is required in the Studio communication guidance. Unsupported `lang` values should fall back cleanly; they must not produce undefined text or broken layout. Preserve raw server identifiers while localizing display names. Do not translate mode keys, event types, session tokens, or currency codes. Source: [RGS communication](https://studio.engine.io/docs/approval-guidelines/rgs-communication).

For every added language, inspect text expansion, number formatting, pluralization, line wrapping, and loading states. Test social mode and public replay independently from normal play. Document any unavailable translations or unresolved rule differences in the submission report; do not label a partial language audit complete.
