# MBA91 no-reset `0x40` with host-parity preflight (2026-09-07)

Public-safe. Local script: `~/Projects/t2sep-probe/mba91-load40-host-parity.py`.
Private LTFC lengths only (no paths in outcome table beyond note).

## Procedure

1. Bridge open (Multiverse → 0 → client-ver 2 → 1)  
2. Preflight (must pass): `0x53` ready=1 → `0x10` prov=5 → `0x35` → `0x28` cal_present → `0x52` builtin≥1  
3. Snapshot `0x42` / `0x54` / `0x38` / `0x3c` / `0x3a`  
4. `0x40` master LTFC then user_501 LTFC (bent `current_catacomb_secure_data_fields`)  
5. Snapshot again  

**Not done:** sensor reset, `no_catacomb`, enroll, ConfirmSave.

## Results

| Step | Result |
| --- | --- |
| Preflight | **pass** (ready=1, prov=5, cal_present=True, builtin=1) |
| before `0x42` | count **1** |
| before `0x54` | 83 B, first=0, nonzero_bytes=0 |
| before `0x38`/`0x3c` | `0xe00002c2` |
| before `0x3a` v1 | status 0, len 33 |
| `0x40` master (244 B) | **257** |
| `0x40` user501 (24542 B) | **257** |
| after `0x42` | count **1** (unchanged) |
| after `0x54` | still all-zero |

## Interpretation

Host-readable parity + treating `0x52` as cache **does not** clear status **257**.
Combined with Sequoia evidence that macOS also sees all-zero `0x54` and still
loads, 257 on this Air is **not** explained by missing accessory first_byte or
missing ready/prov/cal flags.

Next research: actual **`loadMSRkData` / `loadCalibrationData` write path**
(opcodes bent never published; macOS calBLOBSource **3**), or load-envelope /
component framing differences — not more `0x54` type A/B.
