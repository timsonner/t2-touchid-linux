# Linux enroll identity — MBA91 (2026-10-03)

Branch: `research/mba91-aks-ep7`. Protocol patch `ddfcdf6` was installed
into `/opt/t2-touchid/src` before this start. One macOS finger already
verified. This start added a second identity for uid 501.

No identity UUIDs, keybag handles, addresses, or biometric payloads.

## What ran

One `t2-touchid-enroll start` from a floating terminal, with the three
live acknowledgements. `user.kb` was already loaded and unlocked.
`warm-bringup-mba91.sh` was not run.

The operator typed the macOS keybag password. The sensor was used.
Start returned status 0, protocol version 2, 68-byte request.

## Journal, this start

| Milestone | Result |
| --- | --- |
| `ENROLL_START_OBSERVED` | status 0 |
| `ENROLL_CONTINUE_INTENT` / `OBSERVED` | ordinals **70**, **160**, **220**, **275**, **339**, **341**, **345**, **355**. Every continue status 0 |
| Stop | `ENROLL_OUTCOME_UNKNOWN`, reason `protocol-error`, stage terminal, `mutation_possible` true |

Ordinal 70 is the recovered `enrollContinue` path. 160 through 355 are
progress (about 23% through 100%). Status **80** did not freeze this
start.

The event after 355 was not journaled. The freeze is still one of the
eight fail-closed generic ordinals: `51`, `58`, `60`, `61`, `62`, `65`,
`99`, `502`. Do not name that ordinal from this log. Do not fold it
into the protocol from this shot.

## SEP vs host

`recover-outcome` refused: host and SEP identity inventories diverge.

| Store | uid 501 count |
| --- | --- |
| Baseline, this journal | 1 |
| Local Catacomb after the freeze | 1 (`user_000001f5.cat` still 22963 bytes) |
| Live SEP per-user and global lists | 2, repeats equal |

The new finger was on the SEP. The host store had not been rewritten.

## Persist

`t2-touchid-enroll recover-observed` with both acknowledgements
returned `observed_identity_recovered` true, `persistence_ready` true,
`reconciliation_complete` true, `fingerprint_mutation_performed` false.

| After recover-observed | Result |
| --- | --- |
| `t2-touchid-enroll list` | count 2, both `live` true, `local_live_reconciled` true. Names: Finger 1, Linux enrolled finger |
| `user_000001f5.cat` | 39314 bytes |
| `master.cat` | 736 bytes |
| `biolockout.cat` | 423 bytes |
| Gate | `unfinished_count` 0, `post_reboot_pending_count` 1, `post_reboot_verification_candidate` true, `live_enrollment_blocked` true |

`user.kb` is still 1560 bytes. `native-501.kb` is still 1540 bytes and
unloaded.

## Next

E4 requires a different Linux boot UUID than this enroll boot.

1. Reboot Omarchy.
2. Load `user.kb` with `t2-keybag-load.service`. Unlock both handles.
   Do not run `warm-bringup-mba91.sh`.
3. `sudo t2-touchid-enroll verify-post-reboot`
4. Optional match check: `fprintd-verify -f any tim` for the new finger.

Do not start another enroll until that verification returns
`post_reboot_verified` true. This Air's `fprintd` is still verify-only.

## Do-nots

- No second `t2-touchid-enroll start` while post-reboot verification is
  pending.
- No mapping of the post-355 freeze from this live log.
- No mapping of 60 or 61 onto the status-80 finish.
- No `bridge-xpc-enroll-native-501.py`.
- No second bag, and no copy of `native-501.kb` onto `user.kb`.
- No `warm-bringup-mba91.sh` while `user.kb` is the loaded bag.
- No `0x40`, sensor reset, `no_catacomb`, or `0x48`.
- No commit of journals, inventory logs, or the Catacomb archive.
