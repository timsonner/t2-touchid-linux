# MBA91 Sequoia accessory contrast (2026-09-07 cold boot)

Public-safe. Raw logs stay under `~/Private/t2-aks-capture/`. No UUIDs / hashes / LTFC.

## Setup

| Item | Value |
| --- | --- |
| Host | MacBookAir9,1 · Sequoia **15.7.9** (24G830) |
| Boot | Cold boot into macOS after Omarchy (empty Linux `0x42`) |
| Capture | `/usr/bin/log show --last 90m` (biometrickitd / coreauth / catacomb keywords) |
| Private-data profile | **not** installed this session |
| Boot-capture LaunchAgent | **not** installed this session |

Tim locked/unlocked twice after login; mine covers boot + those unlocks.

## Verified order (biometrickitd Mesa init)

Timestamps relative; all in one ~600 ms burst after Bridge HELO (`bkremoted` / **39** / **23P6068**):

1. Bridge transport up → `Bridge will init` / interface v3  
2. `checkSensorReadiness` → sensorReady **1**  
3. `initSensor` → `loadMSRkData` (provisioningState **5**) → success  
4. `loadCalibrationData` → success (calBLOBSource **3**) → `initSensor` → 0  
5. **`cacheAccessories accessories 1:`**  
   - `BiometricKitAccessory (type:1, uuid:0, flags:0x6, group type:1 uuid:0)`  
6. **`loadCatacomb`** → Master → User **501** → both status **0**  
7. `restoreAndSyncTemplates identities 1` (identity bound to that same accessory)  
8. Later lock-screen: `MechanismTouchId will start matching user 501` (match path works)

`cacheAccessories` also reappears around unlock/match (still count **1**, same type/flags).

## What did *not* appear

- No literal `accessoryInfo` string in this (non-private) log mine  
- No Mesa `performCommand` opcode hex (needs private-data profile / live stream kit)  
- So we still lack a direct macOS proof that Mesa `0x54` first_byte ≠ 0 — only the **host-visible** accessory cache

## Contrast vs Omarchy Linux

| Signal | Sequoia (this boot) | Omarchy (post reset-load) |
| --- | --- | --- |
| Builtin device list | accessory type **1** / uuid **0** / flags **0x6** via `cacheAccessories` | `0x52` still **1** builtin |
| Host accessory cache before load | **yes** (`cacheAccessories` then `loadCatacomb`) | no host cache step |
| Mesa `0x54` accessoryInfo reply | unknown (not logged) | **all-zero 83 B** (types 0–3) |
| `0x40` loadCatacomb | succeeds (status 0) after accessories cached | **257** |

## Implication

macOS does **not** wait on a mysterious accessory UUID. It:

1. Brings Bridge + sensor + MSR/cal online  
2. Caches the **builtin** accessory (type **1**, zero UUID, flags **0x6** — same shape as `0x52` records)  
3. Then loads catacomb

Linux already sees the builtin on `0x52` but never runs an equivalent of steps 2–3’s *host* cache, and bent’s `0x54` presence gate stays empty. Next Linux work should chase **sensor-init / MSR-cal / cacheAccessories-equivalent** before another `0x40`, not more `0x54` type enums.

Optional follow-up on Sequoia: reinstall capture kit + private-data profile for one unlock if we need Mesa opcode hex around `cacheAccessories`→`loadCatacomb`. Not required to keep moving on the host-side gap.
