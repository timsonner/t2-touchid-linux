# Fork B match-74 verdict: session-binding (2026-09-13 capture)

Source: private match-traffic capture, boot `82F1CBFC-…`, macOS 15.7.9.
785 lines pre → 8964 post. Two lock-screen Touch ID unlocks (~2 min
apart, 05:16 + 05:18 local, both ok), no enroll, no settings edits.
Raw logs + catacomb stay in `~/Private` (+USB for the enroll trip) —
shapes below, no payloads.

Trip note: [FORKB_MATCH_TRAFFIC_TRIP_2026-09-13.md](FORKB_MATCH_TRAFFIC_TRIP_2026-09-13.md).
Decides: `MATCH74_CREDENTIAL_IN_PAYLOAD_DESIGN.md` (session-binding
vs credential-in-payload). Enroll shapes:
[ENROLL_ARG_SHAPES_2026-09-13.md](ENROLL_ARG_SHAPES_2026-09-13.md).

## Verdict framing (both unlocks)

`48 → 84 → 39 → 84 → 12 → 74`, all ver=1, inValue=0:

| Opcode | inSize |
| --- | ---: |
| `48` | 0 |
| `84` | 20 |
| `39` | 4 |
| `84` | 20 |
| `12` | 0 |
| `74` | **0** |

Pre-verdict prelude (~3 s earlier, both unlocks): `48`(0), `39`(4),
`46`(4), `4`(**68**), `46`(4), `46`(4). Deviations: unlock #1 doubles
the verdict-48 and carries an extra prelude `58`(4 B); #2 has neither.

Post-verdict catacomb cluster (both): `60`/`80` empty, `61`/`62`/`63`
ver=2 24 B, `56`/`58` 4 B — known shape, unchanged (#2 trails one
extra `63`).

## Checklist answers

- **Opcode 8 (`GetIdentityRecords`): absent** — nowhere in either
  unlock minute or near them. The opcode-8-first session hypothesis
  gets no support from match minutes.
- **82/84 pairing: 84s bare**, no 82 in either minute. Consistent
  with the Linux prelude (also no 82).
- **Decimal 65 (`0x41`): absent** in/near unlock minutes.
  Enroll-only so far.
- **Any 74 with inSize != 0: no.** Zero non-empty 74 in all 8964
  lines. **Decisive: credential-in-payload (C4/C1/C2) is dead —
  the answer is session-binding.** Whatever arms 74 is not carried
  in its args.
- **Working verdicts proven:** `MATCH` uid 501 plus
  `getEnabledForUnlock → 1` inside both minutes.
- **Absence check: `3` / `14` / `enrollContinue` absent ✓ — but `4`
  (ver=1, 68 B) is present in both unlock preludes**, same shape as
  the enroll post-`4`. Flagged, unexplained: a 68 B token flows on
  the match path too, just earlier than the verdict.

## Side observation

Match mints catacomb state (user cat grew, mtimes at unlock #2) —
refreshed Private copy under `catacomb-20260913-match/`. Keybags
left alone (no identity change); no USB copy this trip (volume
already ejected).

## Linux-side impact

- Do not chase credential bytes into 74: replicate the *session*
  (prelude ordering + the unknown arming signal), not a payload.
- Open leads, in order: (1) what the prelude `4`/68 B token is on a
  match path and whether 74 needs it; (2) the doubled-48 / extra-58
  in unlock #1 as candidate arming-signal noise; (3) whether the
  prelude `48 → 39 → 46…` cluster (vs bare verdict framing) is the
  actual session-establishment the Linux prelude is missing.
