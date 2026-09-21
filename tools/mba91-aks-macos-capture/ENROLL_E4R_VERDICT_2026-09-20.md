# E4r verdict: clean refusal, finger work matters (2026-09-20)

Branch: `research/mba91-aks-ep7`. E4 gate disabled (verified).
Shapes/statuses/counts only.

## Verdict

**Refused-clean, state untouched.** Same zero-group start opened
(dispatch 0), all 8 continues status 0, cancel 0 — but all
continues carried exactly 1 event each (E4's success had a 3-event
burst on #5) and the count stayed 2→2. The SEP ran the protocol
and minted nothing. This is the honest negative the design
allowed for, and it teaches: enrollment is not automatic on
protocol completion — the template engine needs real coverage
work across the dance.

## Reading

E4 vs E4r differ only in the finger work (same framing, same
session shape, same finger, same boot epoch family): E4's dance
produced progress chatter and an identity; E4r's uniform dance
produced baseline chatter and none. The SEP evaluates presented
biometric variety, not command shapes. Retry prescription: deliberate
placement variety across the 8 touches (center, tip, left edge,
right edge — the macOS enroll rhythm), not the same plant ×8.

## State

Post: `0x42`=2, repeat-equal true, SKS `0x208`, free 1/5. The
freed slot from D2 is intact and waiting. No halt condition
triggered (refused-clean is terminal-honest, not ambiguous).

## Next steps

1. **E4r retry with variety** (same gates + ack + dance, varied
   placements). Success closes the lifecycle loop 2→3→2→3.
2. Do-nots unchanged.
