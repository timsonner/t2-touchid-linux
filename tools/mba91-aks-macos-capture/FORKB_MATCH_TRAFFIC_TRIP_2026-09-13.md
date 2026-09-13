# Fork B match-traffic mine — macOS trip checklist (working-verdict prelude)

Purpose: mine a **successful** Touch ID unlock session to learn what arms
`74` on the working path — the one datum that decides between
session-binding and credential-in-payload
(`MATCH74_CREDENTIAL_IN_PAYLOAD_DESIGN.md`). Linux 74 refuses 258 on
every axis (shape, ambient password-context, wire version); captures so
far show the *framing* (`48 → 84 → 39 → 84 → 12 → 74`, 74 always empty)
but never the full session that makes 74 accept. This trip mines that
session. Everything below assumes the capture stack was torn down (last
reboot) and must be reinstalled.

This is **not** the Mesa-64 B mine — that stays closed (three
independent confirmations, Path B dead). Do not re-task this trip to 64.

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

- **No new enroll.** Keep the existing uid-501 enrollment(s); this trip
  mints no state. Confirm free slots only to prove nothing changed.
- No sensor reset, no keybag/password changes, no FileVault changes,
  no Touch ID settings edits (settings UI brings its own device-list
  traffic — keep the session clean unless asked).
- Plan **two lock-screen unlocks ~2 min apart** so each unlock minute
  mines cleanly. Note wall-clock time + success of each.

## Capture run

1. Checkpoint the growing triple (`*.boot.txt`, `*.logstream.log`,
   `*.snapshot.log`) — note boot UUID + line count.
2. Lock (Ctrl+Cmd+Q) → Touch ID unlock #1, confirm desktop returns.
   Note time + success.
3. Wait ~2 min (idle desktop; do not open Touch ID settings).
4. Lock → Touch ID unlock #2, confirm desktop returns. Note time +
   success.
5. Checkpoint again: `mkdir -p ~/Private/t2-aks-capture && rsync -a
   /var/log/t2-aks-capture/ ~/Private/t2-aks-capture/` (re-chmod a+r
   first on Permission denied). Copy the catacomb tree + keybag export
   per `BACKUP_AND_TEARDOWN.md` only if either changed (expected:
   unchanged — match does not mint state).

## Teardown + warm handoff (do not skip)

```bash
sudo ./uninstall.sh
# remove the Device Management profile via GUI
```

Warm reboot to Omarchy (Apple menu → Restart, NOT Shut Down) with no
sensor reset, then report: boot UUID, pre/post line counts, unlock
#1/#2 times + success, slots unchanged.

## What the Linux side needs from the log (mine, don't publish raw)

Shapes and ordering only — opcodes + `(version, inValue, inSize)`,
counts, status codes, event kinds. Never payload bytes, UUIDs, or
keybag/catacomb contents. Sanitize before anything touches git
(`sanitize-bridgexpc-log.py`, `tools/privacy-check.sh`). Raw logs stay
in `~/Private` + USB only.

Per unlock minute, in order:

- Full ordered framing — confirm or deny `48 → 84 → 39 → 84 → 12 → 74`
  (both unlocks; flag any deviation between #1 and #2).
- **Opcode 8 (`GetIdentityRecords`)**: present anywhere in the unlock
  minute? Within how many lines before the first 74? (Decides the
  opcode-8-first session hypothesis — Linux match sessions never send
  8.)
- **82/84 pairing**: does an 82 precede the 84s (device-list arm), or
  are the 84s bare? (Linux prelude has no 82.)
- **Decimal 65 (`0x41`)**: present in/near the unlock minute? Args?
  (Enroll minute had one 4-B call; unlock minutes so far had none.)
- **Any 74 with inSize != 0**: decisive for credential-in-payload —
  a single non-empty 74 keeps C4/C1/C2 alive; all-empty 74 kills them
  and the answer is session-binding.
- `MATCH` + `getEnabledForUnlock → 1` confirmation per unlock (proves
  both windows are working verdicts, not silent opens).
- Catacomb save cluster after (60/80 empty? 61/62/63 v2/24 B?) — known
  shape, just confirm unchanged.
- `enrollContinue` / `3` / `4` absence check in the unlock minutes
  (expected absent; flag if present).
