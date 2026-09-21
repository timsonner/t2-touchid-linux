# Locked-bag verdict: lock gates the sensor, unlock required (2026-09-20)

Branch: `research/mba91-aks-ep7`. F1 gate disabled (verified).
Shapes/statuses/counts only. No state change anywhere (both
windows mute; inventory 3/3 repeat-equal after).

## Verdict

**Unlock is genuinely required on MBA91 — the lock gates the
sensor itself, not just verdicts.** With bags locked (fresh boot,
no unlock): token-free match mutes (39 status + 1 statistics, no
verdict) AND credential-set-authorized match with live
policy-1007 mutes (29 events, no `match_result`) — despite
`match_start` 0, green prelude, and satisfied policy in both.
Neither framing nor ambient authorization overcomes a locked bag.

## The touch-signature discriminator

Unlocked windows carry the 73/3242 B finger-present event;
BOTH locked windows show only the idle ordinal cycle
(53/80/90/81/63/91/78/64/95) with zero 73 — matching September's
explicit note that the cycle runs "identically with and without
finger". The locked SEP does not report contact at all. This
rules out finger-timing as the explanation (twice over, across
framings): there is nothing to mistime when the sensor is tomb.

## Consequences

- The t2touch inference (password-bound matching without
  unlocked bags) does NOT transfer: per-image behavior differs,
  exactly as their compatibility doc warns. MBA91 needs
  unlocked bags, period.
- Native keeps exactly one wall: the activation ceremony that
  installs a password credential on created bags (-5 stable).
  No framing, context, or UID trick routes around unlock.
- SKS `0x219` accompanied every mute; `0x228`/`0x208` every
  verdict session. Correlation holds across the night; bit
  semantics still borrowed, still distrusted for claims.

## Next steps

1. Operator unlocks (still manual / credential-pending), then
   business as usual — nothing here changes the working reader.
2. Activation paper continues as the sole native direction.
3. Do-nots unchanged.
