# BridgeXPC capture session — 2026-09-07 (MBA91)

## Setup

- Script: `capture-en3-bridgexpc.sh` (90s window)
- Output dir (Private): `~/Private/t2-bridgexpc-research/capture-20260907T044748Z/`
- Operator: locked + Touch ID unlocked **twice** during the window

## Results

| Artifact | Outcome |
| --- | --- |
| `en3.pcap` via `pktap,en3 -y RAW` | **Empty** (24-byte pcap header only) — recipe bug on this Sequoia/Air |
| `unified-log.ndjson` | **Good** (~3.2 MB); biometrickitd BridgeXPC + Mesa traffic |
| Sanitized pcap JSON | N/A (no packets) |

## Unified-log evidence (public-safe)

Two unlock-adjacent clusters (~22:48:08 and ~22:48:36 MT):

- Live `BridgeXPC` connection: header 16 B; RX body sizes seen include **116, 119, 149, 153, 201, 207, 213, 368**; TX message sizes **128, 162, 166, 185, 188**
- `getEnabledForUnlock → 1` (Mesa opcode **48**)
- `performCommand` opcode counts in-window: **48×8**, **46×8**, **39×6**, **84×4**, **74×2**, **62×2**, **63×2** (ConfirmSave), plus catacomb family **60/61/56/58/80**, cancel **12**, etc.

This matches the previously mined unlock → match → post-unlock save/ConfirmSave path. It does **not** yet give byte-exact TCP frames (need a working pcap).

## Follow-up

1. Re-run with fixed script (direct `-i en3`, optional `pktap` without `-y RAW`).
2. Keep using size timelines from os_log as a Sequoia framing check vs bent even before pcap works.

## Second run (045414Z) — Ctrl-C after double unlock

- Script: fixed `pktap,en3` twin (PKTAP + RAW)
- Operator: locked + unlocked twice, then Ctrl-C
- `en3-pktap.pcap` / `en3-raw.pcap`: **0 packets** (tcpdump listened; filter saw nothing)
- `unified-log.ndjson` (~2.9 MB): **good** — 8× `getEnabledForUnlock → 1`, ConfirmSave **63×2**, opcodes match prior unlock/save pattern
- Conclusion: host BPF on `pktap,en3` is blind to BiometricKit BridgeXPC on MBA91 Sequoia; prefer os_log sizes + codecs.
