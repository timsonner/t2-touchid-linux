# Post-reboot proof: re-enrolled set survives and verifies (2026-09-20)

Branch: `research/mba91-aks-ep7`. No live gates involved.
Shapes/statuses/counts only.

## Verdict

The E4r2 set (index, middle, re-enrolled ring) **survives reboot
and verifies**, closing the delete-ladder lifecycle loop end to
end: 2→3 (E4) →2 (D2) →2-refused (E4r) →3 (E4r2) →3-stable (here).

## Sequence (fresh boot)

1. Installed chain self-started: transport (pinned), keybag-load
   (fresh handle 7), `fprintd.service` on the bus.
2. Operator unlock of both bags `status=0` (carrying `sudo` showed
   the PAM fingerprint prompt, timed out without a touch,
   password fallback authorized — fallback seen live again).
3. Fingerless inventory: per-user 3, global 3, reconciled true,
   repeat-equal true, free 0/5, SKS `0x228`.
4. Daemon verifies: ring → `verify-match` exit 0; index →
   `verify-match` exit 0.
