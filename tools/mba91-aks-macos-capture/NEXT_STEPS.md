# MBA91 Touch ID / BridgeXPC — next steps

Branch: `research/mba91-aks-ep7`. Host: MacBookAir9,1 · Omarchy `MBA19-OMARCHY` ·
bridgeOS **23P6068** · BridgeXPC **39**.  
Fingerprint path = **BridgeXPC** (`BRIDGEXPC_PATH.md`). This work is
conducted under **Track A** — independent ownership research
([`docs/LAB_PROTOCOL.md`](../../docs/LAB_PROTOCOL.md)); the earlier 2026-09-08
park is lifted. See `PARKED_2026-09-08.md` for the authorization record.

## What we know (2026-09-07)

| Fact | Evidence |
| --- | --- |
| Bridge open works (Multiverse → 0 → client-ver 2 → 1) | warm A/B |
| Once enrolled, `0x42` survives soft reboot **and** power-off **without** Linux `0x40` | cold A/B notes |
| `0x54` accessoryInfo: **all-zero 83 B** on Linux; macOS caches builtin accessory **before** load | `ACCESSORY_*` notes |
| `0x40` → **257** with or without reset preflight; USB LTFC extract looks structurally valid | load notes |
| bent: 257 ↔ missing accessory/device-group context; same `0x54` first_byte=0 on their Linux | bent touch-id / catacomb handoff |
| `no_catacomb(0xffffffff)` cleared `0x42` here; reset alone did **not** | `RESET_THEN_LOAD40_2026-09-07.md` |

**Air right now:** `0x42` count **1** (re-warmed 2026-09-13 via single-boot
macOS trip → warm reboot, no sensor reset; verified SKS `0x10`).

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
(`LOAD_CAL_0x20_2026-09-07.md`). Cal loops remain open.

**Done (map):** `LOAD40_ENVELOPE_MAP_2026-09-07.md` — macOS boot load is
mostly Common/unarchive (**A**); our Mesa LTFC `0x40` is path **B**. 257 may
mean wrong tool for warm SEP, wrong blob class, or empty-gate bent also lacks.

**Fork unblocked (2026-09-08):** A (warm match/`0x04`+ACM), B (Sequoia
Mesa-64 mine), and C (empty-SEP load envelope) are all back on the table.
See `PARKED_2026-09-08.md`.

### 2. Re-warm identity (ops)

macOS Touch ID → Omarchy warm handoff to restore `0x42` when you need a
non-empty list again (match UX, etc.). Proven; independent of (1).

### 2b. Next macOS trip checklist (single boot covers all) — DONE 2026-09-13

Trip completed unlock-only variant (existing uid-501 enrollment kept, no
live enroll); evidence in `MESA64_FRESHBOOT_MINE_2026-09-13.md`. SEP was
empty pre-trip; re-warm verified post-trip (`0x42`=1, SKS `0x10`).
Kit procedure: `README.md` + `CHECKLIST.md`; exports/teardown:
`BACKUP_AND_TEARDOWN.md`.

1. Install capture daemon → `chmod 755` + `a+r` on `/var/log/t2-aks-capture`
   → install `EnablePrivateLogging.mobileconfig` → confirm `PRIVATE_DATA`
   → cold reboot.
2. **B mine:** around `loadCatacombForComponent` / `loadCatacombForUser`,
   search for `performCommand … 64` (decimal). Record present/absent (+
   `inValue`/`inSize` if present). Prediction: absent (boot load is
   host-side unarchive).
3. Enroll one finger, lock-screen unlock once; confirm both succeed.
4. Export newest capture set + `/Library/Catacomb/<UUID>/` +
   `t2-keybags.tar.gz` to `~/Private/` and USB. **Skip ESP FDR** (absent/N/A).
5. `sudo ./uninstall.sh`; remove the Device Management profile.
6. Warm reboot to Omarchy (no sensor reset) to restore `0x42=1`.
7. Report back: `sw_vers`, `PRIVATE_DATA` state, enroll/unlock success,
   Mesa-64 verdict, USB contents confirmed.

### 3. Retry `0x40` / match

Live `0x40` or match/`0x04` / ACM work is open for assisted research.

### 4. Linux-native enroll / ACM

Open for assisted research.

### 5. Last resort (EP7)

EP7 AKS stays muted (separate transport dead-end); fingerprint path is BridgeXPC.

## Open items

