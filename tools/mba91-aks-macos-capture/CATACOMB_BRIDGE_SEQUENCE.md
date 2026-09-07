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

## Next instrument

Phase A′ enrolled reboot A/B **done** (see above). Optional next: deeper BridgeXPC
payload decode around `performGetIdentityRecordsCommand`, or lane D raw first-txn.

## Phase A′ — enrolled cold reboot (2026-09-06 ~22:14 MT)

Boot session: `28BE7F9F-FE93-4874-9349-C5714D382E2F`  
Files: `20260907T041436Z-28BE7F9F-*.{boot,snapshot,logstream}` + Private
`logshow-enrolled-boot-28BE7F9F-*.log` (live stream dropped early lines; logshow
recovered them).

Same bring-up order as empty Phase A, but **non-empty** store:

1. Bridge v3 → `initSensor` → `loadMSRkData` (prov 5) → `loadCalibrationData`
2. `loadCatacomb`
   - Master component → 0
   - User 501 → `user_000001f5.cat` → `unarchiveCatacombData…` → 0
   - `addIdentityObjects:` identity UUID `7C66170E-39D3-44EB-8DEF-9173BF839790`
     (same UUID minted at first enroll)
   - `logCatacombUUIDForUser:501 → 18BE***` (redacted; **not** `0000***`)
   - `logCatacombHashForUser:501 → b9e3*** (len=32)` (**not** len=0)
3. **`restoreAndSyncTemplates identities 1:`** (was `identities 0: ()` when empty)
4. Mesa `performGetIdentityRecordsCommand`; Bridge reply payload includes the
   identity UUID bytes (`7c66170e…`)
5. `bridgeBootUUID` → `9E70089C-5D62-4BEA-B791-B43C2561970C` (unchanged vs empty boot)
6. `serviceMatch initialized`

Later: password unlock at login, then lock-screen **fingerprint** unlock succeeded
(`mesa.matchAttempt` / `BKMatchTouchIDOperation`); catacomb files remtimes ~22:16;
post-unlock Master save again.

### A/B table

| Signal | Empty enroll boot (Phase A) | Enrolled reboot (Phase A′) |
| --- | --- | --- |
| Catacomb UUID log | `0000***` | `18BE***` |
| Catacomb hash | len=0 | len=32 |
| `restoreAndSyncTemplates` | identities **0** | identities **1** |
| `addIdentityObjects` | none | `7C66170E-…` |
| `user_*.cat` unarchive | n/a / empty | success |
| `bridgeBootUUID` | `9E70089C-…` | same |

### Solved: directory UUID

`/Library/Catacomb/<DIR_UUID>/` **DIR_UUID equals Hardware UUID / Provisioning
UDID** on this Air (`64FFD0F9-9014-5F6F-BC5B-265A589D0570`). Content/user catacomb
UUID (`18BE…`) remains a separate namespace.

### Still open

- Early live `log stream` drops — always pair with `log show` for boot window.
- AKS `getUserKeybagUUIDForUID` failed during early unarchive (sel 23/35) before
  password unlock — catacomb still unarchived; keybag timing vs template sync.
- Linux EP7 mute unchanged; this A/B is Bridge/Mesa + filesystem catacomb only.

## Bridge payload decode

GetIdentityRecords (Mesa opcode **8**) 40-byte uid+UUID layout, topology (17),
and CFTL complete-save blobs:
[BRIDGE_GETIDENTITY_DECODE.md](BRIDGE_GETIDENTITY_DECODE.md).
