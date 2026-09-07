# MBA91 supervised reset-then-`0x40` (2026-09-07)

Public-safe. Destructive run. No LTFC bytes / UUIDs in git.

## Procedure

1. Snapshot canaries (`0x42`/`0x54`/`0x38`/`0x3c`/`0x3a`/`0x53`/`0x10`)
2. bent-style preflight: readiness → provisioning → **reset `0x02`** → cancel →
   sensor info → biometrickitd info (require `calibration_present`) → `0x52`
3. Snapshot again
4. `no_catacomb` for uid `0xffffffff` (bent `initialize_general`)
5. `0x40` master LTFC then user LTFC (Private extracts)
6. Snapshot again

No enroll / ConfirmSave / EP7. Script local:
`~/Projects/t2sep-probe/mba91-reset-then-load40.py`

## Results

| Phase | `0x42` | `0x54` first | `0x40` | notes |
| --- | --- | --- | --- | --- |
| before_reset | **1** | 0 | — | cold-preserved state |
| reset | status 0 | — | — | calibration_present=True; 1 builtin device |
| after_reset_before_load | **1** | 0 | — | **reset alone did not clear `0x42`** |
| no_catacomb(0xffffffff) | — | — | — | status **0** |
| `0x40` master / user | — | — | **257** / **257** | same reject as no-reset |
| after_load | **0** | 0 | — | identities gone; store APIs still fail |

Also: `0x2e` protected_config after failed loads → status 0, len 32.

## Interpretation

1. **`0x40` status 257 survives bent’s reset preflight** on this Air with USB LTFC.
2. bent `docs/touch-id.md` links 257 to **missing accessory / device-group
   context** (not a bad LTFC length/uid). Matches our persistent **`0x54`
   first_byte=0** (accessory-present false).
3. Sensor **reset did not** empty `0x42` here; **`no_catacomb(0xffffffff)`**
   (and/or the failed load sequence) left count **0**.
4. Next research target is **accessory / `0x54` / cacheAccessories-class
   context**, not another blind `0x40` retry. Optionally re-warm from macOS to
   restore `0x42` for match experiments.

## Follow-ups

1. Offline / read-only: deepen `0x54` accessoryInfo decode; compare bent’s
   successful-load host traces for accessory prep before general `0x40`
2. Do **not** spray enroll until accessory-present path is understood
3. To restore identity visibility: macOS Touch ID warm handoff again (proven)
