# C5 verdict: enroll requires a provisioned UID, framing can't overcome it (2026-09-20)

Branch: `research/mba91-aks-ep7`. C5 gate disabled (verified).
Shapes/statuses/counts only. No finger contact occurred (correct —
refusal preceded the dance by design).

## Verdict

** scratch-UID enroll refused `22` with correct framing and live
policy.** Zero-group 68 B + policy-1007 SATISFIED + green prep for
uid 502 (empty namespace, confirmed) → `enroll did not start:
status=22`. Same `22` as the old group-1 refusals, now with every
known variable corrected — isolating the one that remains: the
SEP enroll path gates on a **provisioned account** (their
`isValidUser` + existing Catacomb component load, per FINDINGS),
and 502 has neither. The UID-native middle ground is dead without
provisioning first.

## Runs

- C5a: blind wrapper failure (message swallowed by context
  cleanup) — infra lesson re-learned, diagnostic print added.
- C5b: `consumer failed: enroll did not start: status=22`.
  Post: 501 = 60 B (3 records intact), 502 empty. Zero state
  change anywhere.
- (Diagnostic fix committed alongside: consumer errors print
  before the cleanup wrapper re-raises.)

## What this decides

- Enroll (unlike match) is account-gated SEP-side. Match reads
  records; enroll mints into a user namespace that must exist.
- Native enroll therefore requires the provisioning ceremony
  (account UUID + bag + mapping — the C4-activation track),
  not better framing. No further enroll-shape variants can pass:
  the matrix is E1(open) → E4/E4r2(501-verified) → C5(502-gated).
- 501-enroll remains fully working (E4r2 + post-reboot proof);
  capacity full in any case.

## Next steps

1. Activation paper → staged ceremony against scratch handles
   (the `-5` wall is the same gate from the other side).
2. Do-nots unchanged; no 502 retries (answered twice over).
