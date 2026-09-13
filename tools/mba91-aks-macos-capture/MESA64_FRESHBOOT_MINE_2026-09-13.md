# Sequoia single-boot trip — Mesa-64 mine + unlock + exports (2026-09-13)

Public-safe. No identity UUIDs, serials, catacomb bytes, keybags, or raw
Mesa payloads. Only counts, status codes, event kinds, and command shapes.

**Host:** MacBookAir9,1 · macOS 15.7.9 · capture daemon running, log mode
`STREAM_LIVE PRIVATE_DATA` for the whole trip.
**Authorization:** Track A (operator-owned hardware + own finger,
`docs/LAB_PROTOCOL.md`).
**Checklist source:** `NEXT_STEPS.md` §2b (single boot: B mine + exports +
re-warm). Unlock-only variant (existing uid-501 enrollment kept, no live
enroll).

## 2b.1 — capture armed

- Daemon `running` at trip start; current-boot set
  (`*.boot.txt` + `*.logstream.log` + `*.snapshot.log`) growing
  (~2.6 MB / ~25k lines pre-unlock).
- `PRIVATE_DATA` confirmed on for the boot.

## 2b.2 — B mine verdict: Mesa-64 absent (fresh boot)

- `loadCatacombForUser: 501` present; component path is host-side
  unarchive (`catacombFileNameForComponent` → per-user `.cat` →
  `unarchiveCatacombDataForComponent` → keybag UUID lookup). No Mesa push
  in the window.
- Exact first-arg sweep over the full boot log
  (`performCommand:version:inValue:inData:inSize:outData:outSize: 64 `):
  **0 hits**.
- Full first-arg histogram this boot:
  `12, 26, 39, 44, 48, 58, 60, 67, 74, 80, 82, 84` — no 64.
- ACM-layer `cmd(...)` histogram: `2, 3, 19, 22, 25, 26, 36` — no 64.
- `cacheAccessories` (1 accessory) logged after load, result 0.
- Third independent confirmation (after the 2026-09-06 cold-boot re-mine
  and the stale-private-copy sweep): Sequoia boot load does not send
  Mesa decimal-64. Path B is a command macOS doesn't use.

## 2b.3 — unlock confirm

- Lock (Ctrl+Cmd+Q) → Touch ID unlock succeeded on live capture
  (+~3k lines).
- Unlock framing at match minute, in order:
  `48 → 84 → 39 → 84 → 12 → 74`
  (matches the prior re-mine framing `48 → 84 → 39 → 84 → 12 → 74`
  with match traffic on 74 between 84s).

## 2b.4 — exports

- Current-boot triple copied to `~/Private/t2-aks-capture/` and to
  `mba91-backup-<date>/` on USB (logstream ~3 MB at copy time).
- Catacomb UUID tree (`master.cat`, per-user `.cat`, `biolockout.cat`)
  copied to both destinations.
- `macos-export-keybags.sh` run; dated `t2-keybags` archive kept in
  `~/Private/t2-keybags/` and on USB. ESP FDR skipped (absent/N/A on
  this Air).
- USB verified then ejected.

## 2b.5–2b.6 — teardown / re-warm (ops)

- `uninstall.sh` run; daemon gone from launchctl; logs kept on disk.
- Operator removes the Device Management private-logging profile via GUI.
- Warm reboot to Omarchy with **no sensor reset** to restore the Linux
  warm identity (Linux SEP was at `0x42` count 0 before this trip).
