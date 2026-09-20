# R1 verdict: repeatability across reboot (2026-09-20)

Branch: `research/mba91-aks-ep7`. All live gates disabled in source.
Shapes/statuses/counts only — no payloads, no keybags, no passwords,
no identity UUIDs.

## Verdict

The authorized match path is **routine, not a one-boot fluke**.
After a full Linux reboot: the safe loader re-established the warm
session on first try, the fingerless baseline came back green, and
the same F1 framing returned `matched: true` on the enrolled right
index. Every stage of the bring-up is now a documented, repeatable
procedure instead of a hand-typed expedition.

## Sequence (post-reboot, in order)

1. **Clean slate confirmed:** module unloaded, `/dev/t2-*` absent,
   `/run/t2-touchid` absent, same kernel
   (`7.1.8-arch1-Watanare-T2-2-t2`), repo at `a762e09`, tree clean.
2. **Loader first run** (`warm-bringup-mba91.sh --bring-up`): insmod
   with pinned params, survived past the 9 s death mark, all three
   nodes present, keybag loaded (handle 1), session file staged
   (1/1/`-501`). Exit 0, no deviations.
3. **Operator unlock:** both bags `status=0` via terminal prompts.
4. **Baseline:** same dynamic port (`49188`), `0x42`=2, global 2,
   reconciled true, repeat-equal true, selftest PASS.
5. **Repeat match (F1 framing, right index, careful hold):**
   `match_start_status` 0 → 35 events → terminal 3268 B
   `match_result` `matched: true`. `cancel_status` 0,
   `identities_preserved` true.
6. **Post-window:** `0x42`=2, repeat-equal true, SKS `0x208`,
   gate complete. F1 gate re-disabled (verified, no source diff).

## What this closes and what is next

- Closed: one-boot-fluke hypothesis; manual-bring-up fragility
  (loader tested on both paths: refuses-while-loaded pre-reboot,
  full bring-up post-reboot).
- Still manual: the two password unlocks (operator terminal) and
  the per-match password bind — the match-broker product question.
- Next: broker architecture (where the per-match password comes
  from: PAM capture vs context caching vs unlocked-keybag framing
  experiments), then facade/PAM work reusing the proven broker
  discipline. No further match science needed for verification;
  selectivity + repeatability are both proven.
