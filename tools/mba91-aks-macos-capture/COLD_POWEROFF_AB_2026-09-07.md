# MBA91 true cold (power-off) identity A/B (2026-09-07)

Public-safe. Follow-on to `COLD_SOFT_REBOOT_AB_2026-09-07.md`.

## Procedure

1. Prior state: soft reboot already left `0x42` count=1.
2. **Full shutdown** → power off → power on into **Omarchy only** (no macOS).
3. No sensor reset / fprintd. Multiverse via NM Wired connection 2.
4. Re-run Mesa canaries + catacomb store probes.

## Results (post power-off)

| Op | Result |
| --- | --- |
| RSD advertised port | `49184` (dynamic; was `49156` earlier) |
| Method 0 / client-version 2 / method 1 | ok |
| `0x52` | 1 builtin |
| `0x54` | 83 B, first_byte=0 |
| `0x27` v1 | state `0x10` |
| `0x42` | **count=1, uid=501** — survived **true cold** |
| `0x08` | still not a clean list |
| `0x38` / `0x3c` | fail `0xe00002c2` |
| `0x3a` v1 | status 0, len 33 |
| `0x53` readiness | `0x01` |
| `0x10` provisioning | state **5** |

## A/B ladder (MBA91 Omarchy)

| Transition | `0x42` count | Notes |
| --- | --- | --- |
| Cold before any macOS warm | 0 | empty |
| macOS Touch ID → warm Omarchy | 1 | first prove |
| Omarchy soft reboot | 1 | preserved |
| **Full power-off → Omarchy** | **1** | **preserved** |

## Interpretation

- On this Air / bridgeOS **23P6068**, identity visibility via bent’s `0x42`
  survives true host power-off **without** Linux `loadCatacomb`.
- bent’s “cold restore” gap is **not** “`0x42` goes empty after power loss” on
  this SKU — at least after macOS has enrolled once and state has been live.
- Still broken / distinct:
  - `0x38` / `0x3c` catacomb **store** queries fail even when `0x42` is non-empty
  - `0x54` accessory-present first_byte stays 0
  - Linux-native enroll / ACM still open
- First empty `0x42` on this Omarchy install was **before** the macOS warm
  handoff — not after power-off once identities existed.

## Next

1. USB/Private `.cat` → bounded `0x40` (does it flip `0x38`/`0x3c` / `0x54`?)
2. Warm match canary (read-only path) only if Tim wants — still no enroll.
3. Keep EP7 parked.
