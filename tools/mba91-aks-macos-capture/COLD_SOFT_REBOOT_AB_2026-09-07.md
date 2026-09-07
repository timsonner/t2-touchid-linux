# MBA91 Omarchy soft-reboot identity A/B (2026-09-07)

Public-safe. Follow-on to `WARM_IDENTITY_AB_2026-09-07.md` and
`WARM_CATACOMB_PROBES_2026-09-07.md`.

## Procedure

1. Warm state already proven: macOS Touch ID → Omarchy, `0x42` count=1.
2. **Soft reboot** Omarchy → Omarchy only (kernel reboot). **Not** a full
   power-off / cold power-on. No macOS boot in between.
3. No sensor reset / fprintd. Multiverse LL still up via NM Wired connection 2.
4. Re-run Mesa canaries + catacomb store probes.

## Results (post soft reboot)

| Op | Result |
| --- | --- |
| Method 0 / client-version 2 / method 1 | ok |
| `0x52` | 1 builtin |
| `0x54` | 83 B, first_byte=0 |
| `0x27` v1 | state `0x10` (same as prior warm) |
| `0x42` | **count=1, uid=501** — identity **survived** soft reboot |
| `0x08` | still not a clean list |
| `0x38` / `0x3c` | fail `0xe00002c2` |
| `0x3a` v1 | status 0, len 33 |

## Interpretation

- On this Air, identity visibility via `0x42` survives an **Omarchy soft reboot**
  without macOS and without Linux `loadCatacomb`.
- Catacomb store APIs (`0x38`/`0x3c`) remain failed — same split as warm probes.
- **Still unknown:** full power-off → power-on (true cold). Soft reboot may keep
  bridgeOS / Mesa RAM state that a power cycle clears.
- Do not over-claim “cold restore solved”; label this **soft-reboot preserve**.

## Next

1. Optional: full power-off A/B (hold power until off, then on into Omarchy only).
2. Private `.cat` → bounded `0x40` loadCatacomb (no enroll).
