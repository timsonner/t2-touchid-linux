# Verified MBA91 session — 2026-09-06 (MT) / 2026-09-07 UTC

Status: **capture path verified** through cold boot → Touch ID enroll → lock-screen unlock.
Raw logs stay private (`~/Private/t2-aks-capture/`); nothing sensitive in git.

| Item | Value |
| --- | --- |
| Machine | MacBookAir9,1 |
| macOS | 15.7.9 (24G830) |
| Cold boot session | `2489129E-9BD5-4664-BB45-17368482CDA9` |
| Capture files | `20260907T030054Z-2489129E-*.{boot.txt,snapshot.log,logstream.log}` |
| Daemon | `com.timsonner.t2-aks-boot-capture` — running from boot (`runs=1`) |
| Private data | Device Management profile → `PRIVATE_DATA` in `log config --status` |

## Sequence verified

1. Install kit + LaunchDaemon
2. `chmod 755` / `chmod a+r` on `/var/log/t2-aks-capture` (agent/local tools cannot sudo)
3. Enable private logging via `EnablePrivateLogging.mobileconfig`
4. Cold reboot
5. Confirm **new** boot UUID + growing `*.logstream.log`
6. Enroll right index finger (~21:10 MT)
7. Lock-screen Touch ID unlock (~21:14 MT)
8. Copy logs to `~/Private/t2-aks-capture/` **before** EFI/FDR work

## Observed signals (sanitized)

### Cold boot
- AppleKeyStore kernel traffic present (ops / notifications; various `e00002f0` / related returns)
- BiometricKit + LocalAuthentication active before enroll

### Enroll (~21:09–21:11 MT)
- Large BiometricKit / Mesa volume; enroll UI (`FingerprintEnrollViewController`)
- Path: Touch ID Settings → `biometrickitd` → **Mesa** / **BridgeTransport** / **BridgeXPC**
- Mesa `performCommand` examples seen: `82`, `84`, `12` (host↔bridge envelopes with replies)

### Unlock (~21:14 MT)
- `loginwindow` + LocalAuthentication; AppleKeyStore lock-state notifications (`handle -501`, state changes)
- `getEnabledForUnlock -> 1`
- Catacomb persistence over Mesa/BridgeXPC: `master.cat`, `performConfirmSaveCatacombCommand`, `saveCatacombForComponents`, `saveTemplateListAfterTemplateUpdate`

### Stream size
- After unlock: on the order of **~5 MB+** for the cold-boot `logstream` (still growing while daemon up)

## Research implication (high level)

Host biometric bring-up on this Air is **BridgeXPC + Mesa via `biometrickitd`**, with AppleKeyStore participating in lock/keybag notifications. This does **not** by itself un-mute Linux mailbox EP7, but it is the macOS-side sequence to mine for opcodes / ordering vs `research/mba91-aks-ep7` falsifications.

## Still TODO (after this checkpoint)

1. ~~ESP FDR backup~~ — **N/A on this Mac** (path absent; not required — see below)
2. Optional: keybag / catacomb export for Linux restore path
3. `sudo ./uninstall.sh` + remove Device Management private-data profile
4. Offline filter of Private logs for a public-safe opcode timeline (no templates / UUIDs that look like secrets)


## EFI / FDRData finding (same session)

Mounted ESP `disk0s1` → `/Volumes/EFI`.

| Check | Result |
| --- | --- |
| `EFI/APPLE/EMBEDDEDOS/FDRData` | **Absent** |
| ESP contents | Essentially empty (~844 KiB; Spotlight/Trash metadata only) |
| Preboot `EMBEDDEDOS` / `FDRData` | **Not found** (targeted search) |
| Touch ID without ESP FDR | **Works** — enroll + lock-screen unlock already captured |

**Conclusion for MBA91 / T2 Sequoia:** do **not** treat T1Bridge-style ESP `FDRData` as required. Full-disk Omarchy wiped any prior Apple EFI tree; this macOS install did not recreate it, yet Mesa/BiometricKit/catacomb still functioned. Factory/sensor state for this path appears to live in SEP / xART / catacomb (see unlock: `master.cat`, `performConfirmSaveCatacombCommand`), not on the ESP.

**Do not** install Omarchy (or anything else) hoping it will regenerate Apple `FDRData` — Linux cannot create that machine-specific Apple tree. Dual-boot Omarchy is fine for lab space; it is unrelated to FDR recovery.

Optional later: keybag/catacomb export for Linux; uninstall capture daemon + remove private-data profile.

## Do not commit

- Raw `*.logstream.log` / snapshots
- `FDRData`, keybags, catacomb blobs
