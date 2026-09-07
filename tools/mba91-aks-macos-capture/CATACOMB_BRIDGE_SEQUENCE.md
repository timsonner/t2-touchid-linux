# MBA91 catacomb + Bridge/Mesa sequence (mined 2026-09-06 capture)

Public-safe notes from cold-boot session `2489129E-9BD5-4664-BB45-17368482CDA9`
(macOS 15.7.9 on MacBookAir9,1). Raw logs stay under `$HOME/Private` / USB only.

## On-disk layout (example UUID is machine-specific)

```text
/Library/Catacomb/<CATACOMB_DIR_UUID>/
  master.cat
  user_<uid_hex>.cat          # uid 501 → user_000001f5.cat
  biolockout.cat
  prepare/user_<uid_hex>.cat  # staging during save (seen in enroll)
```

This Air: dir UUID `64FFD0F9-9014-5F6F-BC5B-265A589D0570`.
Logged *content* UUID for user 501 is a **different** value (os_log redacts to
`18BE***` after enroll; cold boot showed `0000***` / hash len=0). Treat directory
UUID and catacomb-content UUID as separate namespaces.

## Phase A — cold boot load (~21:00:58 MT)

`biometrickitd` bring-up order (logshow):

1. Bridge interface **v3**
2. `checkSensorReadiness` → `initSensor`
3. `loadMSRkData` (provisioningState 5) → success
4. `loadCalibrationData` → success
5. **`loadCatacomb`**
   - `loadCatacombForComponent:(Master)` → 0
   - `loadCatacombForUser:501` / User component → 0
   - `logCatacombUUIDForUser:501 → 0000***`, hash len=0 (empty store)
   - `loadCatacomb loaded user: 501` → `loadCatacomb → 0`
6. `restoreAndSyncTemplates identities 0: ()` (nothing to sync yet)
7. `bridgeBootUUID` → success; `serviceMatch initialized`
8. Clients attach (`coreauthd`, etc.); `GET_BIO_DEVICE_LIST` via Mesa **82/84**

Mesa timeline near load: early **opcode 26**, then **39**, **44**, device-list
**82/84**. Catacomb *file* load here looks **filesystem-side** in Common logs;
the heavy Mesa catacomb opcode cluster appears later on **save**, not on this
empty load.

## Phase B — first enroll persist (~21:10:25 MT)

After enroll UI / finger samples:

1. `getEnabledForUnlock` → **1** (Mesa **opcode 48**, high confidence)
2. SKS / BioLockout chatter
3. **Save pipeline** (repeats for User then Master):

```text
saveCatacomb → saveCatacombForComponents
  performGetCatacombStateCommand
  performGetCatacombGroupStateCommand
  performPrepareSaveCatacombCommand   # Mesa ~60 family
  performCompleteSaveCatacombCommand  # Mesa ~61/62 (v2) + large XPC RX
  catacombFileNameForComponent → user_000001f5.cat | master.cat
  # enroll wrote staging URL:
  #   file:///Library/Catacomb/<DIR_UUID>/prepare/user_000001f5.cat
  performConfirmSaveCatacombCommand   # Mesa opcode 63 (8/8 near ConfirmSave)
  performGetCatacombUUIDCommand / HashCommand
performSaveBioLockoutRecordCommand    # → biolockout.cat
```

Canonical Mesa order observed on first User save:

`48` (unlock enabled) → `8` → `17` (topology) → `84`/`14` (enroll path) →
`60` → `80` → `61` → `62` → **`63` ConfirmSave** → `56` → `58` → (Master
repeat of prepare/complete/confirm).

Also: `saveCatacombForIdentity` with a new identity UUID after first template.

## Phase C — lock-screen unlock (~21:14 MT)

1. `ENABLED_FOR_UNLOCK 1` again
2. Match path (heavy **84**, **74**, cancel **12**, etc.)
3. Post-unlock **same save cluster** (User then Master + ConfirmSave **63**)
4. On-disk mtimes for `master.cat` / `user_*.cat` / `biolockout.cat` align ~21:14

## Mysteries this clarifies

| Question | Finding |
| --- | --- |
| Where are the files? | `/Library/Catacomb/<dir-uuid>/` + `prepare/` staging |
| Load vs save? | Empty load at boot is Common/`loadCatacomb*`; durable write is Mesa prepare→complete→**confirm(63)** |
| Same as Linux EP7 AKS? | **No.** Path is BridgeXPC↔Mesa inside `biometrickitd`. Mute EP7 is a different transport mystery. |
| Bags alone enough? | Necessary for bent-style Linux restore attempts; **not** sufficient while EP7 stays mute. |

## Mysteries still open

1. **Load-with-templates cold boot** — re-capture after enroll survives reboot: does Mesa get a catacomb *push* cluster, or still mostly filesystem load + `restoreAndSyncTemplates`?
2. **Directory UUID vs content UUID** — who mints `64FFD0F9-…` vs the redacted `18BE…` user catacomb UUID?
3. **MSRk / calibration blobs** — `loadMSRkData` / `loadCalibrationData` before catacomb; needed for sensor bring-up independently of templates.
4. **Bridge ↔ SEP mailbox** — still no raw EP7 bytes in os_log; first-txn hunt (lane D) if we need wire proof.

## Next instrument (recommended)

Cold reboot **with** enrolled finger still present → new logshow window on
`loadCatacomb` + `restoreAndSyncTemplates` (expect non-empty identities). Compare
opcode timeline to Phase A. No Omarchy reinstall required for that A/B.
