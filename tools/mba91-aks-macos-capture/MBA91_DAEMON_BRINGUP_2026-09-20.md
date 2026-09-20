# MBA91 daemon bring-up: signals fixed, matcher mute under study (2026-09-20)

Branch: `research/mba91-aks-ep7`. Daemon runs, lists, delivers
terminal signals. Match verdicts through D-Bus not yet observed —
see mute study below. Shapes/statuses/counts only.

## Built (verify-only, all gated fail-closed)

- `src/t2-fprintd-mba91.py`: purpose-built MBA91 facade reusing the
  proven claim/caller/sender modules. Single compatibility alias,
  token-free opcode-4 backend under the shared operation lock,
  terminal-verdict mapping (match → `verify-match`, terminal
  non-match → `verify-no-match`, silence → `verify-unknown-error`,
  never a rejection). No enrollment, no deletion, no Catacomb, no
  adaptive sync. Installed into `/opt` by install.sh.
- `systemd/system/fprintd.service.d/10-mba91.conf`: selects the MBA91
  daemon; installed only when `T2_TOUCHID_MBA91_WARM_SEP=1`.
- install.sh: dbus system.d dir creation (usr-merge hosts).
- System `fprintd` package installed for the PAM module + CLI; our
  unit owns `net.reactivated.Fprint`.

## Bugs found and fixed

- **Signal body must be a list.** dbus-next `@signal()` verdict with
  `-> "sb"` must `return [result, done]`; returning a tuple kills
  the emission inside the task and starves clients with zero
  terminal signals (client hung 90 s+). Fixed; clients now terminate.
- **pkill -f footgun.** A `pkill -f <pattern>` issued from a shell
  whose own command line contains the bare pattern kills the shell
  itself. Kill by exact PID; keep one pattern per command.

## Proven live

- Daemon owns the bus; `fprintd-list tim` returns the alias;
  `fprintd-verify` runs full lifecycle to a terminal signal.
- `ListEnrolledFingers` reflects live SEP inventory (2 → alias;
  empty → NoEnrolledPrints).

## Mute study (open, sensor-side)

Late in the K2 boot, after ~6 match windows and ~1 h uptime, the
matcher stopped emitting verdicts: windows open (start 0), idle
ordinals only (53/80/90/64/81/63/91 pattern), **no 73/3242 B
finger-present event** despite confirmed full 60 s holds with both
enrolled fingers. Ruled out: timing (synchronized TOUCH NOW +
60 s), finger-specificity (index + middle), transport/ACM/keybag
(all green: `0x42`=2 repeat-equal, SKS stable `0x219`, policy-1007
preflight nominal, keybags unlocked), daemon plumbing (manual
K2-exact probe mutes identically).
- Device-lock correlation: SKS drifted `0x228`→`0x219` around the
  onset, but the bit meaning is borrowed from another build's
  formatter (distrusted) and a lock/unlock cycle did not clear it.
  Unproven either way.
- Leading hypothesis: sensor-side fatigue per boot (window count or
  wall time); reboot is the honest reset (never the sensor-reset
  command — it wipes identities). K2 proved post-reboot health.
- Product implication (preliminary): mute maps to
  `verify-unknown-error`, and PAM falls back to password — an
  acceptable degradation if the envelope is characterized.

## Next steps (resume here)

1. Reboot → loader → unlock → verify → one right-index window.
   Verdict → envelope characterization (windows-per-boot), and the
   daemon gets its first live D-Bus verdict retry under fresh
   sensor.
2. SKS semantics on THIS build (`23P6068`) from observation, never
   borrowed: log SKS at every window with lock/mute/verdict state.
3. Then PAM templates + sudo control.
