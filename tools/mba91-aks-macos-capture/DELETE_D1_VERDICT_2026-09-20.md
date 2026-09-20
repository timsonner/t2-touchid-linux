# D1 verdict: delete refused at dispatch, state untouched (2026-09-20)

Branch: `research/mba91-aks-ep7`. All live gates disabled in source
(verified). Shapes/statuses/counts only — no UUIDs, no payloads.

## Verdict

**`0x0d` v0/val0 with the exact T-proven 20 B record refused
`0xe00002c2`, zero events, 3→3 unchanged.** The halt worked as
designed: journaled intent, single dispatch, no replay, state
triple-verified intact after. The ladder pauses here — D1 answered
"not this shape", not "deleted".

## Run (single shot, operator-run, no finger needed)

- Warm gate true (`0x42`==3). Intent journaled to operator-private
  storage BEFORE dispatch (record index 2, pre-count 3).
- `0x0d` v0/val0 + 20 B record → status **`0xe00002c2`**
  (signed -536870206 — the same bad-argument vocabulary as C3's
  ver-2 74 and the 52 B enroll bug), 0 events.
- Best-effort cancel 0. Post-`0x42`==3, records byte-identical.
  Nothing was deleted, nothing moved.

## Reading (honest candidates, unranked)

1. **Version axis** (cheapest): the v0 comes from never-live-tested
   broker code; this SEP may want v1 (the `biometric_command`
   default everywhere else). One D2 window with v1 decides it.
2. **Value/capacity framing**: v0/val0/cap0 is assumed from the
   untested adapter, not from capture (no delete exists in any
   capture — nothing was ever deleted on this machine).
3. **Authorization**: deletion may need a credential-bound or
   unlocked-deeper session than K-state; D1 ran credential-free
   per the broker's claim, unproven here.
4. **Opcode mapping**: 0x0d-as-delete is inherited knowledge,
   never observed live on this build.

## Next steps (resume here)

1. **D2 (one window, same gates + delete ack):** identical D1 with
   version=1. Refusal vocabulary decides: another `0xe00002c2`
   kills the version axis (graduate to value/capacity or auth
   variants, one variable at a time); 0 opens the delete track.
2. **Do not:** replay v0 (answered), combine variables, touch the
   other two records (macOS prints — T-proof is the only thing
   standing between D-series and permanent loss), reset,
   `0x40`/`no_catacomb`.
3. The nuke talk stays parked behind a working single delete:
   without D-series success there is no safe path to empty SEP.
