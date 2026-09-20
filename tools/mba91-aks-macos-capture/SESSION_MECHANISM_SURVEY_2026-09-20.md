# Session-mechanism survey: what TCP cannot carry (2026-09-20)

Branch: `research/mba91-aks-ep7`. Offline only — no live windows, no
state touched. Follows `SESSION_S5_VERDICT_2026-09-20.md` (H1 closed,
H2 stands). Shapes/statuses/counts only.

## 1. Wire identity surface (what we control — all exhausted)

- HELO JSON is the only per-connection identity we send
  (`src/t2_bridge_wire.py:55`): `MaxSupportedProtocolVersion`,
  `OSBuild`, `BridgeXPCVersion`, `ProcessName`. Self-reported strings.
  S5 value-swap (`biometrickitd`/`24G830`) → still 258. H1 closed.
- Init (`[0]` → `(0,3)`, `[10,min(peer,2)]` → `[0]`, `[1]` →
  `[0,True]`) negotiates versions and opens service. Method table 0–12
  (`BRIDGEXPC_PATH.md`): 2/4/6/7/8/12 are host-info/ioreg/time/cal —
  **no session-bind method exists**. Service-open takes no identity
  args; no variant can mint a server-side session.
- Mesa-74 on the working path is always empty: 3× empty in the
  unlock-minute mine, zero non-empty in 8964 lines
  (`MATCH74_SESSION_BINDING_2026-09-13.md`). Version axis dead
  (ver 2 → `0xe00002c2`). There is no payload left to try.
- Session-shape hypotheses dead: opcode 8 absent in unlock minutes;
  82 absent near unlock; `4`/68 B present in prelude but not mandatory
  (00:00/00:07 lack it); S2 showed an open-`4` session breaks 74
  dispatch (nil halt), S2b cancel-separated still 258, S3 no-`4`
  still 258.
- Fork-A opcode-4 opens (status 0) but stays mute: no `match_result`
  in 6 windows incl. calibrated + 60 s hold. macOS sends zero
  opcode-4 on unlock — 4 is not the verdict path.

## 2. Binding above Mesa (where the gate lives)

- Framework layer: `match:withOptions` carries 16 B
  `BKOptionMatchForCredentialSet` + `MatchForUnlock=1`
  (`UNLOCK_VERDICTS_2026-09-16.md`). Credential binding lives above
  Mesa; Mesa-74 stays empty. `BKClientProcessName/BundleIdentifier/Type`
  are XPC-side, not BridgeXPC HELO.
- ACM/endpoint-10 is alive; tracking `0x24` vs legacy `0x01`
  create, policy 1007 SATISFIED reachable via operator-password
  `verify-password-acm`. S4 proved ambient auth insufficient
  (258 with policy live, exact session). Transport split matters:
  ACM auth rides `/dev/t2-acm` (mailbox) while 74 rides
  BridgeXPC/NCM — no evidence the SEP links the two contexts.
- Backend credential selection is real but not a 74 payload:
  `_findValidCredential` requires credential SUID == credential-set
  SUID (+ freshness/use-count); enrollment writes `0x0100` flags.
  Binding is enforced inside credential resolution, not carried
  in 74 args.
- Host policy boundary (from `enrollment_research/FINDINGS.md`):
  applekeystored derives sid/suid from `xpc_connection_get_asid/euid`
  + audit-token copy; coreauthd `ContextManager` keeps a live map
  (`registerExternalizedContext`/`findContextForExternalizedContext`)
  and recovery carries PID/UID/audit-session/entitlement-check;
  ACM user-client checks `com.apple.private.applecredentialmanager.allow`
  per open, appends only the numeric UID to create `0x01`/`0x24`.
  Task/audit/entitlement are **not serialized to SEP**. Linux must
  replace that boundary with a trusted broker (root + PolicyKit +
  session binding + exact-UID context create) — proven pattern on
  the enroll track, but the match-verdict session is still missing.
- SKS coloring (`0x10/0x11/0x208/0x209/0x239/0x810`) is session
  coloring, never a gate. `0x42`=2 + `repeat_equal` is the warm
  baseline, not the session.

## 3. H2 proxy options (ranked, design-only)

1. **macOS-side XPC proxy.** A macOS helper/daemon with a genuine
   audit session speaks the above-Mesa path (XPC → keybag-bound
   session) and relays Linux intent. Highest fidelity; needs macOS
   code + entitlement story, SIP/dyld-cache constraints respected,
   keybag-unlocked session still required. Only option that addresses
   the actual gate.
2. **Same-session auth dance.** Perform the (unknown) session-arming
   dance on the exact socket that later sends 74. Blocked: no Mesa
   session-bind opcode exists, so the dance is almost certainly
   above Mesa (XPC/framework) — not replayable as Mesa bytes.
3. **Fork-A credential-set lens.** Ask whether the 68 B options
   block's 60 reserved bytes carry unlock binding. Weak rationale
   (macOS sends zero opcode-4); design-only, no live dispatch
   until (1)/(2) says something.
4. **Park match, work the proven track.** MBP16,2 fprint lifecycle
   (ROADMAP §10) and MBA91 cold-restore/enroll policy are
   independent of the 74 verdict. Legitimate default.

## 4. Falsifiability + boundaries

- H2 is falsified only by a non-258 from a genuine
  session-mechanism demonstration. No further Mesa-shape probe can
  falsify it — that matrix is closed (S1–S5 + C3 + authorized-74).
- Track A boundaries hold: single MBA91, operator material only,
  A/B/C scope, no SIP-disabled cache extraction, no default-param
  warm insmod, no payload sprays, no new attack surface without
  fresh consent (`docs/LAB_PROTOCOL.md`).
- `fprintd --warm-verify` stays gated on a first probe verdict.
