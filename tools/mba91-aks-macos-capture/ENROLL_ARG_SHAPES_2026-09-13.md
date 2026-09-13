# Enroll v2 arg shapes (2026-09-13 capture trip)

Source: private enroll-phase capture, boot `62D1A28F-…`
(`20260913T092455Z`), macOS 15.7.9. Pre-enroll 8564 lines →
post-enroll 28002 → final 30983. New finger enrolled (finger 2),
then one lock-screen Touch ID unlock with the new finger (verified
`MATCH` uid 501, `getEnabledForUnlock → 1`). Raw logs, catacomb, and
keybags stay in `~/Private` + USB only — shapes below, no payloads.

Trip note: [ENROLL_CAPTURE_TRIP_2026-09-13.md](ENROLL_CAPTURE_TRIP_2026-09-13.md).
Opcode annotations: [MESA_OPCODE_ANNOTATIONS.md](MESA_OPCODE_ANNOTATIONS.md).

## Sweep (enroll minute 03:44:14–03:44:31 UTC)

Predicted `3` ×1, `65` ×1, `14` ×N, `4` ×1 — all present:

| Opcode | n | version | inValue | inSize |
| --- | ---: | ---: | ---: | ---: |
| `3` (`0x03`, enroll start) | 1 | 2 | 0 | **68** |
| `14` (`0x0e`, enroll continue) | **8** | 1 | 0 | **0 every time** |
| `65` (decimal, adjacent pre-enroll) | 1 | 1 | 0 | **4** |
| `4` (post-enroll) | 1 | 1 | 0 | **68** |

Timeline: `65` ~10 s before enroll start → `3` at enroll open →
eight `14`, each glued to an `enrollContinue → Success`
(03:44:17→03:44:24) → catacomb save cluster
(Prepare/CompleteSave → 0; opcodes 61/62/63 ver=2 inSize=24) →
`4` → in-enroll match → UI teardown (`12` cancel); lock-screen
unlock `MATCH` several minutes later.

## Answers to the three open items

- **`0x03` bare vs token: token.** Single call, ver=2, 68 B input.
- **`0x0e` input-size sequence (the missing datum): N=8, all
  inSize 0.** Continues carry no input; finger-progress state must
  live server-side (or in an unwatched channel), not in these args.
- **`65` args: ver=1, inValue=0, inSize=4**, single call just before
  enroll open.

## Notation flag

The trip note's "`0x65`" reads as decimal-65 shorthand (i.e. `0x41`):
decimal `65` appears exactly once (above); decimal `101` (`0x65`
proper) appears **zero** times in the whole 30 k-line boot log.
`0x03`/`0x0e` are unaffected (same value in hex and decimal digits).

## Linux-side impact

- v2 enroll start can be replayed shape-faithfully as ver=2 + 68 B
  token; the token's *contents* remain unrecovered (never logged).
- `0x0e` continues are trivially shaped (empty) — N=8 for a full
  discrete-touch enroll; pacing ~1–2 s apart separated them cleanly.
- No new preflight beyond the existing parked-EP7 analysis; this
  closes the arg-shape gap only.
