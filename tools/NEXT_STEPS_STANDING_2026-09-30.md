# NEXT_STEPS standing-state addendum — 2026-09-30 inventory (updated 22:28 MDT)

> Folded into the top of `tools/mba91-aks-macos-capture/NEXT_STEPS.md` on
> 2026-10-01. This file remains the night's record. The live standing
> state is the 2026-10-01 block in `NEXT_STEPS.md`.

## Standing state (2026-09-30, post macOS one-finger + private dump)

Transport OK on `7.2.7-arch1-Watanare-T2-2-t2`. macOS one-finger enroll for
uid 501 survived warm reboot. RO inventory public+private complete
(`INVENTORY_RO_501_20260930-222840_*`; interpretation
`CATACOMB_IDENTITY_LAYOUT_20260930-222840.md`).

| Fact | Evidence |
| --- | --- |
| Per-user `0x42` count **1** (status 0, 20 B) | `…-222840` |
| Catacomb UUID/hash status **0**; component present | same |
| Catacomb state words **`[0xFFFFFFFF, 3, 501, 3]`** | same |
| SKS lock **16 = 0x10** (warm) | same |
| Free `0x41` **2** / capacity **5** | same |
| Private dump persisted (`priv_rc=0`) after journal dir `0700` fix | `/var/lib/t2-touchid/inventory-journals/inventory-ro-501-20260930-222840.private.json` |
| BridgeXPC port **49183** | same |

Hard bans unchanged: no enroll start, no bag create, no `0x21`, no second bag.

## Next

1. **Password-bound match research** (not enroll): confirm private UUID/hash
   presence, then follow `MATCH_BROKER_DESIGN_2026-09-20.md` /
   `NEXT_STEPS.md` authorized-match path with explicit operator approval.
2. Optional: patch oneshot `mkdir -p` → `install -d -m 0700` for journals.
