# C4/C4b verdict: bind works, fresh-bag password ops answer -5 (2026-09-20)

Branch: `research/mba91-aks-ep7`. All live gates disabled in source
(verified). Shapes/statuses/counts only — no passwords, no UUIDs.

## Verdict

**Bind succeeds, password ops refuse with SEP status -5.** The
native bag (C1-created, C3-exported) binds to scratch alias `-502`
cleanly (`status=0`, macOS `-501` untouched), but `unlock-keybag`,
`verify-password-only`, and `verify-password-acm` ALL answer `-5`
with the creation password. The credential was never established
in a form these paths accept — the bag needs their *activation*
ceremony (fresh-owner activation: mapping-committed bundles and
proofs), not more password attempts. No local decode for -5
exists; it is recorded as vocabulary, not diagnosed.

## Runs

- C4a (unlock-before-bind): bind skipped by order, unlock rc=1.
- C4b (bind-first reorder): bind `status=0`; unlock rc=1 again.
- `verify-password-only` on the bound handle: SEP `-5`.
- C4b (fresh ACM context + verify): SEP `-5` at password-binding,
  context cleaned. All pre-states intact; macOS bags, aliases,
  and the 3 SEP templates untouched throughout (post inventory
  3/3 repeat-equal).

## What this separates

- Creation/export/bind: PROVEN on MBA91 (C1/C3/C4-bind).
- Password-establish on a fresh bag: REFUSED (-5 ×3 paths).
  Their product flow never password-unlocks a fresh bag
  directly either — it runs a full activation subsystem
  (mapping bundles, owner proofs, replacement journals) first.
  That subsystem is the next paper mountain, sized in
  NATIVE_C4C5_DESIGN_2026-09-20.md and still open.

## Next steps (resume here)

1. Paper: map their activation sequence (provision → mapping-
   committed → fresh-owner activation proofs → runtime) onto
   MBA91 prerequisites without live dispatches.
2. No more password attempts against the fresh bag (answered
   thrice); no bind/unbind cycling on `-502` (leave it parked
   or rebind explicitly with a recorded pre-state if needed).
3. Do-nots unchanged; the C3 test file stays quarantined.
