# MBA91 research handoff (2026-09-30 ~17:50 MDT)

## Transport: FIXED for 7.2.7

| Item | Result |
| --- | --- |
| Kernel | `7.2.7-arch1-Watanare-T2-2-t2` |
| `t2_sep_transport` + patched `applesmc` | loaded; `/dev/t2-aks` present |
| Earlier gap | modules missing after upgrade (no dkms); rebuild+install restored |
| Elevate notes | `ELEVATE_NEEDED_2026-09-30.txt` (password was required for install) |

## Inventory (RO 501) — 17:41 MDT

Public facts only (`private_inventory_complete=false`):

| Fact | Value |
| --- | --- |
| `0x42` | status **0**, nil → count **0** |
| Catacomb UUID/hash | status **22** (no user component) |
| SKS lock | **21** (`0x15`, cold) |
| Port | **49208** |
| Artifacts | `INVENTORY_RO_501_20260930-174149_{REPORT,PUBLIC_SUMMARY}.*` + STATUS1_DIAG |

Earlier oneshot failures (no port / private-gate raise) are kept as
`INVENTORY_RO_501_20260930-173616_*` and `…-173845_*`. Fix notes live in
`t2-inventory-ro-501.sh` / `.service` and the PUBLIC_SUMMARY "Oneshot fix" section.

## NEXT_STEPS.md

Standing-state text for 2026-09-30 is in
`tools/NEXT_STEPS_STANDING_2026-09-30.md`. The live
`tools/mba91-aks-macos-capture/NEXT_STEPS.md` is still the 2026-09-26
block (root-owned; needs `sudo` to prepend).

## Next (operator)

**macOS one-finger re-enroll** for uid 501, then Linux RO re-inventory.
Hard bans: no enroll / bag create / `0x21` / second bag on Linux.
