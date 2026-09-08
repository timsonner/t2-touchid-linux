# MBA91 MSR / calibration load map (offline + read-only Omarchy)

Public-safe. No FDR blob bytes / full hashes in git. Private meta:
`$HOME/Private/t2-aks-research/FDR_CAL_BLOB_META.txt` on the Air.

## What macOS does (already mined)

Boot bring-up (Common + Mesa):

1. `checkSensorReadiness` → `initSensor`
2. `loadMSRkData` (provisioningState **5**)
3. `loadCalibrationData` → `setCalibrationData:source:` with length **61407**,
   source / calBLOBSource **3**
4. then `cacheAccessories` → `loadCatacomb`

MSRk **write** opcodes are still unpublished (bent README: absent). Calibration
load path **is** documented in-tree via `bridge-xpc-probe.py`.

## Fork / bent inventory

| Piece | Where | Status on MBA91 |
| --- | --- | --- |
| Bridge method **5** `CALIBRATION_DATA_FROM_EEPROM` | `bridge-protocol.py` | Omarchy reply is a **UUID string**, not a cal blob |
| Bridge method **11** `CALIBRATION_DATA_FROM_FDR` | same | Omarchy returns **nonempty bytes, len=61407** |
| Mesa **`0x20`** load cal (`value=3` = remote/bridgeOS FDR; `5` = macOS file) | `src/bridge-xpc-probe.py --load-calibration` | **not** in bent `biometric-command.py` helpers |
| MSRk load | — | **missing** everywhere we looked |
| ESP `FDRData` path | prior MBA91 note | **N/A** on wiped Air — **orthogonal**: Bridge method 11 still works |

`bridge-xpc-probe` load sequence (do **not** run yet without intent):

```text
Bridge [11] → FDR bytes
Mesa performCommand 0x20 version=1 value=3 data=FDR_bytes
```

## Omarchy read-only result (2026-09-07)

After normal Bridge open (method 0 → client-ver 2 → method 1):

| Call | Result |
| --- | --- |
| method 5 (EEPROM) | `[ "<uuid-string>" ]` — not usable as cal payload |
| method 11 (FDR) | **bytes len=61407** (matches macOS `setCalibrationData` length) |

So Linux can **fetch** the same-sized FDR calibration macOS loads with source **3**.
We have never issued Mesa **`0x20`** on this Air.

## Gap vs `0x40` status 257

Host-parity (ready/prov5/cal_present/`0x52`) did **not** clear 257. Leading
hypothesis for next live work:

1. Supervised Mesa **`0x20` value=3** with method-11 blob (cal load), then
   re-check host canaries / optional `0x40`
2. Still need Sequoia private Db confirmation that boot actually uses **`0x20`**
   (and whatever MSRk uses) before treating this as complete parity
3. MSRk remains a separate unknown if (1) alone is insufficient

## Sequoia checklist (when you reboot)

Capture kit + `PRIVATE_DATA` still installed. Soft reboot → login → ping Rook:

1. Mine boot Db for `loadMSRkData` / `loadCalibrationData` / `setCalibrationData`
   and Mesa `performCommand:version:…` numbers in that window  
2. Confirm whether **`0x20`** appears with inSize≈61407 / value 3  
3. Note any MSRk-related opcodes (unknown)  
4. Return to Omarchy for supervised `0x20` (not blind `0x40` first)

## Parked

- Blind / host-parity-only `0x40`
- `0x54` type A/B
- Assuming ESP FDRData is required (Bridge FDR is enough to *read*)
