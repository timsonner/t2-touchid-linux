# Export return findings — MBA91 (2026-10-03)

Branch: `research/mba91-aks-ep7`. Phase: the return half of
`MACOS_EXPORT_HANDOFF_2026-10-01.md`. No second bag was created.
`native-501.kb` was not copied onto `user.kb`.
`bridge-xpc-enroll-native-501.py` was not run.

Shapes, statuses, counts, and file sizes only. No keybag handles, no
identity UUIDs, no biometric payloads.

## What the export contained

The stick directory `t2-touchid-export-20261001` held both archives:

| Archive | Size | SHA-256 |
| --- | ---: | --- |
| `t2-keybags.tar.gz` | 12561 | `2219c8087c84cada1759ef9092094f914ae9ef3873d6755c2ff8123b75eb18f4` |
| `t2-touchid-catacomb.tar.gz` | 23665 | `3a9c6dce463e20cb4c2bc4c685cc7a24b5ea19d2f808b6443f7f4e98c31705db` |

The keybag archive had 29 candidates. Two were named `user.kb`, one via
the Data volume and one via the `/Users` firmlink. They were the same
1560-byte file. Nothing else in the archive had that basename. The
Catacomb archive had an enrolled-user store: `user_000001f5.cat` (uid
501), `biolockout.cat`, `master.cat`, and `source-stat.txt`. There was
no `TemplateList.cat`.

The stick filesystem is vfat, so both archives were mode 644. The
provisioner rejects that. The installed copy was a private mode-0600
file owned by the configured user.

## What was installed

| Step | Result |
| --- | --- |
| `user.kb` | 1560 bytes, root:root, mode 0600. Bytes match both archive members. `native-501.kb` stayed 1540 bytes, mode 0600, different contents, timestamp unchanged |
| `t2-touchid-provision-catacomb` | `identity_count` 1, `local_store_provisioned` true, schema 1. Store mode 0700. Components mode 0600: `master.cat` 695, `biolockout.cat` 423, `user_000001f5.cat` 22963 |
| `t2-keybag-load.service` | Load status 0. `set-system-keybag` onto `-501` status 0, `response_length` 4. Session 1. Module was already loaded and was not reloaded |
| `t2-keybag-unlock` | Both calls status 0, `response_length` 16. Ready file mode 0600 |
| `fprintd-verify -f any tim` | `verify-match`. Daemon: `mba91-fprintd: verify verify-match` |
| `tools/install-pam.sh` | Templates installed. Originals in `/var/lib/t2-touchid/pam-backups`. `pam_fprintd` on `sudo` is `sufficient`, then `system-auth`. Lock screen gained `omarchy-lock-fingerprint`. Password lock stack unchanged |

The operator then opened a terminal and fingerprint `sudo` succeeded.
A typed Linux password at that prompt was not the shot recorded here.

This boot's read-only inventory (`INVENTORY_RO_501_20261003-194352`,
not committed; the log contains DMA addresses) still shows one
identity, free 2 / capacity 5, Catacomb present, and state words
`[0xFFFFFFFF, 3, 501, 3]`. Two figures differ from the 2026-10-01 cold
boot: `applesmc` boot-policy response **3** (that boot was response 1),
and `sks_lock_state` **520** (that boot was 16). BridgeXPC port
**49197**.

## What this says about enrollment

The status-1 halt is unchanged and still binds
`bridge-xpc-enroll-native-501.py`. That script's creation-reference
`0x21` option `0x100` is not the password-bound policy-1007 ceremony
that opened enrollment on this Air (`STATUS1_DIAG_2026-09-30.md`).

This boot is a different baseline. The real macOS bag is loaded, both
handles unlocked with status 0, one finger is already enrolled, and the
local Catacomb matches that export. The Linux enroll command for that
baseline is `t2-touchid-enroll`. This Air's `fprintd` is verify-only
and has no enroll method.

`t2-touchid-enroll` refuses to run until
`/var/lib/t2-touchid/backups/` contains exactly one private archive
whose filename is its SHA-256. That directory is absent. The stick was
plugged back in on 2026-10-03 and the Catacomb archive hash above still
matches. The backup file has not been installed.

## Next

1. Install the Catacomb archive as
   `/var/lib/t2-touchid/backups/3a9c6dce463e20cb4c2bc4c685cc7a24b5ea19d2f808b6443f7f4e98c31705db.tar.gz`,
   root:root, mode 0600. Do not commit it.
2. Confirm a typed password `sudo` in a terminal that stays open.
3. `t2-touchid-enroll preflight --acknowledge-password-fallback-tested`.
   Read-only.
4. `t2-touchid-enroll start` only after that preflight passes.

## Do-nots

- No `bridge-xpc-enroll-native-501.py`, and no creation-reference
  `0x21` option `0x100` or `0x200`.
- No second bag, and no copy of `native-501.kb` onto `user.kb`.
- No `warm-bringup-mba91.sh` while `user.kb` is the loaded bag. That
  script loads `native-501.kb`.
- No `0x40`, sensor reset, `no_catacomb`, or `0x48`.
- No commit of the export archives, the inventory logs, or the private
  inventory JSON.
