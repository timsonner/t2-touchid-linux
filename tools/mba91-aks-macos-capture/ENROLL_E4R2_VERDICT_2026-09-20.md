# E4r2 verdict: variety enrolls, lifecycle loop closed (2026-09-20)

Branch: `research/mba91-aks-ep7`. E4 gate disabled (verified).
Shapes/statuses/counts only.

## Verdict

**Variety hypothesis confirmed: 2→3 with ring attributed.** Same
finger, same framing, same session shape as the refused E4r — only
the dance varied (center/tip/edges rotated, macOS-enroll rhythm).
The template engine mints on coverage, not on protocol completion.
Full delete-ladder lifecycle now reads 2→3 (E4) →2 (D2) →2-refused
(E4r) →3 (E4r2), all with state proofs at every step.

## Runs

- E4r2 dance: policy-1007 live, prep 5/5, dispatch 0, 8/8
  continues status 0 (1 event each — note: NO 3-event burst this
  time, so the burst is correlative, not required), cancel 0,
  `identities_before` 2 → `identities_after` 3,
  `outcome: enrolled-pending-reboot-proof`.
- Post: per-user 3, global 3, reconciled true, repeat-equal true,
  free 0/5, SKS `0x208`.
- Attribution (daemon, no passwords): ring → `verify-match`
  exit 0. The newcomer is the ring finger again.

## Standing state

Identical to the banked E4 state: 3 enrolled (index, middle, ring),
all verifying, capacity full. The pending item is the same as
after E4: post-reboot proof of this exact set (stability is
expected — E4's set survived — but proof is proof).
