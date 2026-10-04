# Linux handoff — identity 2 after the macOS boot delete (2026-10-04)

**Confirm completed.** Result:
[`MACOS_IDENTITY2_LINUX_CONFIRM_2026-10-04.md`](MACOS_IDENTITY2_LINUX_CONFIRM_2026-10-04.md).
List failed (`local and live identity inventories disagree`). Finger 1
matches. Identity 2 did not. Next:
[`IDENTITY2_NEXT_HANDOFF_2026-10-04.md`](IDENTITY2_NEXT_HANDOFF_2026-10-04.md).
The original confirm steps remain below as the shot that was run.

Branch: `research/mba91-aks-ep7`. You are on Omarchy. The write-up is
`MACOS_IDENTITY2_UNLOCK_2026-10-04.md`.

macOS 15.7.9 loaded the one-finger `/Library/Catacomb`, then
`syncTemplateListForUser:` removed the Linux-enrolled SEP identity
because it was not in biometrickitd. `bioutil` showed one template
for uid 501. Unlock with that finger cannot work on macOS until the
macOS Catacomb also holds it.

The Linux two-identity Catacomb was not overwritten by that boot.
This shot was meant to confirm a restore onto SEP. The confirm found
disagreement instead. It does not teach a protocol ordinal and it
does not enroll.

## Do this

1. Let `t2-keybag-load.service` load `user.kb`. Do not run
   `warm-bringup-mba91.sh`.
2. Unlock both handles as on the 2026-10-04 verify boot.
3. `t2-touchid-enroll list` should show count **2**, both live.
4. `fprintd-verify -f any tim` of the Linux-enrolled finger should
   return `verify-match`.

If the list is count 1, stop. Do not enroll. Do not copy Catacomb
files. Record that the Linux store did not restore, and leave the
macOS finger as the specimen.

If count 2 and verify-match succeed, the macOS delete is session-
local on the SEP. Everyday Linux match still uses either finger.
macOS unlock still uses Finger 1 only.

## Do-nots

- No copy of the Linux Catacomb onto `/Library/Catacomb`.
- No System Settings enroll of the Linux finger as a debug step.
- No `t2-touchid-enroll start` as part of this confirm.
- No naming of the post-355 freeze from the 2026-10-03 log.
- No `bridge-xpc-enroll-native-501.py`.
- No second bag, and no copy of `native-501.kb` onto `user.kb`.
- No `0x40`, sensor reset, `no_catacomb`, or `0x48`.
- No commit of journals, inventory logs, or the Catacomb archive.

Cross-OS unlock is a later Catacomb-sync problem. The decoder gate
for replacing the macOS archive is still closed.
