# MBA91 bounded `0x40` loadCatacomb canary (2026-09-07)

Public-safe. No LTFC/CFTL bytes, no identity UUIDs.

## Inputs

USB: `mba91-backup-20260906/catacomb/64FFD0F9-…/`

| Source | Extract | Notes |
| --- | --- | --- |
| `user_000001f5.cat` | `user_501.ltfc` len **24542**, LTFC v10, uid 501, 1 identity | Private extract only |
| `master.cat` | `master.ltfc` len **244**, uid field `0xffffffff` | Private extract only |

Extract via `t2_catacomb_codec` (`decode_user_catacomb` / `MasterCatacomb`).  
Stored under `$HOME/Private/t2-aks-research/cftl-extract/` mode 0600 — **not** in git.

## Procedure (deliberately non-destructive)

1. True-cold state already had `0x42` count=1.
2. Multiverse → method 0 → client-version 2 → method 1.
3. Snapshot: `0x42` / `0x54` / `0x38` / `0x3c` / `0x3a`.
4. `0x40` load **master** LTFC then **user** LTFC via
   `current_catacomb_secure_data_fields` (bent’s LoadCatacomb wrapper).
5. **No** sensor reset, **no** `no_catacomb`, **no** enroll / ConfirmSave.
6. Snapshot again.

Bent’s stock `external-catacomb-load-probe` **resets the sensor** before load;
that path was **not** used (would destroy the cold-preserve A/B evidence).

## Results

| Step | Result |
| --- | --- |
| before `0x42` | count=1 |
| before `0x54` first_byte | 0 |
| before `0x38` / `0x3c` | fail `0xe00002c2` |
| before `0x3a` v1 | ok, 33 B |
| **`0x40` master** | **status=257**, no output |
| **`0x40` user** | **status=257**, no output |
| after snapshots | **unchanged** vs before |

## Interpretation

- Raw LTFC from macOS `.cat` is the right **on-disk** family (uid/version match
  `CATACOMB_ONDISK.md`), but a no-reset `0x40` on this warm/cold-preserved
  session returns **257** and does not flip store APIs or `0x54` first_byte.
- Likely need bent’s pre-load context (sensor reset + readiness/calibration
  gate, and/or master `no_catacomb` init) — **destructive** to in-SEP identity
  visibility we just proved survives power-off.
- Next supervised choice: reset-then-load A/B (expect `0x42` empty after reset,
  then reload from LTFC) **or** chase status-257 meaning offline vs bent logs.

## Script

Local only: `~/Projects/t2sep-probe/mba91-load-catacomb-noreset.py`
