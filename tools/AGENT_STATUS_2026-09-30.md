# MBA91 research handoff (2026-09-30 ~17:50 MDT)

Historical night-of note. Current narrative:
[`docs/FINDINGS.md`](../docs/FINDINGS.md). Live standing:
[`mba91-aks-macos-capture/NEXT_STEPS.md`](mba91-aks-macos-capture/NEXT_STEPS.md).

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

This file is the 2026-09-30 17:50 handoff. The live standing state is the
top block of `tools/mba91-aks-macos-capture/NEXT_STEPS.md`.

## Next (operator)

The macOS one-finger re-enroll completed later the same night. On
2026-10-01 the approved match canary loaded `native-501.kb` and the
handle-1 unlock returned SEP `-5`. Current orders are the standing
block in `NEXT_STEPS.md`. Track A approval is unchanged
(`docs/LAB_PROTOCOL.md`).
