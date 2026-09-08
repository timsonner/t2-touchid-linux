# Handoff: MacBookAir9,1 AKS EP7 mute (for upstream / bent agents)

**Branch:** https://github.com/timsonner/t2-touchid-linux/tree/research/mba91-aks-ep7  
**Doc:** [`RESEARCH_MBA91_AKS.md`](RESEARCH_MBA91_AKS.md) (Linux EP7 parked; macOS capture done)  
**Machine:** MacBookAir9,1 · bridgeOS `23.16.16068` · SEP PCI `106b:1802`  
**Intent:** Reusable negative result + research tooling — not a claim of Air Touch ID support.

**Authorization:** This research runs under **Track A** — independent ownership
research: operator-owned hardware and biometric material, controlled private
lab, operator's written authorization; no third party is implicated. The
BridgeXPC A/B/C forks (match, `0x40` load, empty-SEP envelope) are authorized
and unblocked. See [`docs/LAB_PROTOCOL.md`](LAB_PROTOCOL.md) for scope,
boundaries, and the future-agent due-diligence checklist.

## What works on Air

- EP0 NOP, MSI (2), Apple `_startCPUGated`, AKS OOL register (16 KiB)
- ACM EP10 SCRD (~1 ms)
- EP12 SET_OOL ACK (SSE-class; no app traffic sent)
- Research `/dev/t2-sep-lab` + `tools/t2-sep-lab.c` (in-session probes without rebuild)

## What does not

- AKS EP7 service ops: `0x19`, `0x4d`, `0x06`, `0x2a` — timeout, `ool_out_nonzero=0`
- Passive `0xfd` discovery: empty at 1s and dual 10s (`pre-ool` + `post-acm`)
- Bent **exact** full-wire `0x4d` / `0x2a` (codec from `bentsignal/t2-omarchy` `aks-transport.py`) — still mute
- EP8 SET_OOL → `EREMOTEIO`; EP0 size opcodes `4`/`5` → SEP `0x1` reject

## Takeaways for other agents

1. Do **not** burn the same AKS wire/ABI matrix on Air without a new lever.
2. Mute is **service-level**, not dead SEP mailbox (ACM proves transport).
3. Lab header path is ruled out vs bent codec.
4. macOS **os_log / Mesa / BridgeXPC** cold-boot+enroll+unlock capture: **done** (2026-09-06).
   Not the same as raw mailbox EP7 OOL bytes — see `tools/mba91-aks-macos-capture/`.
5. Next Linux-side levers: map BridgeXPC/Mesa bring-up, or true mailbox capture if still required —
   **do not** reburn the EP7 ABI matrix alone.
6. Do **not** invent SBIO app / xART payloads; EP8 already NACKs SET_OOL.

## Not included (private)

Keybags, catacomb, host sudoers/LUKS helpers — intentionally off-git.

## Suggested upstream use

- Cite as Air / `23.16.16068` negative result in compatibility notes
- Reuse `aks_lab` / `t2-sep-lab` ideas for other mute-EP bring-up
- Cross-check bent MBP startCPU/MSI path (already aligned; AKS still diverges on Air)

## macOS capture kit

`tools/mba91-aks-macos-capture/` — boot/enroll/unlock unified-log LaunchDaemon +
private-data profile. Captures Mesa/BridgeXPC + AKS kernel notifications; not
raw SEP mailbox OOL.


## macOS capture — verified (2026-09-06)

Cold boot + enroll + lock-screen unlock captured on MBA91 with
`tools/mba91-aks-macos-capture/`. Private logs under Tim’s
`~/Private/t2-aks-capture/` (not in git). ESP FDR backup was attempted next; path was absent and is not required on this T2 Air. Details:
[`VERIFIED_SESSION_2026-09-06.md`](../tools/mba91-aks-macos-capture/VERIFIED_SESSION_2026-09-06.md).


## ESP FDR — MBA91 finding

After wipe + macOS reinstall, ESP had **no** `EFI/APPLE/EMBEDDEDOS/FDRData`.
Touch ID still worked. Treat T1-style FDR preserve as **non-blocking** for this
T2 Air; do not expect Linux install to recreate it. See RESEARCH +
`tools/mba91-aks-macos-capture/VERIFIED_SESSION_2026-09-06.md`.

## Lane B progress

Catacomb load/save + Bridge/Mesa ordering documented in
`tools/mba91-aks-macos-capture/CATACOMB_BRIDGE_SEQUENCE.md`.
Recommended next: enrolled cold-boot reload capture (still on macOS).

Enrolled cold-reboot A/B (`28BE7F9F-…`) confirms non-empty load vs empty Phase A; see `CATACOMB_BRIDGE_SEQUENCE.md` Phase A′.
