# Match-broker architecture: where the per-match password comes from (2026-09-20)

Branch: `research/mba91-aks-ep7`. **Paper only — no code, no live
windows, no state touched.** The sensor path is proven
(mute→verdict F1, polarity F2, selectivity N1/N2, routine R1). What
remains is the product gap: every proven match consumed a *fresh*
ACM tracking context bound with the operator's password at dispatch
time. A login flow must answer where that password comes from.

## Constraint inventory (all live-proven on this Air)

- Match requires: warm `0x42` identities + Sequoia prelude + opcode-4
  with 68 B options carrying flags `0x4009` + the 16 B ACM external
  form + counted blob (F1/F2/R1).
- The 16 B form comes from a fresh tracking context (`0x24`
  create → type-1 preflight → externalize → `verify-password-acm`
  bind → final policy-1007 SATISFIED), mandatorily cleaned up
  (`with_authorized_context`). Single-use semantics of a form across
  shots is **unknown** — every window used a fresh one by design.
- Keybag prerequisites: module (pinned minimal set) + load +
  operator unlock of both bags, all currently manual.
- Token-free opcode-4 (flags 0, 60 zero bytes) stayed mute in 6
  windows — but those predate the current keybag/authorization
  understanding, and unlocked-keybag state at the time is not
  cleanly documented. The variable is NOT cleanly closed.

## Options (ranked by falsifiability cost)

1. **K1 — unlocked-keybag token-free retest (one gated window,
  CHEAPEST, decisive).** With keybags confirmed unlocked (current
   machine state), run the exact Fork-A token-free shape
   (flags 0 + counted blob, finger present). Verdict emitted →
   the broker may not need per-match passwords at all (unlocked
   keybag suffices). Mute again → per-match password binding is
   structurally required; proceed to option 2. Either outcome is
   a verdict, not a fishing trip.
2. **PAM password capture (engineering).** If K1 mutes: capture the
   login/lock password via a PAM hook (proven pattern on the
   MBP16,2 track: password already flows to the keybag-unlock
   helper), mint a fresh authorized context per match inside a
   privileged broker holding `/dev/t2-acm`, wipe after. Reuses the
   existing caller/session/PolicyKit broker discipline
   (`docs/FPRINT_INTEGRATION.md`) — no new trust model, but a real
   daemon to build, plus lock-screen (user-session) caller plumbing
   distinct from the sudo path.
3. **Context/form caching (experiment, only if 2 looks costly).**
   Mint once per boot/login, reuse the context or cached 16 B form
   across matches. Blocked on unknown SEP-side lifetime and
   single-use semantics — needs its own staged experiment (back-
   to-back matches on one context, then spaced matches). Do not
   assume; measure.
4. **fprintd facade + PAM templates (last).** Only after the broker
   decision: expose verification through the standard ABI with the
   MBA91 broker underneath. Enrollment stays macOS-side until the
   cross-OS question is answered; Linux-native enroll is out of
   scope for the reader-working milestone.

## Decision tree

- K1 verdict → broker may be password-free at match time (keybag
  UX per boot is then the only auth work) → prototype broker
  without password plumbing, prove with repeated matches.
- K1 mute → per-match password binding required → design the
  PAM-capture broker (option 2), prototype, then facade.
- Either way, no installer/DKMS/facade work before the broker
  answer — it decides the architecture.

## Do-nots (unchanged)

No 74 traffic, no payload sprays, no enroll/load/reset/delete, no
default-param warm insmod (loader owns the pinned set), no
persistent password storage (process memory only, wiped after use —
same rule as the proven PAM hook).
