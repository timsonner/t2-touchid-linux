# MBA91 Touch ID / BridgeXPC — next steps

Branch: `research/mba91-aks-ep7`. Host: MacBookAir9,1 · Omarchy `MBA19-OMARCHY` ·
bridgeOS **23P6068** · BridgeXPC **39**.  
**EP7 AKS stays parked.** Fingerprint path = **BridgeXPC** (`BRIDGEXPC_PATH.md`).

## What we know (2026-09-07)

| Fact | Evidence |
| --- | --- |
| Bridge open works (Multiverse → 0 → client-ver 2 → 1) | warm A/B |
| Once enrolled, `0x42` survives soft reboot **and** power-off **without** Linux `0x40` | cold A/B notes |
| `0x54` accessoryInfo: **all-zero 83 B** on Linux; macOS caches builtin accessory **before** load | `ACCESSORY_*` notes |
| `0x40` → **257** with or without reset preflight; USB LTFC extract looks structurally valid | load notes |
| bent: 257 ↔ missing accessory/device-group context; same `0x54` first_byte=0 on their Linux | bent touch-id / catacomb handoff |
| `no_catacomb(0xffffffff)` cleared `0x42` here; reset alone did **not** | `RESET_THEN_LOAD40_2026-09-07.md` |

**Air right now:** `0x42` count **0** (after reset-load run).

## Next (in order)

### 1. Accessory / host cache — status

**Done (Linux):** `0x54` type A/B + order canary → all-zero 83 B (`ACCESSORY_0x54_NOTES.md`).

**Done (Sequoia cold boot):** `cacheAccessories` (type 1 / uuid 0 / flags 0x6)
runs **before** successful `loadCatacomb`. See
`ACCESSORY_MACOS_CONTRAST_2026-09-07.md`.

**Next (Linux):** host-side parity with macOS init order — sensor ready /
MSR+cal (or documented stubs) → accessory cache equivalent → then `0x40`.
Do **not** blind-retry `0x40` or more `0x54` type enums.

**Optional Sequoia:** private-data profile + capture kit for Mesa opcode hex
around that burst (nice-to-have, not blocking).

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
| `ACCESSORY_0x54_NOTES.md` | accessoryInfo / all-zero reply |
| `ACCESSORY_MACOS_CONTRAST_2026-09-07.md` | Sequoia cacheAccessories → loadCatacomb |
