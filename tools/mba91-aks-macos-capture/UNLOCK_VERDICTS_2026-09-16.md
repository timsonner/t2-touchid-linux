# macOS unlock verdicts — capture answers 2026-09-16 (Sequoia 15.7.9)

Boot `20260916T0557Z-62AAABB9-…` (post-reboot, daemon reinstalled same
night, `INFO STREAM_LIVE PRIVATE_DATA`). Shapes/ordering/statuses only —
no payload bytes, UUIDs, or keybag/catacomb contents. Raw logs in
`~/Private/t2-aks-capture/` + USB only.

Login 23:58 was password (`clearPassword` logged, `82 → 84 → 39`, no
match op). Three Touch ID ScreenLock unlocks, all successful, desktop
returned: 00:00, 00:07, 00:10. Enrollments intact throughout
(`enrolledIdentityCount 2`, `enrolledUserCount 1`).

## Canonical verdict framing (fully captured, 00:07 unlock)

Prelude: `46` (v1/0/4 B) → `48`-empty (match-start,
`getEnabledForUnlock → 1`, `unlockAttemptStarted`), gap **3.4 s**, then:

`48`-empty → `84` (v1/0/20 B) → `39` (v1/0/4 B) → `12`-empty →
`84` (v1/0/20 B) → `74`-empty (v1/0/0 B)

All status 0, then `matchAttempt postEvent`, `unlockAttemptFinished`,
save cluster `60/80/61/62/63/56/58/61/62/63` (~15–16 s post-verdict).
`74` inSize is 0 on the working path — third confirmation that 74
carries no credential payload (session-binding stands).

## Answers to the 2026-09-16 Linux asks

1. **Prelude→verdict gap:** 2–3.5 s (3.4 s @00:07, 2.2 s @00:10,
   ~3 s @00:00). Gap contains zero Mesa calls — only
   `serviceStatus`/`statusMessage(90)` finger traffic. **No `12`-cancel,
   no teardown call.** The session stays open across the gap.
   Consequence: S2b's "macOS closes the `4` session" assumption is
   **disproven**. S2 (no separation) was the faithful model; neither S2
   nor S2b is capture-exact as run (see prelude variance below).
2. **Doubled-`48` / extra prelude-`58`:** doubled `48`s appear **only at
   boot** (23:57:56, 6 ms apart). All three ScreenLock unlocks use a
   single verdict-`48`; `58` appears only inside save clusters, never in
   any prelude. Doubling is a boot/first-auth phenomenon, **not**
   every-unlock. S1b variant unneeded — S1-closed stands.
3. **Opcode 8 / 82 window:** `8` ×0 in the entire boot (8.3 k→18 k
   lines). `82` ×2, boot + password-login only — never within ±5 min of
   any Touch ID unlock (closest ~2.5 min prior). Opcode-8-first session
   hypothesis is **dead**; unlock-path `84`s are bare (no 82 arm).
4. **`4`/68 B call (00:10 unlock):** ver **1**, inValue **0**, inSize
   **68**, out 0/0, status 0. Thread neighbors: match-start context →
   `4` → `48`-empty (6 ms) → `46` (16 ms). Prelude: `4 → 48 → 46`.
5. **State kept:** both enrollments, no Touch ID settings edits, no
   sensor reset, no keybag/password/FileVault changes.

## Prelude variance (new datum)

The prelude is NOT fixed shape unlock-to-unlock:

- 00:00: `46 → 48 → 46` (no `4`, no `39`)
- 00:07: `46 → 48` (no `4`, no `39`)
- 00:10: `4 → 48 → 46` (full shape, matches 2026-09-13 mine)

The verdict framing is invariant; the prelude varies. The `4` is not
even mandatory on the working path.

## Whole-boot opcode census (Mesa performCommand, stream)

`48` ×7, `84` ×4, `39` ×5, `46` ×5, `82` ×2, `58` ×2 (save clusters),
`4` ×1, `12` ×1, `74` ×1, `8` ×0, `65` ×0. (00:00 + 00:10 verdict
bursts partially stream-dropped under touch-burst load — the 00:07
window is the complete one; success confirmed for all three via
`matchAttempt`/`unlockAttemptFinished`/save-cluster/desktop-return.)

## Misc for Linux notes

- New SKS coloring: `0x209 (DeviceLocked,UnlockTokenPresent,
  ApplePayTokenPresent)` at ScreenLock match-start. Informational only.
- Framework layer passes a 16 B `BKOptionMatchForCredentialSet` +
  `MatchForUnlock=1` at `match:withOptions` — credential binding lives
  above Mesa; Mesa-74 stays empty. Consistent with session-binding.
- `39` reply shape 4 B (`08 02 00 00` pattern family — shape only).
- 00:00 unlock's verdict burst was stream-dropped (lossy `log stream`
  under burst); `log show` cannot backfill debug-level Mesa lines, so a
  fully-captured window needs a quiet-predicate re-run if ever required.
  Current answers don't need it.

## Pending

- Capture daemon still installed + profile present (left live in case a
  re-run is wanted). Teardown per `BACKUP_AND_TEARDOWN.md` when Linux
  side calls it: `sudo ./uninstall.sh`, remove Device Management
  profile, warm reboot to Omarchy (Restart, NOT Shut Down), no sensor
  reset, then fingerless self-test + full-inventory.
