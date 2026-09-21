# D2 verdict: single delete confirmed, survivors exact (2026-09-20)

Branch: `research/mba91-aks-ep7`. All live gates disabled in source
(verified). Shapes/statuses/counts only — no UUIDs, no payloads.

## Verdict

**First live single-identity deletion on MBA91: confirmed.** The
version axis was the entire wall — v0 refused `0xe00002c2` (D1),
v1 dispatched 0 with zero events (D2). Post-state is exactly the
two pre-existing records, byte-identical; the ring no longer
matches while the index verifies. The macOS prints were never in
the blast radius and prove intact.

## Runs

- D1 (`--mesa-version 0`): `0xe00002c2`, 0 events, 3→3. Halted
  per design, state triple-verified.
- D2 (`--mesa-version 1`): dispatch **0**, 0 events, cancel 0,
  `identities_before` 3 → `identities_after` 2,
  `survivors_match_expected: true`, `outcome: deleted-confirmed`.
  Journal (index + counts only) in operator-private storage.
- Attribution via installed daemon (no passwords): ring →
  `verify-no-match` exit 1 (the deleted identity was ring);
  index → `verify-match` exit 0 (survivor intact).
- Post: per-user 2, global 2, reconciled true, repeat-equal true,
  free 1/5, SKS `0x208`, gates complete.

## T+D joint reading (delete ladder, closed)

| Step | Result |
|---|---|
| T0/T1 (records 0/1, ring held, valid 0x4000 framing) | terminal `false` |
| T2 (record 2, ring held) | terminal `true` — ring's record |
| D1 (v0) | `0xe00002c2`, unchanged |
| D2 (v1) | 0, 3→2 exact survivors |
| ring post-delete | no-match (was the target) |
| index post-delete | match (untouched survivor) |

The never-live-tested broker version (v0) was wrong for this
build; v1 is the delete wire version here. Same lesson shape as
the enroll version question (capture said v2; we obeyed capture).

## Next steps (resume here)

1. **E4r re-enroll (proven dance):** ring again → expect 3 with
   ring-true. Closes the full lifecycle loop 2→3→2→3 and returns
   capacity to the banked E4 state.
2. The nuke path is now *technically* unblocked (single delete
   works) but still a product decision, not a research need:
   macOS prints would need re-enrollment in macOS, and empty-SEP
   authorized start remains the one untested dispatch on this
   machine.
3. Do-nots unchanged.
