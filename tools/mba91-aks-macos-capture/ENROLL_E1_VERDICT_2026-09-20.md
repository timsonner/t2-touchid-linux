# E1 verdict: enroll start opens with zero-group bytes (2026-09-20)

Branch: `research/mba91-aks-ep7`. All live gates disabled in source
(verified). Shapes/statuses/counts only — no payloads, no keybags,
no passwords, no identity UUIDs.

## Verdict

**`dispatch_status: 0` — the enroll start OPENS.** The only change
from the refused September construction is bytes [48:52] of the 68 B
token (zero group here, u32=1 there). The 4-byte group theory is
confirmed; the 22 wall is down and the enroll track reopens at E4.

## Run (single shot, operator-run, no finger contact)

- Warm gate true (`0x42` count 2 uid 501, SKS `0x228`
  informational). Fresh tracking ACM context, operator password
  bound, final policy-1007 SATISFIED, mandatory cleanup.
- Session prep all status 0 (device-list, sensor-readiness,
  system-protected-config, xart-available, enabled-unlock).
- `0x03` v2 zero-group 68 B → start status **0** (first
  non-refusal of any enroll dispatch on this Air: -3 token-free,
  22 group-1, now 0).
- Cancelled immediately per start-only design: cancel 0,
  `identities_before` = `identities_after` = 2, preserved true.
- Post-window re-verify: `0x42`=2, repeat-equal true, gate
  complete. No state change of any kind.

## Side observation (production PAM, same session)

The `sudo` invocation carrying E1 exercised the installed PAM
stack live: ring finger rejected ("Failed to match fingerprint"),
index accepted, session authorized. Rejection + acceptance both
correct in production, password fallback untouched.

## Next steps (resume here)

1. **E4 full dance (staged separately, never combined here):**
   same zero-group start, then 8x empty `0x0e` with lift/place
   dance (~2 min), post-`4`, cancel. Natural candidate: the
   unenrolled **ring** finger — post-enroll ring-true plus
   index-still-true plus count 2→3 proves the new identity is
   real and distinct. Requires explicit new-identity ack
   (operator's own finger — Track A covers it), journaled
   outcome, and post-reboot proof before any further mutation.
2. **Do not:** re-run E1 (answered), combine the dance with any
   other variable, touch `0x40`/reset/`no_catacomb`/delete,
   default-param warm insmod.
