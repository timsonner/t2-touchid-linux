# K2 verdict: unlocked keybags suffice, priming dead (2026-09-20)

Branch: `research/mba91-aks-ep7`. No gates to disable (standard
probe only, no source changes). Shapes/statuses/counts only — no
payloads, no keybags, no passwords, no identity UUIDs.

## Verdict

**Token-free match verifies on a fresh boot with unlocked keybags
and zero prior authorized windows.** K2 ran first this boot — after
only the loader, operator unlock, and fingerless baseline — and
returned a terminal 3268 B `match_result` with the enrolled template
present (`matched: true`) against the enrolled right index. The K1
confound is resolved: the variable is keybag state, not matcher
priming. Per-match password binding is **not structurally required**;
the PAM-capture broker direction is retired. The remaining auth work
is per-boot keybag UX, not per-match password plumbing.

## Run (single window, fresh boot, enrolled finger present)

1. Clean slate: no module, no `/dev/t2-*`, no `/run`, same kernel.
2. Loader `--bring-up`: exit 0, 3 nodes, keybag session 1/1/`-501`.
3. Operator unlock of both bags: `status=0` each.
4. Fingerless baseline: port `49188`, `0x42`=2, repeat-equal true,
   selftest PASS. No ACM context, no password bind, no authorized
   traffic of any kind before K2.
5. K2 (`bridge-xpc-probe.py --initialize --identity-list
   --match-seconds 30 --stop-on-match-result`, flags 0 + counted
   blob): start status 0, cancel 0, 29 events — `status` ordinals
   53/80/73(3242 B)/64/90/63/55/72/95/91, two `sks_lock_state`,
   `statistics` throughout, terminal `match_result` 3268 B
   (`0xe3ff8002`, v2) `matched: true`, plus the trailing 36 B
   `status` ordinal-74 event seen in every verdict window.
6. Post-window: `0x42`=2, repeat-equal true, SKS `0x228`
   (`552`), gate complete. No state damage.

## Joint K-series reading

| Window | Boot state before | Framing | Finger | Result |
|---|---|---|---|---|
| Sept Fork-A x6 | EP7 parked, keybags locked | token-free | enrolled, incl. 60 s hold | mute, no verdict |
| K1 | unlocked bags + prior authorized match | token-free | enrolled | verdict, `true` |
| K2 | unlocked bags, NO prior match | token-free | enrolled | verdict, `true` |

K2 minus K1 equals the priming hypothesis, now dead. September
minus K2 equals the keybag state, now the proven lever. The
September mute is fully explained: locked keybags, not a dead
sensor, wrong opcode, or missing token.

## Next steps (resume here)

1. Broker without password plumbing: per-boot keybag UX (load +
   operator unlock via login-password hook or credential, same
   rules as the proven track) + a match broker holding no
   passwords. Prototype against repeated token-free matches.
2. Facade/PAM work reuses the proven broker discipline when the
   broker prototype repeats cleanly.
3. Do-nots unchanged: 74, sprays, enroll/load/reset/delete,
   default-param warm insmod.
