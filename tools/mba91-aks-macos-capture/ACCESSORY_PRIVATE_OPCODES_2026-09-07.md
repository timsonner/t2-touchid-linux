# MBA91 Sequoia private-data Mesa opcodes (2026-09-07 soft reboot)

Public-safe. Raw streams under `~/Private/t2-aks-capture/` and
`/var/log/t2-aks-capture/`. No full UUID dumps / catacomb hashes in git.

## Setup

| Item | Value |
| --- | --- |
| OS | Sequoia **15.7.9** (24G830) |
| Capture | LaunchDaemon `com.timsonner.t2-aks-boot-capture` + `log show --last boot` |
| Logging | `System mode = INFO STREAM_LIVE **PRIVATE_DATA**` |
| Boot UUID | `668BFA9C-…` (stream `20260908T051731Z-668BFA9C-…`) |
| Note | Accidental Omarchy boot-menu hit before Sequoia; this still looks like a clean macOS boot + two Touch ID unlocks |

Live stream dropped some boot-init lines (`Messages dropped during live
streaming`). Boot **order** comes from `log show`; unlock-path **opcode hex**
comes from the Db stream (complete for `listAccessories`).

## Boot order (`log show`, confirmed again under PRIVATE_DATA)

1. Bridge HELO (`bkremoted` / 39 / **23P6068**)
2. `checkSensorReadiness` → sensorReady **1**
3. `initSensor` → `loadMSRkData` (provisioningState **5**) → `loadCalibrationData` (calBLOBSource **3**)
4. **`cacheAccessories accessories 1`** (type **1**, uuid **0**, flags **0x6**)
5. **`loadCatacomb`** Master + User **501** → status **0**
6. `restoreAndSyncTemplates identities 1`

## Unlock-path opcode gold (`cacheAccessories` / `listAccessories`)

Exact Mesa `performCommand` lines (command, version, inValue, inSize):

| Step | Opcode | Ver | inSize | Reply (public) | Result |
| --- | --- | --- | --- | --- | --- |
| `performGetBioDeviceListCommand` | **82** (`0x52`) | 1 | 0 | **44 B**; LE count **1**; trailing flags dword **0x6** | status 0 |
| accessoryInfo query | **84** (`0x54`) | 1 | **20** | **83 B, all `0x00`** (first_byte **0**) | status 0 |
| host cache | — | — | — | still **`accessories 1`** type1/uuid0/flags6 | `cacheAccessories -> 0` |

Logged shape:

```
cacheAccessories
performGetBioDeviceListCommand
performCommand … 82 1 0 …   → BridgeConnection length=44 (count=1 … flags 0x6)
performGetBioDeviceListCommand -> 0
performCommand … 84 1 0 … inSize=20 → BridgeConnection length=83 all-zero
cacheAccessories accessories 1: (type:1, uuid:0, flags:0x6, …)
cacheAccessories -> 0
```

Other Mesa opcodes seen in this stream (counts, not a full boot table):
**44**, **39**, **48** (`getEnabledForUnlock` → 1), **63** v2, **46**, plus the
single **82**/**84** pair above.

No literal `accessoryInfo` symbol in logs — the Mesa op is just **84**.

## Contrast vs Omarchy / bent gate

| Claim | Sequoia (this capture) | Omarchy Linux |
| --- | --- | --- |
| `0x54` 83 B first_byte | **0** (all-zero blob) | **0** (all-zero blob) |
| `0x52` builtin | count 1, flags 0x6 | count 1 builtin |
| Host still caches accessory | **yes** after 82→84 | we never host-cache |
| `loadCatacomb` | succeeds after cache | `0x40` → **257** |

**Conclusion:** bent’s “`0x54` first_byte ≠ 0” presence gate is **not** what
macOS requires on this Air. macOS treats the **`0x52` device-list record** as
enough to populate `cacheAccessories`, then loads catacomb. Matching all-zero
`0x54` on Linux was never the blocker by itself.

## Plan impact

1. Stop treating nonzero `0x54` as a hard preflight for MBA91 Linux.  
2. Next Linux work: host-side **sensor/MSR/cal + cacheAccessories-equivalent
   from `0x52`**, then retry `0x40`.  
3. Status **257** may still mean “missing host/device-group context” in bent’s
   sense — but that context is the **cached builtin from 82**, not a live
   accessoryInfo blob.

## Teardown reminder

```bash
cd ~/Downloads/mba91-aks-macos-capture
sudo ./uninstall.sh
# System Settings → General → Device Management → remove private-data profile
```
