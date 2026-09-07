# MBA91 Touch ID / BridgeXPC — next steps

Branch: `research/mba91-aks-ep7`. Host: MacBookAir9,1 · Omarchy `MBA19-OMARCHY` ·
bridgeOS **23P6068** · BridgeXPC **39**.  
**EP7 AKS stays parked.** Fingerprint path = **BridgeXPC** (`BRIDGEXPC_PATH.md`).

## What we know (2026-09-07)

| Fact | Evidence |
| --- | --- |
| Bridge open works (Multiverse → 0 → client-ver 2 → 1) | warm A/B |
| Once enrolled, `0x42` survives soft reboot **and** power-off **without** Linux `0x40` | cold A/B notes |
| `0x54` accessoryInfo shape OK (83 B) but **first_byte always 0** (warm, cold, post-reset) | all canaries |
| `0x40` → **257** with or without reset preflight; USB LTFC extract looks structurally valid | load notes |
| bent: 257 ↔ missing accessory/device-group context; same `0x54` first_byte=0 on their Linux | bent touch-id / catacomb handoff |
| `no_catacomb(0xffffffff)` cleared `0x42` here; reset alone did **not** | `RESET_THEN_LOAD40_2026-09-07.md` |

**Air right now:** `0x42` count **0** (after reset-load run).

## Next (in order)

### 1. Accessory / `0x54` — concrete probes  ← **do this next**

Goal: explain or flip accessory-present **before** another `0x40`. Prefer
read-only. Public-safe logging only (status / lengths / first_byte).

1. **Offline decode** of 83-byte `0x54` reply layout from bent + any MBA91
   macOS capture notes (what bytes besides first_byte mean). Write
   `ACCESSORY_0x54_NOTES.md` (no raw dumps in git).
2. **A/B input variants** (still read-only): type/UUID in the 20-byte
   accessoryInfo request — type **2**+zero UUID is what we used; try bent’s
   documented builtin shapes only; never enroll.
3. **Order canary:** `0x52` → `0x54` → `0x0c` (bent enroll-predecessor order)
   and record first_byte only — expect still 0, but documents parity.
4. **macOS contrast (when Tim is on Sequoia):** one unlock/enroll-adjacent
   os_log window — does macOS ever log accessory-present / `accessoryInfo`
   success before `loadCatacomb`? No more blind Linux `0x40`.

Stop condition for this section: either first_byte becomes nonzero under a
documented probe, **or** we prove Linux cannot get it without a missing
host-side step bent also lacks (then escalate that gap).

### 2. Re-warm identity (ops)

macOS Touch ID → Omarchy warm handoff to restore `0x42` when you need a
non-empty list again (match UX, etc.). Proven; independent of (1).

### 3. Retry `0x40` only after (1) moves

- Skip `no_catacomb(0xffffffff)` unless a note says it’s required  
- Success = status 0 + `0x42` count≥1 + note `0x38`/`0x54`  
- Then optional warm match canary  

### 4. Linux-native enroll / ACM

Only after load/match is coherent. No ConfirmSave spray.

### 5. Last resort

SIP-off EP7 — explicit Tim OK.

## Parked

- Mute AKS EP7  
- Blind `0x40` / reset-load loops  
- Assuming power-off clears enrolled `0x42`  
- `0x08` as alias for `0x42`  

## Doc index

| Note | Topic |
| --- | --- |
| `WARM_IDENTITY_AB_2026-09-07.md` | smoke + warm |
| `WARM_CATACOMB_PROBES_2026-09-07.md` | store API split |
| `COLD_*_AB_2026-09-07.md` | preserve ladder |
| `LOAD_CATACOMB_0x40_2026-09-07.md` | no-reset 257 |
| `RESET_THEN_LOAD40_2026-09-07.md` | reset + still 257 |
| `MESA_BENT_OPCODE_CROSSWALK.md` | opcodes |
