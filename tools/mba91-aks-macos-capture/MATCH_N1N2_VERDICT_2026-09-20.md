# N1/N2 verdict: selectivity proven, full discriminator matrix (2026-09-20)

Branch: `research/mba91-aks-ep7`. All live gates disabled in source.
Shapes/statuses/counts only — no payloads, no keybags, no passwords,
no identity UUIDs.

## Verdict

The authorized opcode-4 match path **discriminates truthfully**.
Enrolled fingers return terminal `match_result` verdicts with the
enrolled template present; a genuinely unenrolled finger returns a
terminal `match_result` without it. Selectivity gate closed.

## Matrix (all same F1 framing, policy-1007 live, `0x42`=2)

| Window | Finger presented | Enrolled? | `match_result` | `matched` |
|---|---|---|---|---|
| F1 | right index, normal placement | yes | seen (3268 B) | **false** (placement) |
| F2 | right index, careful flat hold | yes | seen (3268 B) | **true** |
| N1 | middle, believed unenrolled | **yes** (see note) | seen (3268 B) | **true** (correct) |
| N2 | right ring | no | seen (3268 B) | **false** |

N1 note: the operator's "unenrolled" finger turned out to be the
second macOS-enrolled identity (pointer + middle are the two
enrollments). The SEP returning `true` was correct behavior, not an
always-yes fault — confirmed by code audit of `summarize_event`
(`src/bridge-xpc-probe.py:106-141`): `matched` requires a 16-byte
enrolled UUID substring inside the 3268 B SEP event, which cannot
occur by chance. N2 with the genuinely unenrolled ring finger then
returned the expected `false`, completing the control honestly.

## State after all windows

- `cancel_status` 0 every window; `identities_preserved` true every
  window; post-series inventory `0x42`=2, global 2, reconciled true,
  repeat-equal true, SKS `0x208`, gate complete. No state damage
  across four authorized match windows + one HELO-spoof window.
- N1/N2 used the already-open F1 gate; no source changes for the
  controls. Gate re-disabled after each window (verified).

## What this closes and what is next

- Closed: mute-vs-verdict (F1), polarity-vs-placement (F2),
  selectivity (N1/N2). The MBA91 Touch ID sensor path is fully
  characterized as a truthful biometric discriminator under
  credential-set authorization.
- Retired: the 74 track (moot for verification) and the macOS
  session-proxy for *verification*.
- Next: repeatability across reboot (warm handoff preserves `0x42`;
  module/keybag bring-up still manual), then the match-broker
  product question (per-match password-bound context → PAM/daemon
  architecture), reusing the proven MBP16,2 broker discipline.
