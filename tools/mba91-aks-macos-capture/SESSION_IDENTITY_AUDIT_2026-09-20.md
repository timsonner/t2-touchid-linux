# Session-identity audit: what binds 74 to biometrickitd (2026-09-20)

Branch: `research/mba91-aks-ep7`. Offline only — no live windows, no
state touched. Companion to `SESSION74_VERDICT_2026-09-17.md` step 1.

## Wire facts (ours, `src/t2_bridge_wire.py:55`)

HELO `{MaxSupportedProtocolVersion:1, OSBuild:"Linux",
ProcessName:"t2-touchid-probe", BridgeXPCVersion:<peer>}`, then
`[0]` getBridgeVersion → `[10,v]` setClientVersion → `[1]`
service-open (expects `[0, True]`) → method-3 Mesa. Methods ever sent:
0/1/3/5/10/11. Full table 0–12 (`BRIDGEXPC_PATH.md`): 2/4/6/7/8/12 are
host-info/time/cal — **no session-bind method exists**. Within-protocol,
the HELO JSON is the only per-connection identity bkremoted receives.

## macOS evidence (binary strings + captures, shapes only)

- `BKClientProcessName/BundleIdentifier/Type` are XPC-side
  (client→daemon), not BridgeXPC HELO.
- `BKOptionMatchForCredentialSet` is a real framework option —
  matches the 16 B credential-set + `MatchForUnlock=1` seen at
  `match:withOptions` in the 2026-09-16 unlock (credential binding
  lives above Mesa; Mesa-74 stays empty).
- biometrickitd builds its HELO from `_clientName` /
  `_commProtocolVersion` / `getOSVersion` — exact JSON keys live in
  the BridgeXPC client inside the SIP-hidden dyld cache (unreached).
- macOS HELO bytes never captured: en3 pcap dry twice (0 packets,
  pktap blind to NCM here — 2026-09-07 and 2026-09-20), os_log never
  prints HELO JSON, Sep-07 sanitized transcripts empty.
- 2026-09-20 unlock re-confirmed canonical verdict
  (`48×4/84×2/39×3/12×1/74×1/4×1/46×4` + save cluster, 74 empty).

## Hypotheses, ranked

- **H1 HELO-identity (spoofable):** bkremoted gates 74 on HELO
  `ProcessName`/`OSBuild`. Weak rationale (self-reported strings as a
  security gate) but cheap and falsifiable.
- **H2 kernel/XPC identity (architectural):** bkremoted checks
  something TCP cannot carry (audit token / code identity / keybag
  session in kernel state). S4 already proved ambient password-context
  is insufficient. If H1 falsifies, H2 stands and Linux needs a
  session mechanism (e.g. macOS-side XPC proxy), not wire bytes.

## S5 proposal (STAGED — needs operator auth, Linux side, one window)

Rationale: H1's only unknown is macOS's exact HELO bytes, so probe
value-swaps on our known keys (keys preserved, values macOS-faithful:
`ProcessName` → `biometrickitd`, `OSBuild` → `24G830`).

- Gates (same as S1): warm `0x42`=2 + `repeat_equal` pre-verified,
  single 74 dispatch, `LIVE` flag default-off + `--confirm-live`.
- Body: swapped HELO → standard init → S1 capture-exact framing
  (`48→84→39→84→12→74`, all v1/val0, empty 74) → cancel →
  post-`0x42`==2 required.
- Prediction: 258 either way. Success (non-258 verdict path) means H1
  lives and unlocks the track; 258 closes H1 and promotes H2.
- Halt rules: any 74 start status other than 258/22 halts with no
  further shots; never combined with other stages.

## Do not

More 74 framings, payload sprays, 8/82 hunts, prelude variants,
default-param insmod on warm SEP, SIP-disabled cache extraction for
HELO keys (invasive, disproportionate — S5 falsifies H1 without it).
