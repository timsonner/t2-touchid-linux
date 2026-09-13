# MBA91 enroll-phase capture trip — lab setup + gathering (§2c)

Purpose: recover the v2 enroll flow's arg shapes (`0x03` bare start,
`0x0e` continue ×N, adjacent `0x65`), which exist nowhere on disk. The
2026-09-06 raw enroll log is gone (only its histogram survives); the
2026-09-13 trip was unlock-only. Everything below assumes the capture
stack was torn down (last reboot) and must be reinstalled.

## Lab setup (macOS, as admin)

```bash
cd tools/mba91-aks-macos-capture
chmod +x install.sh uninstall.sh t2-aks-boot-capture.sh
sudo ./install.sh
sudo chmod 755 /var/log/t2-aks-capture
sudo chmod a+r /var/log/t2-aks-capture/*
ls -lt /var/log/t2-aks-capture/    # need a growing *.logstream.log
open EnablePrivateLogging.mobileconfig
# System Settings → General → Device Management → Install
sudo log config --status                # expect PRIVATE_DATA
```

Reboot, log in, re-chmod if needed, confirm NEW boot-UUID files are
growing before proceeding.

## Preconditions (operator decisions — do not improvise)

- Identity capacity: SEP holds uid-501 macOS enrollment + any Linux
  identities. Enrolling captures mint state — confirm free slots first
  (max 5). Operator decides: enroll a NEW finger (preferred: discrete,
  slow touches give discrete `0x0e` samples) or re-capture with an
  existing finger (Settings → Touch ID → add).
- No sensor reset, no keybag/password changes, no FileVault changes.
- If full: delete a Linux test identity first (operator call) — never
  the macOS enrollment.

## Capture run

1. Checkpoint the growing triple (`*.boot.txt`, `*.logstream.log`,
   `*.snapshot.log`) — note boot UUID + line count.
2. Open Touch ID settings; add fingerprint. Touch **slowly and discretely**
   (lift fully between touches, ~2 s apart) so `0x0e` continues separate.
3. Finish enroll, then one lock-screen (Ctrl+Cmd+Q) Touch ID unlock.
4. Checkpoint again: `mkdir -p ~/Private/t2-aks-capture && rsync -a
   /var/log/t2-aks-capture/ ~/Private/t2-aks-capture/` (re-chmod a+r
   first on Permission denied). Copy the catacomb tree + keybag export
   per `BACKUP_AND_TEARDOWN.md` if either changed.

## Teardown + warm handoff (do not skip)

```bash
sudo ./uninstall.sh
# remove the Device Management private-logging profile via GUI
```

Warm reboot to Omarchy (Apple menu → Restart, NOT Shut Down) with no
sensor reset, then report: boot UUID, pre/post line counts, finger
added (or not), slots free.

## What the Linux side needs from the log (mine, don't publish raw)

- `performCommand …` first-arg sweep (expect `3` ×1, `65` ×1, `14` ×N,
  `4` ×1 in the enroll minute) with `(version, inValue, inSize)` per
  call — opcodes + sizes only, never payload bytes or UUIDs.
- `0x0e` input-size sequence across the N continues (the missing datum).
- Confirm `0x03` input size (bare vs token) and `0x65` args.
- Sanitize before anything touches git (`sanitize-bridgexpc-log.py`,
  `tools/privacy-check.sh`). Raw logs stay in `~/Private` + USB only.
