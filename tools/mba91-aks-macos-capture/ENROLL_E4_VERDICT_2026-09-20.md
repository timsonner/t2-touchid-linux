# E4 verdict: Linux enrollment accepted, ring attributed (2026-09-20)

Branch: `research/mba91-aks-ep7`. All live gates disabled in source
(verified). Shapes/statuses/counts only — no payloads, no keybags,
no passwords, no identity UUIDs.

## Verdict

**First Linux-native Touch ID enrollment on MacBookAir9,1.** The
zero-group `0x03` v2 start opened, all 8 empty `0x0e` continues
returned status 0 with enroll-progress events, cancel was clean,
and SEP went 2→3 reconciled with capacity now full. The new
identity attributes to the ring finger (proven-unenrolled before):
ring returns `verify-match` through the installed daemon; a first
sloppy hold returned `verify-no-match`, a careful hold `verify-match`
— placement decides again, exactly as F1 established.

## Runs

E4 dance (operator-run, ring finger, ~2 min): policy-1007 live,
prep 5/5 status 0, dispatch 0, continues 8/8 status 0 (1 event
each, 3 on #5), post-`4` omitted by default, cancel 0,
`identities_before` 2 → `identities_after` 3,
`outcome: enrolled-pending-reboot-proof`. Post-window inventory:
per-user 3, global 3, reconciled true, repeat-equal true, free
0/5, SKS `0x208`, gate complete.

Attribution (installed `fprintd` daemon, no passwords involved):
ring careful hold → `verify-match` exit 0; ring sloppy hold →
`verify-no-match` exit 1. Both terminal verdicts, both correct
under placement semantics.

## Design corrections made live

- Continues MUST NOT halt on service events: post-start `0x0e`
  windows carry enroll-progress chatter (the September zero-event
  reads were start-less sessions). Halt only on non-0 dispatch.
- The E1/E4 consumer now surfaces failing detail in its errors
  instead of failing blind behind the context-cleanup message.

## Next steps (resume here)

1. **Post-reboot proof (required before any further mutation):**
   fresh boot → loader → unlock → stable `0x42`==3 reconciled →
   ring `verify-match` + index `verify-match`. Capacity is FULL
   (free 0) — no further enrollment is possible regardless.
2. **Do not:** enroll again (no room; refused or worse),
   re-run E4, touch `0x40`/reset/`no_catacomb`/delete,
   default-param warm insmod.
3. Cross-OS question now live: what a macOS boot does with a
   Linux-enrolled identity (on the proven track, macOS reconciled
   SEP back to its own Catacomb and dropped the Linux identity).
   Do NOT boot macOS until the Linux-side proof in (1) is banked.