- Mute AKS EP7 (dead-end transport; BridgeXPC path preferred)
- Live Mesa match / `0x40` / ACM canaries (unblocked 2026-09-08)
  - 2026-09-13: Fork A match opens (status 0, no 261) but yields no
    `match_result` in 5 windows incl. calibrated + confirmed touch —
    see `MATCH_FORKA_2026-09-13.md`. Warm `0x42=1` preserved throughout.
- Sequoia Mesa decimal-64 boot mine — DONE 2026-09-13 (third independent
  confirmation): full-boot sweep **0 hits** for `performCommand … 64`;
  boot histogram without 64; unlock framing `48 → 84 → 39 → 84 → 12 → 74`
  with match traffic on 74 — see `MESA64_FRESHBOOT_MINE_2026-09-13.md`.
  Path B is a command macOS doesn't use; closed.
- Blind `0x40` / reset-load loops (open)
  - 2026-09-13: no-reset `0x40` master+user re-run on warm `0x42=1` boot:
    **257/257**, snapshots identical before/after, warm preserved.
  - 2026-09-13: full reset → `no_catacomb(0xffffffff)` → `0x40` re-run:
    reset 0, `no_catacomb` 0, **257/257**, `0x42` went **1→0**.
    Reset alone again did **not** clear (count 1 after reset).
    Air now at `0x42` count **0** — re-warm via macOS before any match work.
- Host-parity-only `0x40` (still 257)
- `0x20` then `0x40` (cal OK, load still 257)
- Assuming power-off clears enrolled `0x42` (falsified — noted)
- `0x08` as alias for `0x42` (investigation open)
- Linux-native ordinary (token-free) enroll `0x03` uid 501 (2026-09-13):
  start rejected **status -3**, no events, no state change — with and
  without same-session sensor context. Pre-enroll context probe passes
  every precondition (bridge init, readiness, provisioning, protected
  config, xART, catacomb consistency), so -3 is purely the dispatch
  gate. SEP still empty.
- ACM-token path, first live run as root (2026-09-13 late, `/dev/t2-acm`
  generation 1): context **create/delete succeeded** (tracking 21 B),
  policy-1007 preflight = unsatisfied **type-1 passcode requirement**
  (state 1, flags 1), wall at exactly **`password-binding`** with
  mandatory cleanup — no `/run/t2-touchid/keybag.env`, no installed
  `t2-aks-tool`, EP7 canary still -110. No authorized 16 B form exists,
  so no `authorized_enroll_fields` dispatch was built. Endpoint-10
  itself is alive; the block is the keybag-bound password proof.
- `0x30` getEnabledForUnlock shape recovered (2026-09-13, Linux-only):
  v1 (empty or uid501) → status 0, 1 byte; reads **enabled=True** for
  uid 501 even with empty SEP. v0 → `0xe00002c2`. `0x11` empty-in →
  status 22 (needs its ~20 B input; not sprayed).
- Re-mine of the 2026-09-06 cold-boot capture (2026-09-13 late, no boot):
  **1,731** tagged `performCommand` events across boot/enroll/unlock
  contain **zero opcode-64** — second independent confirmation Sequoia
  never sends Mesa `0x40`. Path B is not a wrong constant, it is a
  command macOS doesn't use. Unlock framing is `48 → 84 → 39 → 84 →
  12 → 74` (match traffic on **74** between 84s); opcode **65** appears
  exactly once, in enroll, unannotated.
- Bounded read-only probes, operator-authorized, 9 calls (2026-09-13
  late, empty SEP, state verified unchanged): `0x08` v1 → **status
  265** (novel), v0 → `0xe00002c2`; the 400 returned bytes are
  **all zero** — the daemon returns the preallocated out-buffer
  unfilled on error paths, so `out_len == cap` on failures is
  meaningless everywhere (status only). `0x11` zero-fill at 16/20/32 →
  **22 every time**: content-gated, not length-gated; oracle closed.
  `0x41` ver=1/val=0/empty → `0xe00002c2` (one call, not chased).
  Lesson: brute-forcing small fields cannot converge — remaining
  unknowns sit behind enrolled SEP state or the framework binary.
- APFS offline-read attempt (2026-09-13 late): built `apfs-fuse-git`,
  but open fails at **`KeyManager` init** in both `apfs-fuse` and
  `apfsutil`, before any password prompt. T2 + Sequoia + FileVault
  container keybag is SEP-wrapped — no Linux tooling unwraps it.
  Mount track dead; framework binaries stay behind a macOS boot.

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
| `PARKED_2026-09-08.md` | authorization record; forks unblocked |
