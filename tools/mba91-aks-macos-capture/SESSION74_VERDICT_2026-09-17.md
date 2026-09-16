# Session-74 verdict: the gate is session-identity (2026-09-17)

Branch: `research/mba91-aks-ep7`. All live gates disabled in source.
Shapes/statuses/counts only — no payloads, no keybags, no passwords.

## Verdict

Mesa-74 refuses at dispatch (258) regardless of wire bytes or ambient
authorization. The SEP gates 74 on **calling-session identity** — our
anonymous BridgeXPC socket is never `biometrickitd`'s keybag-bound
session — not on traffic shape, ordering, or password context.
Further Mesa-shape windows are closed; do not re-probe them.

## Closed matrix (every cell a gated single shot, warm-preserved)

| Axis | Window | Result |
|---|---|---|
| Fork-A 68 B / unlock-flags / empty framing | 7, 8, 9 | 258 |
| Wire version gate (C3, ver 2) | C3 | `0xe00002c2` |
| Credential-in-payload (C4/C1/C2) | Fork B mine | dead: 74 always empty (3 confirmations) |
| Capture-exact framing, no auth (S1) | S1 | 258 — 48 shape benign |
| Full cluster, no separation, no auth (S2) | S2 | nil halt — open `4` breaks 74 dispatch |
| Full cluster + cancel/drain/gap, no auth (S2b) | S2b | clean 258 — session-shape closed |
| No-`4` session + corrected order, no auth (S3) | S3 | 258 — prelude ruled out entirely |
| **No-`4` session + corrected order + live policy-1007 auth (S4)** | S4 | **258 — credential axis exhausted** |

S4 detail (operator-run, finger down): `verify-password-acm` status 0,
warm gate true (`0x42`=2, SKS `0x11`), all eight session steps status 0
(`46→48→46`, 3 s gap, `48→84→39→12→84` corrected order), empty 74 →
258, cancel 0, ACM context cleaned by construction. Early S4 attempts
died on a staging `NameError` (fixed) before dispatching — only the
final run counts; 74 was dispatched exactly once under auth.

## Standing state (this boot, verified after S4)

- `0x42` count 2 (uid 501), free 1/5, `full_snapshot_repeat_equal` true.
- SKS coloring drift (informational, never a gate):
  `0x10 → 0x810 → 0x239 → 0x11 → 0x208` across warm sessions.
- Minimal module still loaded (warm-surviving set only); `/dev/t2-acm`
  + `/dev/t2-aks` present. Both vanish on reboot, as does
  `/run/t2-touchid/keybag.env` — S4-class work needs the full runbook
  again (insmod minimal set → keybag load → operator password unlock).
- macOS capture daemon still installed (per UNLOCK_VERDICTS pending);
  teardown when Linux side calls it.

## Next steps (resume here)

1. **Session-establishment research (no live windows).** What does
   `biometrickitd` speak that we don't? Audit targets: HELO fields
   (`ProcessName`/`OSBuild` gating?), client-version negotiation,
   service-open variants, any Mesa opcode resembling session-bind.
   macOS side (private only): how the framework's
   `BKOptionMatchForCredentialSet` + `MatchForUnlock=1` reaches the
   SEP — if it never becomes Mesa bytes, Linux needs a session
   mechanism, not a payload.
2. **Fork-A mute revisit, credential-set lens.** Opcode 4 is the only
   path that OPENS (status 0, six mute windows). Open question: does
   the 68 B options block carry unlock binding in its 60 reserved
   bytes? Weak rationale (macOS sends zero opcode-4) — design-only,
   no live dispatch until (1) says something.
3. **Do not:** more 74 framings, payload sprays, opcode-8/82 hunts
   (dead), prelude variants (ruled out), default-param insmod on warm
   SEP (journal-proven killer).
4. `fprintd --warm-verify` stays gated on a first probe verdict.

## Resume checklist (fingerless, ~1 min)

Port rediscover (dynamic; was `49184`) → `--initialize
--full-inventory` (`0x42`=2, repeat `True`) → `session-selftest.py`
PASS. Any deviation halts live work before windows.
