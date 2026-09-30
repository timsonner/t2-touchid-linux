# NEXT_STEPS standing-state addendum — 2026-09-30 inventory

> Prepend / replace the "Standing state" block in
> `tools/mba91-aks-macos-capture/NEXT_STEPS.md` when root write is available
> (that file is root-owned 0644 on MBA91). Facts below are already in
> `INVENTORY_RO_501_20260930-174149_PUBLIC_SUMMARY.md`.

## Standing state (2026-09-30, after RO inventory)

Transport is loaded again on kernel `7.2.7-arch1-Watanare-T2-2-t2`
(`t2_sep_transport` + patched `applesmc` boot_state). Read-only inventory
for uid 501 completed public-only (private dump gated incomplete).

| Fact | Evidence |
| --- | --- |
| Per-user `0x42` status **0**, output nil → identity count **0** | `INVENTORY_RO_501_20260930-174149_*` |
| Catacomb UUID/hash (`0x38`/`0x3A`) status **22** — no user component for 501 | same |
| SKS lock (`0x27`) **21** (`0x15`, cold) | same |
| BridgeXPC port **49208**; private inventory not written (gate incomplete) | same; oneshot fix in `t2-inventory-ro-501.*` |
| Kernel upgrade had dropped modules; rebuild+install restored transport | `AGENT_STATUS_2026-09-30.md`, `ELEVATE_NEEDED_2026-09-30.txt` |

Hard bans unchanged: no enroll start, no bag create, no `0x21`, no second bag.

## Next

1. **macOS one-finger re-enroll** for uid 501 (System Settings → Touch ID).
   Proven path to Catacomb user component + warm SKS + non-nil `0x42`.
2. Warm-reboot to Linux; re-run RO inventory before any password-bound
   Linux enroll research.
