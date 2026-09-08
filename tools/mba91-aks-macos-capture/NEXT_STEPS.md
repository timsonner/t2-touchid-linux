# MBA91 Touch ID / BridgeXPC — next steps

Branch: `research/mba91-aks-ep7`. Host: MacBookAir9,1 · Omarchy `MBA19-OMARCHY` ·
bridgeOS **23P6068** · BridgeXPC **39**.  
**EP7 AKS stays parked.** Fingerprint path = **BridgeXPC** (`BRIDGEXPC_PATH.md`).

**PARKED (2026-09-08):** live Mesa match / `0x40` / ACM / enroll probes stopped. See `PARKED_2026-09-08.md`. Prior notes are historical only.

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

**Done (Linux):** `0x54` all-zero (`ACCESSORY_0x54_NOTES.md`).

**Done (Sequoia):** `cacheAccessories` before `loadCatacomb`
(`ACCESSORY_MACOS_CONTRAST_2026-09-07.md`).

**Done (private opcodes):** unlock-path **82→84**; **84** all-zero on macOS
too; cache still succeeds from **82**
(`ACCESSORY_PRIVATE_OPCODES_2026-09-07.md`). Nonzero `0x54` is **not** an
MBA91 hard gate.

**Done (Omarchy host-parity):** ready=1, prov=5, cal_present=True, xART,
`0x52` builtin, warm `0x42`=1 (`HOST_PARITY_CANARIES_2026-09-07.md`).

**Done:** no-reset `0x40` after host-parity preflight → still **257** both
blobs; warm `0x42` preserved (`LOAD40_HOST_PARITY_2026-09-07.md`).

**Done (offline + read-only):** FDR Bridge method **11** returns **61407 B**
on Omarchy (matches macOS cal length); load path is Mesa **`0x20` value=3**
(`MSR_CAL_LOAD_MAP_2026-09-07.md`). MSRk still unknown.

**Done (Sequoia):** this boot **calBLOBSource 0** (no `setCalibration` /
no Mesa 32). Source-3 boots log 61407@3 but Db `0x20` lines were dropped —
inference only (`MSR_CAL_SEQUOIA_CONFIRM_2026-09-07.md`).

**Done:** Mesa **`0x20` value=3** status **0**; follow-up `0x40` still **257**
(`LOAD_CAL_0x20_2026-09-07.md`). Cal loops parked.

**Done (map):** `LOAD40_ENVELOPE_MAP_2026-09-07.md` — macOS boot load is
mostly Common/unarchive (**A**); our Mesa LTFC `0x40` is path **B**. 257 may
mean wrong tool for warm SEP, wrong blob class, or empty-gate bent also lacks.

**Fork parked (2026-09-08):** neither Sequoia Mesa-64 mine nor warm
match/`0x04` ACM canary will be run from this agent. See
`PARKED_2026-09-08.md`.

### 2. Re-warm identity (ops)

macOS Touch ID → Omarchy warm handoff to restore `0x42` when you need a
non-empty list again (match UX, etc.). Proven; independent of (1).

### 3. Retry `0x40` / match — **parked**

No further live `0x40` or match/`0x04` / ACM work from this agent.

### 4. Linux-native enroll / ACM — **parked**

### 5. Last resort (EP7) — stays parked

## Parked

- Mute AKS EP7  
- Live Mesa match / `0x40` / ACM canaries (2026-09-08)
- Sequoia Mesa decimal-64 boot mine (parked with fork)
- Blind `0x40` / reset-load loops  
- Host-parity-only `0x40` (still 257)  
- `0x20` then `0x40` (cal OK, load still 257)  
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
| `ACCESSORY_PRIVATE_OPCODES_2026-09-07.md` | private 82→84; 84 all-zero on macOS |
| `HOST_PARITY_CANARIES_2026-09-07.md` | Omarchy ready/prov5/cal-present |
| `LOAD40_HOST_PARITY_2026-09-07.md` | preflight OK, 0x40 still 257 |
| `MSR_CAL_LOAD_MAP_2026-09-07.md` | FDR method 11 + Mesa 0x20 map |
| `MSR_CAL_SEQUOIA_CONFIRM_2026-09-07.md` | calBLOBSource 0 vs 3; no captured 32 |
| `LOAD_CAL_0x20_2026-09-07.md` | 0x20 OK; 0x40 still 257 |
| `LOAD40_ENVELOPE_MAP_2026-09-07.md` | Common load A vs Mesa 0x40 B |
| `PARKED_2026-09-08.md` | live probe trail stopped |
