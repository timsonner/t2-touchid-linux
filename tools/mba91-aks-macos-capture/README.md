# MBA91 macOS AKS/SEP boot capture

Early LaunchDaemon that records unified logs for AppleKeyStore / SEP /
BiometricKit / LocalAuthentication from boot through Touch ID enroll.

**Scope:** sequence and os_log evidence for Linux T2 AKS research.  
**Not in scope:** raw SEP mailbox / OOL wire bytes (later lever if logs are thin).

Hardware context: MacBookAir9,1 — dual-boot / macOS side of `research/mba91-aks-ep7`.

## Verified on MBA91 (2026-09-06)

Cold boot → enroll → lock-screen unlock **confirmed** with growing
`*.logstream.log` and Mesa/BridgeXPC biometric traffic. See
[VERIFIED_SESSION_2026-09-06.md](VERIFIED_SESSION_2026-09-06.md) and
[CHECKLIST.md](CHECKLIST.md).

**Checkpoint rule:** copy `/var/log/t2-aks-capture/` to `~/Private/` (and USB)
**before** mounting EFI / copying `FDRData`, in case ESP work goes wrong.


---

## Prerequisites

- macOS on the Air (this machine), admin account
- This folder (`mba91-aks-macos-capture/`) on disk
- USB or other off-machine store for log + FDR copies (keep off git/iCloud)

---

## One-shot procedure (verified path)

### 1. Install the capture daemon

```bash
cd /path/to/mba91-aks-macos-capture
chmod +x install.sh uninstall.sh t2-aks-boot-capture.sh enable-private-data-system.sh
sudo ./install.sh
```

Confirm it is live:

```bash
sudo launchctl print system/com.timsonner.t2-aks-boot-capture | head -40
sudo ls -lt /var/log/t2-aks-capture/
```

You want `state = running` and a growing `*.logstream.log` (not only `*.boot.txt` / `*.snapshot.log`).

If `logstream` is missing:

```bash
sudo launchctl kickstart -k system/com.timsonner.t2-aks-boot-capture
sleep 3
sudo ls -lt /var/log/t2-aks-capture/
sudo ps aux | grep -E '[l]og stream|[t]2-aks-boot'
```


### 1b. Allow non-root read of capture logs (for agent / local verify)

The log dir is created mode `700` (root-only). Grok Bot / Cursor local tools
on the Mac run as your user and **cannot** `sudo` interactively, so they get
`Permission denied` until you open the dir:

```bash
sudo chmod 755 /var/log/t2-aks-capture
sudo chmod a+r /var/log/t2-aks-capture/*
```

Re-apply `chmod a+r` after each reboot if new files are still root-only
(or copy out):

```bash
sudo mkdir -p ~/Private/t2-aks-capture
sudo cp -a /var/log/t2-aks-capture/. ~/Private/t2-aks-capture/
sudo chown -R "$(whoami)" ~/Private/t2-aks-capture
```

Then verify (you or the agent on `tims-MacBook-Air.local`):

```bash
ls -lt /var/log/t2-aks-capture/
# expect growing *.logstream.log; AppleKeyStore lines may already appear
```

On MBA91 (2026-09-06) after chmod: daemon running, ~360KB stream, real
`AppleKeyStore` kernel lines (`sel: 7` / `sel: 35`, ret `e00002f0`), plus
BiometricKit / LocalAuthentication. Predicate is noisy (`sep` over-matches);
live stream may drop messages — use `log show` later if needed.

### 2. Enable private log strings (do this BEFORE reboot)

`sudo log config --mode 'private_data:on'` is **dead** on modern macOS
(Catalina+). It returns `Invalid Modes`.

**Working method (preferred):** install the configuration profile.

```bash
open EnablePrivateLogging.mobileconfig
```

Then:

1. **System Settings → General → Device Management**
2. Select **Enable Unified Log Private Data (T2 research)** → **Install…**
3. Authenticate

Verify:

```bash
sudo log config --status
```

Expect a line containing **`PRIVATE_DATA`**, e.g.:

```text
System mode = INFO STREAM_LIVE PRIVATE_DATA
```

**Fallback only** (may not set `PRIVATE_DATA` until reboot / profile path):

```bash
sudo ./enable-private-data-system.sh
sudo log config --status
```

If status still lacks `PRIVATE_DATA`, use the `.mobileconfig` path above.

### 3. Cold reboot (armed capture)

Reboot once so the LaunchDaemon starts before login and records boot-time
AppleKeyStore / SEP chatter.

### 4. Enroll Touch ID while capture is running

1. Log in
2. System Settings → Touch ID → enroll at least one finger
3. Lock the screen and unlock with Touch ID (match path)
4. Leave the daemon running through both

Optional sanity check after login:

```bash
sudo ls -lt /var/log/t2-aks-capture/
# newest *.logstream.log should still be growing
```

### 5. Collect artifacts off-machine

**Checkpoint:** copy capture logs to `~/Private/t2-aks-capture/` (and USB) **before** mounting EFI / copying FDR.


```bash
sudo ls -lt /var/log/t2-aks-capture/
```

Copy (USB recommended) the **newest** set for this boot:

- `*.boot.txt` — marker, hardware/ifaces snapshot
- `*.logstream.log` — live stream (main signal)
- `*.snapshot.log` — short `log show` window

