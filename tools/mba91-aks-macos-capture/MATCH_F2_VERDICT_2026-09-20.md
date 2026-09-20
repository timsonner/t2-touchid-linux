# F2 verdict: positive authorized match on MBA91 (2026-09-20)

Branch: `research/mba91-aks-ep7`. All live gates disabled in source.
Shapes/statuses/counts only — no payloads, no keybags, no passwords,
no identity UUIDs.

## Verdict

**First positive Touch ID match from Linux on MacBookAir9,1.**
Same F1 framing, same right index with careful flat placement and
full-window hold: `match_start_status` 0 → 27 events → terminal
3268 B `match_result` with `matched: true`. F1's `false` was
placement, not identity or binding scope. The credential-set lens is
now a proven end-to-end match path on this Air, and the H2 session
proxy is retired for *verification* (74 remains closed and
irrelevant to this path).

## Run (single shot, operator-run, finger present)

- Preconditions carried over from F1 (minimal module, keybag
  session, both bags unlocked); fingerless baseline re-verified
  before the window (`0x42`=2, repeat-equal true).
- ACM: preflight type 1, operator password bound, final
  policy-1007 SATISFIED. Fresh tracking context, mandatory cleanup.
- Warm gate true (`0x42` count 2 uid 501). Prelude all status 0
  (same S1 shapes as F1).
- Match request: identical to F1 (112 B, flags `0x4009`, 16 B
  external form, 2 selected records).
- Events (27): `status` ordinals 53/80/73/64/90/63/55/72/95/91,
  `statistics` throughout, one `sks_lock_state`, terminal
  `match_result` 3268 B `matched: true`. Note ordinal 73 with
  3242 B status early — a finger-present signature absent from the
  mute windows; analysis-only observation, no claim beyond that.
- `cancel_status`: 0. `identities_preserved`: true.
- Post-window re-verify: `0x42`=2, global 2, reconciled true,
  repeat-equal true, free 1, SKS `520` (`0x208`), gate complete.

## F1 + F2 joint reading

| Window | Finger | Placement | Result |
|---|---|---|---|
| F1 | right index | normal | `match_result`, `matched: false` |
| F2 | right index | careful flat, full hold | `match_result`, `matched: true` |

Same identity, same framing, same session shape — only placement
changed. The matcher evaluates contact quality truthfully; there is
no per-finger allowlist surprise and no binding-scope block on the
presented identity.

## Next steps (resume here)

1. **Negative control (one gated window, same framing):** present a
   known-unenrolled finger, expect `match_result` `matched: false`
   (or clean no-match). Proves selectivity — the positive is real
   discrimination, not always-yes. This is the last scientific gate
   before product talk.
2. **Then:** named/single-identity selection, repeatability across
   reboots (warm handoff already preserves `0x42`), and only then
   any fprintd/PAM productization discussion — reusing the proven
   MBP16,2 broker discipline, not inventing a new one.
3. **Do not:** touch 74 (closed, and now moot), spray variants,
   enroll/load/reset/delete, default-param warm insmod.
4. Attribution stands: match framing adapted from macintog/t2touch
   (`build_match_request`, flag `0x08`); verified live on MBA91
   here for the first time.
