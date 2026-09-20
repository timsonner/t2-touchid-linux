# S5 verdict: HELO-identity closed, session mechanism stands (2026-09-20)

Branch: `research/mba91-aks-ep7`. All live gates disabled in source.
Shapes/statuses/counts only — no payloads, no keybags, no passwords.

## Verdict

S5 swapped HELO values only (`ProcessName` → `biometrickitd`,
`OSBuild` → `24G830`, keys preserved) → standard init → S1
capture-exact framing (`48→84→39→84→12→74`, all v1/val0, empty 74)
→ cancel. Prelude all status 0, empty 74 → **258**, cancel 0,
`0x42=2` preserved. Identical to S1 with stock HELO.

H1 (HELO-identity, spoofable) is **closed**. H2 stands: the SEP gates
74 on calling-session identity our anonymous BridgeXPC socket cannot
carry (audit token / code identity / keybag session in kernel state),
not on wire bytes. Linux needs a session mechanism (e.g. macOS-side
XPC proxy), not further Mesa framings.

## Run (single shot, operator-authorized, fingerless)

- Warm gate true (`0x42` count 2 uid 501, SKS `0x208` informational),
  `full_snapshot_repeat_equal` true pre-verified + selftest PASS.
- `helo_sent`: `biometrickitd` / `24G830`. Peer HELO unchanged
  (`bkremoted` / BridgeXPC 39 / `23P6068`).
- Prelude: `48`-empty → 1 B, `84` → 83 B, `39` → 4 B, `84` → 83 B,
  `12` → nil, all status 0.
- `match_start_status`: 258. `match_result_seen`: false.
  `cancel_status`: 0. `identities_preserved`: true.
- Post-window re-verify: `0x42`=2, global 2, reconciled true,
  repeat_equal true, max 5 / free 1, SKS `520`, gate complete.

## Closed matrix (additive to SESSION74_VERDICT_2026-09-17)

| Axis | Window | Result |
|---|---|---|
| S1–S4 + C3 (shape / version / credential-in-payload / ambient auth) | prior | 258 / `0xe00002c2`, all closed |
| **S5 HELO value-swap (H1)** | S5 | **258 — H1 closed** |

## Next steps (resume here)

1. **No further live Mesa-74 windows.** Framing, ordering, version,
   payload, ambient-auth, and HELO axes are all exhausted.
2. **Session-establishment research only (offline, design-only):**
   what `biometrickitd` speaks that a TCP socket cannot — audit token,
   code identity, keybag session. If it never becomes Mesa bytes,
   the track needs a macOS-side session proxy, not wire bytes.
3. **Fork-A mute revisit stays design-only**, credential-set lens, no
   live dispatch until (2) says something.
4. **Do not:** more 74 framings, payload sprays, opcode-8/82 hunts,
   prelude variants, default-param insmod on warm SEP.
5. `fprintd --warm-verify` stays gated on a first probe verdict
   (none exists on this Air).
