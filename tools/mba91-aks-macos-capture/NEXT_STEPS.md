# MBA91 Touch ID / BridgeXPC — next steps

Branch: `research/mba91-aks-ep7`. Host: MacBookAir9,1 · Omarchy `MBA19-OMARCHY` ·
bridgeOS **23P6068** · BridgeXPC **39**.  
**EP7 AKS stays parked.** Fingerprint path = **BridgeXPC** (`BRIDGEXPC_PATH.md`).

## What we know (2026-09-07)

| Fact | Evidence |
| --- | --- |
| Multiverse → method 0 `(0,3)` → method 1 opened | `WARM_IDENTITY_AB_2026-09-07.md` |
| After macOS enroll, `0x42` survives soft reboot **and** true power-off without Linux `loadCatacomb` | cold A/B notes |
| `0x38`/`0x3c` fail while `0x42` can be non-empty; `0x54` first_byte stays **0** | warm catacomb probes |
| No-reset `0x40` → **257** | `LOAD_CATACOMB_0x40_2026-09-07.md` |
| Reset preflight OK (`calibration_present`) but `0x40` still **257**; `no_catacomb` cleared `0x42` to 0 | `RESET_THEN_LOAD40_2026-09-07.md` |
| bent: 257 ↔ missing accessory/device-group context | bent `docs/touch-id.md` |

**Current SEP/Mesa list state on Air:** `0x42` count **0** after this run.

## Next (in order)

### 1. Accessory / `0x54` context  ← **do this next**

Why `0x54` first_byte stays 0, and what bent’s successful macOS boot does for
accessory caching before general `0x40`. Read-only probes preferred. Goal: flip
accessory-present (or document why Linux cannot) **before** another `0x40`.

### 2. Re-warm identity (when needed)

macOS Touch ID → Omarchy warm handoff again to restore `0x42` for match / UX
experiments. Proven path; no guesswork.

### 3. Only after accessory-present looks right

Retry bounded `0x40` (consider **skipping** `no_catacomb(0xffffffff)` unless
required — it cleared identities here). Then optional warm match canary.

### 4. Linux-native enroll / ACM

Only after load/match story is coherent. No ConfirmSave spray.

### 5. If Bridge stalls

SIP-off EP7 — explicit Tim OK.

## Parked

- Mute AKS EP7  
- Blind `0x40` retries without accessory progress  
- Assuming power-off clears `0x42` once enrolled (disproven)  
- Treating `0x08` as `0x42`  

## Doc index

| Note | Topic |
| --- | --- |
| `WARM_IDENTITY_AB_2026-09-07.md` | smoke + warm A/B |
| `WARM_CATACOMB_PROBES_2026-09-07.md` | store API split |
| `COLD_SOFT_REBOOT_AB_2026-09-07.md` / `COLD_POWEROFF_AB_2026-09-07.md` | preserve ladder |
| `LOAD_CATACOMB_0x40_2026-09-07.md` | no-reset 257 |
| `RESET_THEN_LOAD40_2026-09-07.md` | reset + still 257 |
| `MESA_BENT_OPCODE_CROSSWALK.md` | opcodes |
