# Post-reboot proof: Linux enrollment survives and verifies (2026-09-20)

Branch: `research/mba91-aks-ep7`. No live gates involved (all
verification through the installed daemon + read-only probes).
Shapes/statuses/counts only.

## Verdict

The Linux-enrolled ring identity **survives a reboot and verifies**.
Post-reboot proof complete: stable 3/3 reconciled, ring
`verify-match`, index `verify-match`. The E4 enrollment is closed as
proven-durable. (Side note: the first "ring" hold was actually index
— both fingers now have independent post-reboot positives.)

## Sequence (fresh boot)

1. Installed chain self-started: `t2-sep-transport` (pinned params
   via modprobe.d + installed `.ko`), `t2-keybag-load` (fresh
   handle 6, parsed clean), `fprintd.service` (MBA91 daemon on the
   bus). Only prior gap (module never in `/lib/modules`) stayed
   fixed.
2. Operator unlock of both bags: `status=0` (handle 6). Note: the
   carrying `sudo` invocation exercised production PAM live — no
   finger presented, timer expired, password fallback authorized.
   Fallback path confirmed in passing.
3. Fingerless inventory: per-user 3, global 3, reconciled true,
   repeat-equal true, free 0/5, SKS `0x228`, gate complete.
4. Daemon `fprintd-verify -f any`: index → `verify-match` exit 0;
   ring → `verify-match` exit 0.

## What this closes and what is next

- Closed: E4 pending status. The MBA91 enrollment track is now:
  open (E1) → dance (E4) → attribute (ring) → survive + verify
  (here). Capacity FULL — no further enrollment possible.
- Next candidates: lock-screen unlock flow, unattended credential
  decision, `dkms` package, and — when the operator chooses — the
  macOS-boot cross-OS question (still deliberately untested).
