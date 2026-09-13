# Fork A live match attempts (2026-09-13)

Public-safe. No identity UUIDs, catacomb bytes, keybags, or raw Mesa payloads.
Only counts, status codes, event kinds, and command shapes.

**Host:** MacBookAir9,1 · Omarchy · kernel `7.1.8-arch1-Watanare-T2-2-t2` ·
T2 NCM `enp116s0f1u1` · peer `fe80::aede:48ff:fe33:4455` (ping-verified).
**Peer HELO:** `bkremoted` / BridgeXPC **39** / OSBuild **23P6068**.
**RSD BiometricKit port this boot:** `49225` (dynamic; rediscover every boot).
**EP7 AKS:** untouched, still parked.
**Authorization:** Track A (operator-owned hardware + own finger, `docs/LAB_PROTOCOL.md`).

## Warm gate (passed, no re-warm needed)

`bridge-xpc-probe.py --initialize --full-inventory`:

| Check | Result |
| --- | --- |
| `0x42` per-user count | **1** (uid 501, prefix field) |
| per-user/global reconciled | true |
| protocol v2 attested | true (via global-identity command) |
| SKS lock state | `0x10` (warm; cold is `0x15`) |
| `full_snapshot_repeat_equal` | true |
| private gate | complete, no failures |
| capacity | max 5, free 2 |

Sensor read-only: `sensor_ready=true`, info `[1,12,3]`.

## Match attempts (6 windows, 0 verdicts)

All via `bridge-xpc-probe.py --initialize --identity-list --match-seconds N
--stop-on-match-result`. No `--reset-sensor` in any window (warm preserve).
`--resolve-any-identity-slot` was tried once and fails closed here by design:
no `/var/lib/t2-touchid/catacomb` exists on this Air, so slot/name-resolved
matching has no local baseline — plain all-identities match used instead.

| # | Flags | Window | Finger | `match_start` | `match_rejected` | `match_result` events |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | default (flags 0) | 25s | absent | 0 | none | 0 (status/stat only) |
| 2 | default (flags 0) | 30s | ready, timing unclear | 0 | none | 0 |
| 3 | `--match-processed-flags 1` | 30s | held full window | 0 | none | 0 (8 events) |
| 4 | `--load-calibration` (FDR 61407 B, status 0) | 10s | **not touched** (operator confirmed) | 0 | none | 0 |
| 5 | `--load-calibration` (FDR 61407 B, status 0) | 10s | **touched immediately** (operator confirmed) | 0 | none | 0 (4 status + 3 statistics) |
| 6 | default (flags 0) | 60s | **held continuously** (operator confirmed full-window contact) | 0 | none | 0 (6 status + 3 statistics; ordinals 63/64/80/81/90/91) |
| 7 | **74 framing** (same 68 B + counted blob, Sequoia prelude `48→84→39→84→12`) | n/a (refused at start) | held (irrelevant — never opened) | **258** | n/a | none (probe `bridge-xpc-match74-probe.py`, warm-gated, one shot, no variants) |
| 8 | **74 framing + unlock flags 1** (same script/prelude) | n/a (refused at start) | held (irrelevant — never opened) | **258** | n/a | none (one shot, no variants; refusal is flags-independent) |

Cancel after every window: status 0. Warm `0x42 count=1` re-verified after
all attempts — none of these paths clear the identity.

## Interpretation

* Fork A match **opens reliably** on this Air (no `261` policy gate, no
  rejection) with the exact MBP-shaped command: opcode `4`, counted blob
  (`count + N×20 B` from `0x42`), 68-byte options (`flags, uid, 60×0`).
* The sensor **does not convert touches into `match_result` events** in any
  tried variant (plain, unlock-flags, calibrated). Sensor reports ready;
  status ordinals cycle (63/64/78/81/90/91) identically with and without
  finger — no finger-present signature observed at this layer.
* Calibration is **not** the missing lever for opening match (opens without
  it) nor sufficient for a verdict (still mute with it, status 0 both).
* Continuous full-window contact is **not** the lever either (window 6,
  60 s held, still mute with the same status-ordinal cycle).
* Sequoia comparison (2026-09-13 fresh log, 30k lines): working unlock
  sends **zero opcode-4** — prelude is `48 → 84 → 39 → 84 → 12 → 74`.
  Open-but-mute on 4 is consistent with 4 being, like 64, a command macOS
  doesn't use on this path; the verdict likely lives on the 74/ACM side.
* Window 7 (2026-09-13, warm SEP, no module loaded): 74 with Fork A
  framing refused at dispatch (**258**) after a clean all-zero Sequoia
  prelude. 4 opens / 74 refuses with identical payloads — 74 wants a
  different precondition (ACM-bound context? different payload class?)
  or is not match-start on this build (label stays medium-confidence).
  Single shot, no variants; warm `0x42=1` verified preserved after.
* Window 8 (unlock flags 1): identical **258** refusal. The 74 gate is
  flags-independent — 74-as-match-start with Fork A framing is closed
  as a hypothesis. Remaining 74 path, if any, is ACM-context-gated
  match (keybag track), not payload shape.
* SKS side-observation: coupled-path `0x27` v1 read `0x10` at warm-verify
  and `0x810` (stable across re-reads) after the 74 run; `0x42` intact
  throughout. First observed post-run — correlation with the refused
  start is unproven (intervening read-only sessions exist). Meaning of
  `0x810` unknown; no action taken. Related framing note: direct-path
  SKS payload layout differs from coupled path (warm bytes `10080000`).
* This is an **open-but-mute** result, distinct from the EP7 mailbox mute:
  transport + session + identity list + match-start all succeed; only the
  verdict event is absent.

## Not tried (deliberately)

* `--reset-sensor` before match (would clear the warm identity; contradicts
  the preserve ladder — see `WARM_IDENTITY_AB_2026-09-07.md`).
* `0x40` load / enroll / delete / EP7 (separate forks; out of scope).
* `fprintd --warm-verify` daemon promotion (gated on a first probe verdict;
  code is staged: `--warm-verify` flag + `30-warm-verify.conf` + tests).

## Next

* One variable at a time: lift/place rhythm vs hold (uncontrolled so far),
  longer window with confirmed continuous contact, or Sequoia-side match
  traffic comparison (Fork B mine) to see what a working verdict's
  prelude looks like.
* Raw per-window JSON (counts/statuses only, no identifiers) kept in
  operator-private storage, not in git.
