# Handoff: MacBookAir9,1 AKS EP7 mute (for upstream / bent agents)

**Branch:** https://github.com/timsonner/t2-touchid-linux/tree/research/mba91-aks-ep7  
**Doc:** [`RESEARCH_MBA91_AKS.md`](RESEARCH_MBA91_AKS.md) @ `bcc5040`+  
**Machine:** MacBookAir9,1 · bridgeOS `23.16.16068` · SEP PCI `106b:1802`  
**Intent:** Reusable negative result + research tooling — not a claim of Air Touch ID support.

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
4. Next lever we believe in: **macOS first AKS txn capture** on this bridgeOS vs MBP `23P1072`.
5. Do **not** invent SBIO app / xART payloads; EP8 already NACKs SET_OOL.

## Not included (private)

Keybags, catacomb, host sudoers/LUKS helpers — intentionally off-git.

## Suggested upstream use

- Cite as Air / `23.16.16068` negative result in compatibility notes
- Reuse `aks_lab` / `t2-sep-lab` ideas for other mute-EP bring-up
- Cross-check bent MBP startCPU/MSI path (already aligned; AKS still diverges on Air)
