# MBA91 `0x54` accessoryInfo notes (2026-09-07)

Public-safe. No raw reply dumps in git.

## Command shape (bent + MBA91)

| Field | Value |
| --- | --- |
| Opcode | `0x54` (decimal 84) — bent: read-only `accessoryInfo:` |
| Version | **1** (`COMMAND_VERSION`); version **2** rejected here (`0xe00002c2`) |
| Value | 0 |
| Input | **20 bytes**: LE `uint32` type + 16-byte accessory UUID |
| Canonical input | type **2** + **zero** UUID (built-in) |
| Output capacity | **83** |
| Success gate (bent) | status 0, len 83, **first byte ≠ 0** (accessory-present) |

Contrast with `0x52` bio-device list: records use accessory **type 1** /
group type 1 / flags 6 for Builtin (`BIO_DEVICE_RECORD`,
`BUILTIN_ACCESSORY_TYPE=1`). The `0x54` query type **2** is a different enum
space (accessoryInfo selector), not a typo for type 1.

## Offline layout (what is known)

| Offset | Meaning | Confidence |
| --- | --- | --- |
| 0 | Accessory-present flag (0 = absent) | **high** (bent gate) |
| 1..82 | Remainder of accessoryInfo blob | **unknown** field-level; bent never published a struct table |

No public bent note names the remaining 82 bytes. Treat them as opaque until a
macOS/static decode lands.

## Live Omarchy results (MBA19, empty `0x42`)

Session: Multiverse → method 0 → client-version 2 → method 1. No reset / load /
enroll.

| Probe | status | len | first | nonzero_bytes |
| --- | --- | --- | --- | --- |
| type 1 + zero UUID | 0 | 83 | 0 | **0** |
| type 2 + zero UUID (canonical) | 0 | 83 | 0 | **0** |
| type 0 + zero UUID | 0 | 83 | 0 | **0** |
| type 3 + zero UUID | 0 | 83 | 0 | **0** |
| type 2, command version 2 | `0xe00002c2` | 83 | 0 | 0 |
| Order `0x52` → `0x54` → `0x0c` | 0 / 0 / 0 | 83 for 54 | 0 | **0** |

`0x52` still reports 1 builtin device record. So: **device list ≠ accessoryInfo
populated**. The whole 83-byte reply is zero-filled, not merely first_byte.

This matches bent’s Linux observation (status 0 / 83 B / first_byte 0) even
when warm identities existed — MBA91 now shows the stronger form: **all-zero
payload** with empty `0x42` after the reset-load run.

## Tie to `0x40` status 257

bent links general `0x40` status **257** to missing accessory/device-group
context. Our Air: `0x54` never shows present → load rejects. Input type A/B did
**not** flip presence; ordering with `0x52`/`0x0c` did not either.

## Implications

1. Do **not** retry blind `0x40` until accessory-present can be nonzero (or we
   prove a different load envelope).
2. Next research is **how macOS populates accessoryInfo** (cacheAccessories /
   catacomb-accessory lifecycle), not more type enums on Linux.
3. Optional: on Sequoia, log whether `accessoryInfo` / Mesa `0x54` ever returns
   nonzero first_byte around unlock — contrast only, no Linux load.

## Script

Local: `~/Projects/t2sep-probe/mba91-accessory-54-ab.py`
