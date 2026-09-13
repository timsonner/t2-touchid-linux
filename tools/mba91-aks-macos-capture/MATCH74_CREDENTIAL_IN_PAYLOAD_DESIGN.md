# 74 credential-in-payload — design only (no code, no live dispatch)

Status: **review-only design**. Nothing here has been built or sent. Any
candidate that graduates needs its own disabled-by-default probe, one
single-shot window each, with fresh ACM context + mandatory cleanup per
shot. This note exists to rank the idea honestly — including the reasons
it may be wrong — before anyone spends live windows on it.

## What is already proven (do not re-probe)

| Window | 74 framing | Auth context | Prelude | Result |
| --- | --- | --- | --- | --- |
| 7 | Fork-A 68 B + counted blob, v1/val0 | none | clean Sequoia order, all 0 | **258** |
| 8 | same + unlock flags 1 | none | clean, all 0 | **258** |
| 9 (window-9) | **empty** (capture-exact v1/val0/0 B) | none | all 0 | **258** |
| authorized | **empty** | fresh tracking ACM context, `verify-password-acm` 0, policy 1007 SATISFIED live at dispatch | all 0 (`48`→1 B, `84`→83 B, `39`→4 B, `84`→83 B, `12`→nil), warm gate true (`0x42`=2, SKS `0x11`) | **258** |

Conclusion so far: the 74 gate is **neither input-shape nor ambient
password-context**. Every attempt used wire ver 1, val 0
(`biometric_command` defaults); 258 is a dispatch-level refusal.

## The capture constraint (read before designing payloads)

Working Sequoia 74 is **always empty**: 3× `74` v1/0/0 B in the
unlock-minute mine, and match traffic on 74 with no input in the
09-06 re-mine. **No observed macOS 74 carries inline credential bytes.**
Any credential-in-payload candidate therefore has **zero capture
support** — it is our construction, not a replay. If Fork B (Sequoia
mine, method A) confirms empty-74-working, this whole line should be
killed in favor of session-binding hypotheses (below).

## Why ambient auth may never work: session analysis

Our BridgeXPC session differs from `biometrickitd`'s session in at
least four ways no payload can paper over:

1. **Server-side keybag session.** `biometrickitd` talks to a daemon
   holding the unlocked keybag; our socket is anonymous. The SEP may
   gate 74 on the *calling session* having performed an authorization
   dance, not on SEP-global unlock state (which we proved: SEP-global
   unlock + satisfied policy still 258).
2. **Prior token dance.** A working enroll session performs `0x03`
   (68 B token) + `0x0e` ×8 before anything match-like. Our 74 session
   never presents any token. If 74 requires a session that previously
   presented a valid token, only a token-bearing call in-session helps —
   and the token contents remain unrecovered.
3. **Identity-records fetch.** macOS sessions issue opcode 8
   (`GetIdentityRecords`) and device-list 82/84 pairing; our match
   sessions issue `0x42` (per-user list) but never opcode 8. A
   session-armed-by-8 hypothesis is sequence, not credential — Fork B
   decides it.
4. **Transport split.** Our ACM authorization lives on `/dev/t2-acm`
   (kernel mailbox); 74 rides BridgeXPC/NCM (userspace). There is no
   evidence the SEP links these two contexts. The authorized window's
   258 is consistent with "two unrelated sessions."

## Candidate matrix (if Fork B leaves the door open)

All candidates: one shot each, Sequoia prelude first (abort on
deviation), cancel always, post-`0x42`=2 required, fresh ACM context +
mandatory cleanup per shot where an external form is used. Order is by
ascending cost.

| ID | Payload on 74 | Wire | Needs ACM/password | Rationale | Prediction |
| --- | --- | --- | --- | --- | --- |
| C3 | empty (`b""`) | **ver 2**, val 0 | no | version gate, not payload gate — the one axis never tried | ~~258 or `0xe00002c2`; either is informative~~ → **CLOSED 2026-09-13: `0xe00002c2`** (SEP knows 74 at ver 1 only) |
| C4 | bare 16 B external form | v1, val 0 | yes (fresh context) | minimal credential; tests "SEP reads a raw form on 74" | 258 (likely; no container typing) |
| C1 | 68 B enroll-token clone (`IIII` flags/uid/using_token=1/tokenlen=16 + 16 B form + 16 zero + group u32 + 16 zero) | v1 then (if 258) v2 — two shots max, in that order | yes (fresh context each) | SEP may accept the same credential container on 74 | 258 (container is enroll-typed) or 22; 0 would be a major result |
| C2 | Fork-A match framing (68 B options + counted blob) + 16 B form appended | v1, val 0 | yes (fresh context) | match-typed container plus proof | unknown; weakest rationale, last resort |

Explicitly **excluded**: bare-uid/token-free `0x03`-style 52 B shapes
(authoring bug, already 22), any catacomb/save/reset/delete traffic,
reusing one external form across shots (single-use semantics unknown —
fresh context per shot removes the question).

## Stopping rules (bind any future probe)

- Any start status other than 258/22 → halt, analyze, no further shots.
- Any emitted service events on a nonzero start → halt (violates the
  status-authoritative assumption; reconcile before continuing).
- Post-`0x42` != 2 exact → halt all live work, reconcile.
- One candidate per verified-stable baseline; never combine an
  untested candidate with any other change (module params, keybag
  session, SKS drift).

## Recommendation

Fork B first: if the mine shows empty-74-working, close this file
(superseded — the answer is session-binding, mine opcode 8 / 82-84
sequence next). If the mine is inconclusive or shows non-empty 74,
graduate C3 alone (cheapest, no credential), then stop and re-rank
before touching C4/C1/C2.
