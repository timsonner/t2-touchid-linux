# Linux confirm after macOS deleted identity 2 — MBA91 (2026-10-04)

Branch: `research/mba91-aks-ep7`. Omarchy return after
`MACOS_IDENTITY2_UNLOCK_2026-10-04.md`. The prior handoff was
`MACOS_IDENTITY2_LINUX_HANDOFF_2026-10-04.md`.

No identity UUIDs, keybag handles, hardware UUIDs, or biometric
payloads.

## What was tried

`t2-keybag-load.service` had already loaded `user.kb`. Both handles
were unlocked (`/run/t2-touchid/keybags-unlocked` present). The
operator verified Finger 1 still matches on Linux. Identity 2 failed
to unlock.

## What this boot showed

Read-only. No enroll, no delete, no Catacomb copy, no
`reconcile-external-deletion`.

| Check | Result |
| --- | --- |
| `t2-touchid-enroll status` | `live_enrollment_blocked` false, unfinished 0, post-reboot pending 0 |
| `t2-touchid-enroll list` | exit 2: `local and live identity inventories disagree` |
| `t2-touchid-manage status` | no pending external-reconciliation journal |
| Linux `user_000001f5.cat` | 39314 bytes (two-identity store from `recover-observed`) |
| `user.kb` / `native-501.kb` | 1560 / 1540, unchanged |
| `fprintd-list tim` | compatibility name `right-index-finger` |
| Finger 1 on Linux | operator `verify-match` |
| Identity 2 on Linux | operator no-match / unlock failed |

Linux did not write identity 2 back onto SEP. The host archive still
lists two identities. SEP follows the macOS one-finger Catacomb.

## Meaning

macOS `syncTemplateListForUser:` removed the Linux-enrolled SEP
identity. That identity cannot match on Linux until SEP holds it
again. This tree has no proven restore. The local two-identity
Catacomb is a stale extra record, the same dual-boot split already
recorded on MacBookPro16,2.

Copying `user.kb` onto macOS does not restore it. Linux already uses
that macOS bag. The object macOS consults is `/Library/Catacomb`.
Copying the Linux Catacomb there is still behind the decoder gate.

## Do-nots

- No `t2-touchid-enroll start`.
- No copy of the Linux Catacomb onto `/Library/Catacomb`.
- No copy of `native-501.kb` onto `user.kb` or onto macOS.
- No System Settings enroll of the Linux finger as a debug step.
- No `0x40`, sensor reset, `no_catacomb`, or `0x48`.
- No `bridge-xpc-enroll-native-501.py`.
- No `reconcile-external-deletion` unless the operator asks. That
  command drops the stale local record. It does not put identity 2
  back on SEP.

Next: `IDENTITY2_NEXT_HANDOFF_2026-10-04.md`.
