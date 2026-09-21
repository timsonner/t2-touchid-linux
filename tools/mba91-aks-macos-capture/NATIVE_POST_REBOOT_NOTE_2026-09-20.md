# Native post-reboot note: -5 stable, unlock-op flaps (2026-09-20)

Branch: `research/mba91-aks-ep7`. All live gates disabled in source
(verified). Shapes/statuses/counts only.

## Stable findings (both boots)

- Create (v5) works repeatedly: handles 8 (C1), 14 (C1 rerun),
  both `sep_status` 0 with UUIDs verified.
- Export/reload/bind work repeatedly (C3, C4-bind `status=0`).
- Password ops against native handles refuse `-5` on the
  authoritative path: `verify-password-only` (-5), fresh
  `verify-password-acm` with a new context (-5, C4b on handle 14
  this boot). The fresh bag holds no password credential —
  consistent pre- and post-reboot. Activation ceremony (mapping /
  owner proofs) remains the unported piece.
- macOS bags unlock `status=0` on every boot with the creation
  (macOS) password. Templates steady at 3/3 throughout.

## Unstable edge (unlock op vs native handles)

`unlock-keybag` on native handles answered evaluated-refusal
(rc=1) pre-reboot and transport failure (EREMOTEIO) post-reboot —
same commands, same handles family, while uuid/load/set-system
and macOS-handle unlocks behave identically both boots. Op- and
handle-scoped flap at the mailbox layer; mechanism unknown, no
state impact either way (identities 3/3 repeat-equal after).
Not the main line (verify path is stable and authoritative);
recorded so a future driver pass can distinguish wedge from
SEP-side per-boot state. Candidate confound on record: boot-time
module load via service (with `probe_capabilities=1`) vs manual
loader (without) — untested as a variable, do not over-read.

## Standing state

Gates closed. Native handles (8/9/10/11/13/14 family) live this
boot only; C3 test file quarantined; `-502` binding parked on a
test handle (rebind or reboot clears it — document before reuse).
macOS reader fully working (sudo by finger, password fallback).
