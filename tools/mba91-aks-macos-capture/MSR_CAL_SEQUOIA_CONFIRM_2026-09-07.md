# Sequoia MSR/cal opcode confirm (2026-09-07 late)

Public-safe. Boot UUID `6B52DA57-…` stream `20260908T053855Z-6B52DA57-…`
(+ prior PRIVATE_DATA boots). No finger scans this boot.

## This boot (no Touch ID)

| Step | Result |
| --- | --- |
| `checkSensorReadiness` | sensorReady **1** |
| `loadMSRkData` | success, provisioningState **5** |
| `loadCalibrationData` | success, **calBLOBSource: 0** |
| `setCalibrationData` | **not called** |
| Mesa `0x20` (decimal 32) in Db stream | **absent** |
| Then | `cacheAccessories` → `0x52`/`0x54` as before; `loadCatacomb` Common path |

Visible Mesa ops in the early window: **53** (`0x35` sensor info), then
**40** (decimal; here tied to `getNodeTopologyForIdentity`, 3060 B reply),
**46**, **48**, later **82**/**84**. Bridge also returned the same EEPROM-style
UUID string we see from Omarchy Bridge method **5**.

## Contrast: earlier PRIVATE_DATA boots (calBLOBSource **3**)

`log show` Df lines (23:03 and 23:17 boots):

- `setCalibrationData:source: …[61407] 3` → success  
- `loadCalibrationData → 0 (calBLOBSource: 3)`  

Live stream **dropped** the Db `performCommand` lines in that ~200 ms window
(`Messages dropped during live streaming`). Persisted `log show` for the same
timestamps also lacks Db opcode rows. So we still **cannot** dump a captured
`performCommand … 32 …` line from this Air, even though source **3** + length
**61407** match the fork FDR→`0x20` recipe.

**No stream file on disk contains** `performCommand:… 32 ` (decimal).

## Interpretation

1. **calBLOBSource 0** = macOS skips FDR/`setCalibrationData` when cal is
   already resident. Matches Omarchy `calibration_present=True` without us
   ever issuing `0x20`.
2. **calBLOBSource 3** = push 61407-byte FDR blob (Bridge method 11 size).
   Opcode **inferred** as Mesa `0x20` value=3 from `bridge-xpc-probe.py`;
   **not** wire-proven on MBA91 logs.
3. **MSRk**: success logged at Df only; no Mesa write opcode recovered. May be
   a no-op when provisioningState is already 5, or non-Mesa.
4. Therefore a supervised Omarchy **`0x20`** is still the right *cal-push*
   experiment (especially after sensor reset clears cal), but it may **not**
   explain current `0x40`→257 while `cal_present` is already true.

## Next

| Priority | Action |
| --- | --- |
| A | Omarchy: supervised **`0x20` value=3** with method-11 blob (status only); re-check canaries; optional `0x40` only if something moves |
| B | If still 257 with cal unchanged: dig **load envelope / component** (not more cal) |
| C | Optional Sequoia: sensor-reset boot to force calBLOBSource 3 + catch Db before drop (harder) |

## Parked

- Claiming MBA91 log-proved `0x20` (inference only)  
- Expecting `0x20` to be required every boot (source 0 disproves)  
- Blind `0x40` loops  
