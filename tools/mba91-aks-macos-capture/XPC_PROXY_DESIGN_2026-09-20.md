# macOS session-proxy design: genuine-daemon verdict relay (2026-09-20)

Branch: `research/mba91-aks-ep7`. **Paper only — no code, no live
windows, no state touched.** Decides whether H2 is worth engineering
after `SESSION_MECHANISM_SURVEY_2026-09-20.md`. Shapes and boundaries
only — no payloads, no keybags, no passwords.

## Starting position (do not re-litigate)

- S1–S5 + C3 + authorized-74 closed every anonymous-socket axis at
  258. The SEP gates 74 on calling-session identity our BridgeXPC
  socket cannot carry. No further Mesa-shape probe can change this.
- The missing session is almost certainly **above Mesa**
  (XPC/framework → keybag-bound session). There is no Mesa
  session-bind opcode to replay (`BRIDGEXPC_PATH.md` method table).
- Hard constraint from `enrollment_research/FINDINGS.md`: Apple
  private entitlements (`com.apple.private.biometrickit.allow-match`,
  `allow-enroll`, `allow-id-mgmt`, `applekeystored.*`,
  `applecredentialmanager.allow`) are enforced host-side against the
  opening Mach task and are **not serializable**. We cannot forge
  them, and we do not try (no SIP disable, no cache extraction,
  no entitlement spoofing — already ruled disproportionate).

## Design choice: drive the genuine daemon, never impersonate it

The proxy does **not** pretend to be `biometrickitd` on the wire
(S5 proved strings are not the gate anyway). Instead a macOS
operator agent asks the **genuine** `biometrickitd` — which already
owns a valid audit session, code identity, and keybag-bound server
session — to perform a normal match, then relays only the boolean
verdict to Linux. Linux never sees biometric data, templates, UUIDs,
or credential sets; the SEP/macOS boundary keeps those.

Concretely (staged, each gated separately):

- **Stage P0 — local-only proof (macOS only).** An operator-run agent
  in the logged-in session invokes the public match path (the same
  API family Screen Lock uses: `match:withOptions` with
  `BKOptionMatchForCredentialSet` + `MatchForUnlock=1`) and records
  only: match boolean, `getEnabledForUnlock` state, save-cluster
  occurrence. No relay, no Linux involvement. Success criterion: the
  agent's verdict agrees with Screen Lock unlocks on the same boot.
  This proves we can observe verdicts without touching private APIs.
- **Stage P1 — authenticated relay (macOS → Linux, one shot).**
  Only after P0: the agent transmits a bound, single-use verdict
  ticket to Linux over an authenticated channel (operator-paired
  keys, per-boot pairing, nonce + timestamp + Linux boot/generation
  binding, short expiry). Linux verifies ticket, binding, and
  freshness, then treats it as *one* authentication signal — never
  as persistent authority. Any replay, mismatch, or expiry fails
  closed. Raw biometric or identifier material never crosses.
- **Stage P2 — PAM integration.** Only after P1 proves clean over
  repeated trials with password fallback intact: a narrow PAM hook
  consumes a fresh ticket for the exact Linux session that requested
  it. Same caller/session/PolicyKit discipline as
  `docs/FPRINT_INTEGRATION.md` (unique sender, pidfd-backed process,
  active local session, bounded grant) applies to the *consuming*
  Linux session — the ticket does not bypass it, it only supplies
  the biometric factor.

## Why this shape (and not the alternatives)

- **Not a BridgeXPC MITM on the T2 link.** Interposing between
  `biometrickitd` and `bkremoted` would risk SEP/session state on
  the operator's only machine for zero additional science (working
  unlocks already prove the genuine path succeeds). Excluded.
- **Not entitlement forging or injection.** Any design requiring
  `com.apple.private.*` on our binary, task-port games, or SIP-off
  extraction is rejected at review — it breaks Track A proportionality
  and Lab Protocol scope.
- **Not a Linux-side replay.** There are no session bytes to replay:
  74 is empty on the working path and the session is server-side
  state, not a token. S2/S2b/S3 proved ordering/cancel/gap are not
  the session either.

## Open questions before P0

1. Which **public** API surface the agent uses (LocalAuthentication
   vs BiometricKit client) and its ScreenLock-session requirements
   (logged-in + unlocked keybag + ScreenLock context?).
2. Ticket channel and pairing UX that an operator will actually
   tolerate per boot without weakening to "always yes."
3. Whether the product goal (Linux unlock via Touch ID) justifies a
   permanent cross-OS relay at all, versus parking match and keeping
   Linux password + macOS Touch ID separate. This is a product call
   for Tim, not a technical inevitability.

## Gates and do-nots

- Each stage needs explicit operator go-ahead; P1/P2 additionally
  need the Lab Protocol due-diligence tick (consent, ownership,
  own-material, scope, private storage, warm-state understood).
- P1/P2 must keep password authentication working and keep a root
  shell during tests (same PAM discipline as the proven install).
- Do not: forge entitlements, disable SIP, extract the dyld cache,
  MITM the T2 link, ship biometric/identifier material across the
  relay, or grant persistent authority from one ticket.
- `fprintd --warm-verify` stays gated; this design does not create a
  Linux SEP verdict and must not be presented as one.
