# Milestone: Touch ID sudo works in Omarchy on MBA91 (2026-09-20)

Branch: `research/mba91-aks-ep7`. Product state (installed system
config + services); science in the linked verdict notes.

## What works (all live-proven tonight)

- **Boot chain:** `t2-sep-transport` (pinned warm-safe modprobe set)
  → `t2-keybag-load` (handle parsed per boot) → `fprintd.service`
  running the MBA91 verify-only daemon on `net.reactivated.Fprint`.
  First link initially failed (module never installed to
  `/lib/modules` — DKMS absent); fixed by installing the `.ko` +
  `depmod`. Sleep policy `s2idle` active.
- **Daemon:** `fprintd-list` shows the alias; `fprintd-verify -f any`
  returns `verify-match` (exit 0) for enrolled fingers and
  `verify-no-match` (exit 1) for the unenrolled ring finger,
  all through D-Bus with terminal signals.
- **PAM/sudo:** templates installed with automatic backups;
  enrolled index + middle authenticate, unenrolled ring is
  rejected, password fallback preserved via `system-auth`.
  Rollback: `sudo tools/rollback-pam.sh`.

## Proving chain (this branch)

Session-74 closed S1–S5 (session-identity, H1 dead) →
credential-set F1/F2 (first `match_result`, first `matched:true`) →
selectivity N1/N2 → routine R1 → keybag lever K1/K2 (token-free
verifies with unlocked bags; per-match passwords unnecessary) →
safe loader → installer gaps → verify-only daemon (signal-body bug
fixed) → this milestone.

## Known envelope (not blockers)

- Matcher goes mute after long per-boot match streaks (no
  touch signature, idle ordinals); reboot restores. Maps to
  `verify-unknown-error`; password fallback covers it.
- `dkms` package absent: rerun installer after kernel upgrades.
- Per-boot keybag unlock is password-assisted until an
  unattended credential is provisioned (operator's call).
- Lock-screen Touch ID flow installed, not yet exercised.
- Linux-native enrollment out of scope; macOS-enrolled identities
  are the working set; cross-OS survival untested.
