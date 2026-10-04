# Next after identity 2 left SEP — MBA91 (2026-10-04)

Read `MACOS_IDENTITY2_LINUX_CONFIRM_2026-10-04.md` first. Finger 1
is the specimen. Identity 2 is gone from SEP. Linux Catacomb still
has two identities. `t2-touchid-enroll list` fails: local and live
inventories disagree.

This is not an enroll shot and not a `/Library/Catacomb` replace.
Pick **one** path. Stop when that path's stop line is reached.

## Path L — Linux, this Omarchy boot (default everyday)

Everyday unlock is Finger 1 (`fprintd-verify -f any tim` or
fingerprint sudo). Leave the disagreement, or, **only if the
operator asks**, run the proven one-record repair:

```sh
sudo t2-touchid-manage reconcile-external-deletion \
  --acknowledge-external-fingerprint-removal \
  --acknowledge-local-catacomb-reconciliation
sudo systemctl restart fprintd.service
```

That drops the stale local identity 2, keeps Finger 1, and sends no
SEP mutation. Stop after list agrees and Finger 1 still matches.

Do not enroll. Do not `recover-observed`. Do not load
`native-501.kb`.

## Path M — macOS, decoder fixture only (cross-OS unlock)

Cross-OS unlock needs macOS to accept a Linux-emitted Catacomb so
`syncTemplateListForUser:` keeps identity 2. The gate is still
closed (`enrollment_research/FINDINGS.md`).

macOS agent task, then stop:

1. Normal macOS 15.7.9 build 24G830. Finger 1 still unlocks.
2. Decode a **copy** of the Linux-emitted archive with the matching
   macOS secure decoder in a disposable directory.
3. Record pass or fail. Do not call `loadCatacomb`, save, delete, or
   any biometric command. Do not replace `/Library/Catacomb`.
4. Stop.

A later replace, if ever authorized, needs that decoder note first.
Offline APFS writes from Linux are the same closed gate.

## Do-nots (both paths)

- No `t2-touchid-enroll start`.
- No System Settings enroll of the Linux finger as a debug step.
- No copy of Linux Catacomb onto `/Library/Catacomb`.
- No copy of `native-501.kb` onto `user.kb` or onto macOS.
- No `bridge-xpc-enroll-native-501.py`.
- No `0x40`, sensor reset, `no_catacomb`, or `0x48`.
- No naming of the post-355 freeze from the 2026-10-03 live log.
- No commit of journals, inventory logs, keybags, or Catacomb
  archives.

Optional later, after Path L or an explicit operator ask: one
generic-state enroll to journal the event after 355. That is a new
identity. The next macOS boot will delete it the same way unless
Path M has already passed and a separate replace is authorized.