Also back up machine EFI data before any later wipe/Linux reinstall:

- `EFI/APPLE/EMBEDDEDOS/FDRData` (this Mac only; other Macs’ copies are useless)

Then (when ready for Linux research): export keybags / catacomb per
`t2-touchid-linux` docs — separate from this logger.

### 6. Tear down (after copies are safe)

```bash
# stop daemon; keep logs on disk
sudo ./uninstall.sh

# or stop daemon and delete local logs
sudo ./uninstall.sh --wipe-logs
```

Remove private logging:

- **System Settings → General → Device Management** → remove the
  **Enable Unified Log Private Data (T2 research)** profile

Optional cleanup if the System plist fallback was used:

```bash
sudo rm -f /Library/Preferences/Logging/com.apple.system.logging.plist
sudo log config --status   # PRIVATE_DATA should be gone
```

---

## Quick command card

```bash
# install + confirm stream
cd ~/Downloads/mba91-aks-macos-capture
chmod +x install.sh uninstall.sh t2-aks-boot-capture.sh
sudo ./install.sh

# let user/agent read logs without sudo
sudo chmod 755 /var/log/t2-aks-capture
sudo chmod a+r /var/log/t2-aks-capture/*
ls -lt /var/log/t2-aks-capture/    # need growing *.logstream.log

# private data (BEFORE reboot)
open EnablePrivateLogging.mobileconfig
# → System Settings → General → Device Management → Install
sudo log config --status   # must show PRIVATE_DATA

# reboot → login → chmod a+r again if needed → enroll Touch ID

# collect
ls -lt /var/log/t2-aks-capture/
# copy newest *.boot.txt *.logstream.log *.snapshot.log to USB
# copy EFI/APPLE/EMBEDDEDOS/FDRData off-machine

# teardown
sudo ./uninstall.sh
# remove the Device Management profile
```

---


---

## As-run session (MBA91, 2026-09-06)

Tim’s Terminal history for the working kit, plus the GUI profile step
(`history` does not record Device Management clicks).

```bash
# from ~/Downloads
tar -xvf mba91-aks-macos-capture.tar.gz
cd mba91-aks-macos-capture
chmod +x install.sh uninstall.sh t2-aks-boot-capture.sh
chmod +x enable-private-data-system.sh
sudo ./install.sh

# fallback System plist (alone → status was INFO STREAM_LIVE, no PRIVATE_DATA)
sudo ./enable-private-data-system.sh
sudo log config --status

# confirm / heal live stream
sudo ls -lt /var/log/t2-aks-capture/
sudo ps aux | grep -E '[l]og stream|[t]2-aks-boot'
sudo launchctl kickstart -k system/com.timsonner.t2-aks-boot-capture
sleep 3
sudo ls -lt /var/log/t2-aks-capture/

# preferred private-data path (GUI — required for PRIVATE_DATA on this Mac)
open EnablePrivateLogging.mobileconfig
# System Settings → General → Device Management → Install
#   "Enable Unified Log Private Data (T2 research)"

sudo log config --status
# → System mode = INFO STREAM_LIVE PRIVATE_DATA
```

Then: **reboot → login → enroll Touch ID → copy logs + FDR → uninstall + remove profile.**

Canonical shortened path for docs/next machine (skip the failed CLI mode and
optional kickstart if `logstream` already grows after install):

```bash
tar -xvf mba91-aks-macos-capture.tar.gz
cd mba91-aks-macos-capture
chmod +x install.sh uninstall.sh t2-aks-boot-capture.sh
sudo ./install.sh
sudo ls -lt /var/log/t2-aks-capture/    # need growing *.logstream.log
open EnablePrivateLogging.mobileconfig  # Device Management → Install
sudo log config --status                # expect PRIVATE_DATA
# reboot → enroll → collect → sudo ./uninstall.sh + remove profile
```

## Files in this kit

| File | Role |
| --- | --- |
| `install.sh` | Install LaunchDaemon + start capture |
| `uninstall.sh` | Remove daemon (`--wipe-logs` optional) |
| `t2-aks-boot-capture.sh` | Marker + light snapshot + `log stream` |
| `com.timsonner.t2-aks-boot-capture.plist` | LaunchDaemon definition |
| `EnablePrivateLogging.mobileconfig` | **Preferred** private-data enable |
| `enable-private-data-system.sh` | Fallback System plist writer |

---

## Notes / pitfalls (learned on MBA91)

- Empty log dir + `Terminated: 15` / `inefficient`: avoid a blocking full-boot
  `log show`; stream first, capped snapshot only; use `ProcessType=Interactive`.
- `boot.txt` alone is not enough — confirm **`*.logstream.log` is growing**.
- System plist alone may show `INFO STREAM_LIVE` without `PRIVATE_DATA`; the
  Device Management profile is the reliable path.
- Logs can contain auth/device metadata — treat as sensitive; do not commit.
- This does **not** replace macOS first-txn / bent-style wire capture if we
  later need raw EP7 framing.

---

## After you have logs

Hand the USB tree to Rook / the `research/mba91-aks-ep7` notes with:

1. macOS version (`sw_vers`)
2. Whether Touch ID enroll completed
3. Whether `PRIVATE_DATA` was on for that boot
4. FDR backup confirmation (yes/no + where stored)
