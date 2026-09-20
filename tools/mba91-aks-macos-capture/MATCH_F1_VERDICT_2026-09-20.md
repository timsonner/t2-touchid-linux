# F1 verdict: credential-set-bearing match converts mute to verdict (2026-09-20)

Branch: `research/mba91-aks-ep7`. All live gates disabled in source.
Shapes/statuses/counts only — no payloads, no keybags, no passwords,
no identity UUIDs.

## Verdict

First `match_result` ever observed on this Air. The credential-set
variable is the lever: token-free Fork-A windows (flags 0, 60 zero
bytes) stayed mute across 6 windows incl. 60 s continuous contact;
the authorization-bearing framing emits a terminal 3268 B
`match_result` verdict. The mute was missing authorization, not a
dead sensor or a wrong opcode.

The verdict itself is negative (`matched: false`) — see reading below.
The conversion mute → verdict is the result; the verdict polarity is
the next question (F2), not a failure of this window.

## Run (single shot, operator-run, finger present)

- Prerequisites: minimal warm `insmod` set (survived, 3 nodes),
  keybag load → handle 1, both keybags operator-unlocked (status 0),
  fingerless baseline re-verified with module loaded (`0x42`=2,
  repeat-equal true, selftest PASS).
- ACM: policy preflight type 1 (passcode requirement), operator
  password bound via `t2-aks-tool`, `verify-password-acm` status 0,
  final policy-1007 SATISFIED. Fresh tracking context, mandatory
  cleanup by construction.
- Warm gate true (`0x42` count 2 uid 501). Prelude all status 0
  (`48`-empty → 1 B, `84` → 83 B, `39` → 4 B, `84` → 83 B,
  `12` → nil).
- Match request: 112 B = 68 B options (flags `0x4009` =
  unlock `0x01` | credential-set `0x08` | selected `0x4000`,
  uid 501, credlen 16, 16 B external form) + counted blob
  (count 2 + 2 x 20 B records from `0x42`).
- `match_start_status`: **0** (opened). 53 events: `sks_lock_state`
  x3, `status` ordinals (90/63/55/72/95/70/53 repeating),
  `statistics` throughout — then terminal `match_result`
  (3268 B, `matched: false`).
- `cancel_status`: 0. `identities_preserved`: true.
- Post-window re-verify: `0x42`=2, global 2, reconciled true,
  repeat-equal true, free 1, SKS `552` (`0x228`, new coloring,
  informational), gate complete.

## Reading (honest)

- `matched: false` against both selected records admits three live
  hypotheses: (a) presented finger was not either enrolled identity
  (SEP holds 2, both uid 501 — operator intent vs presented finger
  unverified); (b) placement/contact quality during the single
  window; (c) credential/session binding scoped to one identity.
  The window cannot distinguish these — it was designed to test
  mute-vs-verdict, which it answered decisively.
- What F1 did NOT show: any 258/22 refusal (opened cleanly), any
  state damage (all preservation checks green), any evidence the
  sensor path is dead (status-ordinal cycle + terminal verdict =
  a live matcher evaluating and rejecting).

## Next steps (resume here)

1. **F2 (one gated window, same framing):** deliberate finger
   selection — present the *other* enrolled finger, or the same
   finger with careful flat placement and full-window hold. A
   `matched: true` proves end-to-end authorized match on MBA91 and
   retires the proxy track for verification. A second `false`
   narrows to binding/placement hypotheses.
2. **Do not:** re-run F1 unchanged (answered), spray payload
   variants, touch 74 (closed matrix stands), default-param warm
   insmod (killer), enroll/load/reset/delete.
3. The t2touch construction credit (`build_match_request`, flag
   `0x08`) is recorded in the F1 probe docstring; license family
   is the same (GPL).
