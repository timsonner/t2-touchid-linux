# MBA91 warm catacomb / accessory probes (2026-09-07)

Follow-on to `WARM_IDENTITY_AB_2026-09-07.md`. Same warm Omarchy session
(after macOS→Linux handoff; `0x42` count=1 uid=501). Public-safe: status /
lengths / booleans only.

## Session

Multiverse → method 0 → `setBridgeClientVersion(2)` → method 1 → read-only
method-3. No `loadCatacomb`, save/ConfirmSave, enroll, or sensor reset.

## Results (still warm)

| Op | Result |
| --- | --- |
| `0x42` identity list | status 0, **count=1** (still warm) |
| `0x54` accessoryInfo | status 0, 83 B, **first_byte=0** |
| `0x38` getCatacombUUID | **fail** `0xe00002c2`, out len 16 all-zero |
| `0x3c` getCatacombState | **fail** `0xe00002c2`, out len 2048 |
| `0x50` getCatacombGroupState | **fail** `0xe00002c2`, out len 3584 |
| `0x3a` getCatacombHash | v0 fail `0xe00002c2`; **v1 status 0, len 33** (bytes not logged) |
| `0x53` sensor readiness | status 0, value `0x01` |
| `0x10` provisioning | status 0, state **5** |
| `0x4c` xART available v0 | fail `0xe00002c2` |

## Interpretation

- Warm reboot leaves **identity records** queryable via `0x42` without Linux
  `loadCatacomb`.
- Concurrently, **catacomb store** queries (`0x38` / `0x3c` / `0x50`) fail with
  the same `0xe00002c2` class error — so “identity present” ≠ “catacomb store
  mounted for those APIs.”
- `0x3a` v1 succeeding (33 B) while `0x38` fails is a useful bent/macOS
  discriminator to chase in codec notes.
- `0x54` first_byte remaining 0 matches bent’s post-reset Linux observation and
  is **orthogonal** to warm `0x42` survival on this Air.
- Omarchy install has **no** `~/Private` catacomb `.cat` tree; bounded `0x40`
  load needs a USB/macOS copy of `/Library/Catacomb/<UUID>/` (see
  `BACKUP_AND_TEARDOWN.md`) — do not commit raw `.cat`.

## Next experiments

1. **Cold Omarchy reboot A/B** (no macOS): does `0x42` stay non-empty after a
   full power cycle on Linux alone?
2. Copy Private `.cat` / CFTL extract onto the Air → bounded `0x40` loadCatacomb
   canary (no enroll), then re-check `0x38`/`0x3c`/`0x54` first_byte.
