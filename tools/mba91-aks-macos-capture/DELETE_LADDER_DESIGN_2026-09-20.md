# Delete ladder D-series design: identify ring, delete one, re-enroll (2026-09-20)

Branch: `research/mba91-aks-ep7`. **Paper only — no code, no live
windows, no state touched.** Ladder rung before any nuke talk.
Shapes/statuses/counts only.

## Problem

SEP holds 3 unlabeled 20 B records (uid + UUID). The ring must be
identified before any delete aims at it — a mis-targeted delete
kills a macOS print that Linux cannot re-enroll. Insertion order
(ring enrolled last) is a hypothesis, never evidence.

## Constructions (all recovered, none invented)

- Delete: `0x0D` v0/val0, data = the exact 20 B record, cap 0
  (`t2_identity_delete_bridge.py:85-91`). Outcome trusted only
  from stable SEP inventory, never the command status.
- Targeted match: token-free opcode-4 v1/val0, 68 B options
  (flags 0, uid, 60 zero) + counted blob with exactly ONE record.
  K1/K2 proved token-free verifies with unlocked bags; the blob
  count is the only variable changed.

## Series (in order, never combined)

| ID | Shot | Gates | Prediction |
|---|---|---|---|
| T1–T3 | Targeted 1-record match per 0x42 record (ring held each window, stop at first `matched:true`) | warm `0x42`==3 + repeat-equal, LIVE default-off + confirm, finger present, cancel always, post-`0x42`==3 required | exactly one record returns true (= ring); others terminal `false` |
| D1 | `0x0d` with the T-proven record, journaled intent + outcome (counts/UUID-hash-free: record index only), post-`0x42` must equal 2 with that exact record absent | same + T-proof recorded + explicit delete ack | 3→2, survivor set = the other two records |
| E4r | Re-enroll ring via proven E4 dance → 3 again | E4 gates as proven | full cycle closed: 3→(T)→2→(D1)→3 |

## Stopping rules

- T: any window with non-0 start, any identity change, or two+
  records returning true → halt (records are not what we think).
- D1: any dispatch transport error, any post state other than
  exactly-2-minus-target → halt all live work, reconcile, never
  replay. A D1 that removes the WRONG record is a macOS-print
  kill — this is why T runs first and D1 never aims blind.
- No `0x40`/reset/`no_catacomb`, no default-param warm insmod,
  fresh ACM-free windows (token-free needs no password; keybags
  must simply be unlocked).

## Recommendation

Stage the targeted-match script (no password, no ACM — K2 says
unlocked bags suffice), run T-windows with the ring held, then
stage D1 only against a T-proven record.
