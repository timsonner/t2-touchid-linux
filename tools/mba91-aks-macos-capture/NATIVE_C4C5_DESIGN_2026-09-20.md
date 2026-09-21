# C4/C5 design: bind + enroll-native under a scratch UID (2026-09-20)

Branch: `research/mba91-aks-ep7`. **Paper only — no code, no live
windows, no state touched.** The native loop closes here on paper;
each step stages separately live.

## Construction (ported from t2touch native provision)

Their provision binds password→ACM form→create→export→persist→
mapping, with the SAME Linux-chosen credential unlocking the new
bag afterwards. Our C1/C3 proved create→export→persist→reload on
MBA91; what remains is password-establish, alias bind, and a
native-UID enroll/match — all against a scratch identity that can
never touch the macOS bags or the 3 SEP templates.

## Scratch identity (blast-radius discipline)

- Alias `-502` (no configured user, no Catacomb, no templates).
  `-501` (macOS binding) is never repointed — reversibility by
  avoidance, not by repair.
- Bag: the C1-created native bag (reloaded fresh; handle varies
  per boot — always resolve live, never hardcode 8/9).
- Password: a NEW Linux-chosen test password, operator-typed at
  prompts, never stored. (Not the macOS password — the point is
  macOS-independence.)
- UID `502` for enroll/match scope: SEP namespace proven open
  tonight (`0x42`/`0x41`/`0x30` all status 0, empty-but-valid).

## C-series close-out

| ID | Shot | Gates | Prediction |
|---|---|---|---|
| C4 | Password-establish + unlock cycle on the native bag (unlock-keybag with the new password → status 0 establishes?) + `verify-password-acm` with a fresh context → policy-1007 SATISFIED against the native bag; then `set-system-keybag` bind to `-502`; reload file → UUID verify | warm SEP, keybag session, LIVE default-off + confirm, journal (private, counts/versions), NO `-501` repoint ever | unlock establishes + verifies (their flow says yes), or a new refusal vocabulary to mine |
| C5 | Authorized enroll dance (E4 shapes, zero-group 68 B) scoped to uid `502` with the native-bag ACM context + ring-finger touches → `0x42` for 502 goes 0→1; then token-free match → verdict | C4 green + E4 gates + new-identity ack | first macOS-free enrollment; failure here is SEParchitecture (account checks), not framing |

## Risks (stated plainly)

- C4 password-establish is the least-evidenced step: first-unlock
  semantics on a fresh bag are inferred from their flow, never
  observed on MBA91. Refusal is data, not damage (no templates
  in the scratch namespace).
- `-502` binding writes alias state — reversible by rebinding,
  but record the pre-state (alias readback) first anyway.
- Reboot evaporates live handles; the test `.kb` file + journal
  are the only durable artifacts until product wiring exists
  (explicitly out of scope here).

## Do-nots

No `-501` repoint, no macOS-bag operations, no 502-enroll before
C4 green, no product wiring, no KEK/file persistence beyond the
already proven C3 file (delete it before any product use).
