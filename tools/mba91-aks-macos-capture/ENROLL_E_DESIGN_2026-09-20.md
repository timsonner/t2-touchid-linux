# Enroll E-series design: unblocking 0x03 on MBA91 (2026-09-20)

Branch: `research/mba91-aks-ep7`. **Paper only — no code, no live
windows, no state touched.** Follows the t2touch construction survey.
Shapes/statuses/counts only.

## Standing state (2026-09-13, unchanged since)

- Token-free `0x03` uid 501 → start rejected **-3**, no events, no
  state change, with and without sensor context. Pure dispatch gate.
- Authorized `0x03` v2 68 B (fresh tracking context, policy-1007
  SATISFIED, full session prep green) → **22**, with legacy
  `0x01` context also 22. Generation ruled out.
- `0x0e` opens 0 with empty input, zero events fingerless or held —
  an armed channel needing the start first.
- Capture truth (ENROLL_ARG_SHAPES_2026-09-13): macOS sends `0x03`
  v2 68 B token once, then `0x0e` x8 ALL EMPTY, then save cluster,
  then post-`4`. Our 68 B was refused; contents or session differ.
- Capacity on this Air: max 5, free 1 — room for exactly one new
  identity. A success is a deliberate SEP mutation (3rd identity,
  uid 501, operator's own finger — inside Track A scope).

## The 4-byte finding

t2touch's working v2 layout
(`t2_enrollment_protocol.py: SensitiveEnrollmentRequest`):
`(flags=0, uid, 0, 16)` + 16 B form + **36 zero bytes**.
Ours (`bridge-xpc-authorized-enroll.py:233`): identical header,
identical form placement, but bytes [48:52] are `01 00 00 00`
(group u32 = 1) instead of zero. Their result-side analysis lists
both all-zero and `u32=1` 20 B groups as builtin — so this may be
nothing — but it is the ONLY known construction difference in the
start payload, and it costs one dispatch to falsify. (Note: an old
NEXT_STEPS line misnames our third header word; the code packs 0
in both — verified against source, not the note.)

## E-series (ascending cost, one shot each, never combined)

| ID | Shot | Gates | Prediction |
|---|---|---|---|
| E1 | `0x03` v2, their exact 68 B (zero group), fresh ACM context + cleanup, full session prep, **start-only**: if start opens 0, cancel immediately, post-`0x42` must still be 2, no finger dance | warm `0x42`=2 + repeat-equal, LIVE default-off + `--confirm-live` | 22 again (likely — group is result-side evidence) or 0 (track reopens) |
| E2 | Same as E1 with varied output capacity (capture never mined `0x03` out-cap; we used 0) | same, only if E1 22s | 22 or 0 |
| E3 | Authorized v1 48 B shape (their `SensitiveEnrollmentRequest` supports v1; our authorized attempts were v2-only) | same, only if E1+E2 22 | -3/22 or 0 |
| E4 | Full dance (only if a start opens 0): 8x empty `0x0e` ~1-2 s pacing with lift/place finger dance, post-`4`, cancel, post-`0x42`==3 expected, journaled outcome + post-reboot proof | same + operator finger ~2 min + explicit new-identity ack | new identity or structured refusal |

## Stopping rules (bind any E probe)

- Any start status other than 0/22/-3 → halt, analyze, no further
  shots. -3/22 are the known refusal vocabulary.
- Post-`0x42` anything other than exactly 2 after a start-only
  probe → halt all live work, reconcile (a start-only shot must
  never change identity state).
- One candidate per verified-stable baseline; fresh ACM context +
  mandatory cleanup per shot; never combine with module/keybag/
  SKS changes.
- No `0x40`/reset/`no_catacomb`/delete traffic anywhere near an
  enroll window (state-killers documented on warm SEP).

## Recommendation

Stage E1 alone (start-only, no dance, ~1 min operator time for the
password bind). It is the cheapest falsifiable difference in the
entire enroll matrix. Graduate E2/E3 only on 22; design E4's
journaling only on a 0.
