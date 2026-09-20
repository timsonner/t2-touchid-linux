# K1 verdict: token-free match emits a positive verdict with unlocked keybags (2026-09-20)

Branch: `research/mba91-aks-ep7`. All live gates disabled in source
(verified on disk after the windows). Shapes/statuses/counts only —
no payloads, no keybags, no passwords, no identity UUIDs.

## Verdict

**K1 returned a verdict, not mute — and a positive one.** The exact
Fork-A token-free shape (flags 0, counted blob, no credential set,
no ACM context) that stayed silent across 6 windows in September
emitted a terminal 3268 B `match_result` with the enrolled template
present (`matched: true`) against the presented enrolled finger.
Per the broker decision tree, the broker may be **password-free at
match time**: unlocked keybags appear sufficient, and the PAM-capture
direction is on hold pending one isolation experiment below.

An operator-run F1 positive control (credential-set framing, same
finger) immediately preceded K1 on the same boot and also returned
`matched: true`, so both framings verify side-by-side in one epoch.

## Runs (two windows, same boot, same finger, back-to-back)

Control — F1 re-run (operator-enabled gate, restored to disabled
after; tree verified clean): policy-1007 live, 112 B `0x4009`
framing, start 0 → 35 events → `match_result` 3268 B
`matched: true`, cancel 0, identities preserved.

K1 — token-free via the standard probe (no gate in that tool, no
source changes anywhere):
`bridge-xpc-probe.py --initialize --identity-list --match-seconds 30
--stop-on-match-result` → `0x42` count 2, `match_start` status 0,
cancel 0, 27 events: `status` ordinals
53/80/73(3242 B finger-present signature)/64/90/63/55/72/95/91/74,
`statistics` throughout, terminal `match_result` 3268 B
(`0xe3ff8002`, v2) with `contains_enrolled_identity_uuid: true`,
`matched: true`. Note the trailing 36 B `status` ordinal-74 event
*after* the verdict — first sighting; serviceStatus ordinals live in
a different namespace than Mesa opcodes, so this is an observation,
not a 74-track reopening.

Post-windows inventory: `0x42`=2, repeat-equal true, SKS `0x208`,
gate complete. No state damage.

## Reading (honest confounds)

Two variables changed since September's mute, and K1 cannot
separate them:

1. **Keybag state.** September ran with EP7 parked and no `/run`
   session (explicitly documented); K1 ran minutes after both bags
   were operator-unlocked (`status=0`). Unlocked keybags are the
   prime suspect for the difference.
2. **Matcher priming.** K1 ran ~1 minute after a successful
   authorized match on the same boot. Prior F1/F2/R1 windows may
   have left adaptive template state or a primed matcher; a
   token-free verdict could be riding that wake rather than the
   keybag state alone.

## Next steps (resume here)

1. **K2 isolation (one gated session, fresh boot):** loader
   bring-up → unlock → fingerless baseline → token-free match
   FIRST, before any authorized window. Verdict → unlocked keybag
   suffices, broker needs no password plumbing. Mute → the
   priming/authorization hypothesis wins and the PAM-capture
   broker direction stands.
2. **Do not:** treat K1 as proof the broker is solved (confounded),
   touch 74, spray variants, enroll/load/reset/delete,
   default-param warm insmod.
