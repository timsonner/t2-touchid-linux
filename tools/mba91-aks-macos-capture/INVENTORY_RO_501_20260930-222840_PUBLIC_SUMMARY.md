# Inventory RO 501 — 2026-09-30 22:28 MDT (private dump re-run after journal-dir fix)

## Verdict
**YES — private inventory persisted.** Same post-enroll public picture as `…-222437`, plus root-only private JSON under `/var/lib/t2-touchid/inventory-journals/`.

## What was fixed
- Failure mode on `…-222437`: `PermissionError: private inventory parent must be root-owned mode 0700` for parent `/var/lib/t2-touchid/inventory-journals` (oneshot used `mkdir -p`, which leaves umask `0755`).
- Fix: `install -d -o root -g root -m 0700` on `/var/lib/t2-touchid` + `inventory-journals` (+ `/run/t2-touchid`); cleared `/run/t2-touchid/inventory-ro-501.done`; stopped RemainAfterExit unit; re-ran `/usr/local/sbin/t2-inventory-ro-501`.
- Hygiene (pending/applied in same sudo peek): oneshot script `mkdir -p` → `install -d -m 0700` so this does not recur.

## Transport / port
- Port **49183** (unchanged this boot); host `fe80::aede:48ff:fe33:4455` iface `enp116s0f1u1` uid **501**
- `rc=0` **`priv_rc=0`**
- Public: `INVENTORY_RO_501_20260930-222840.{json,log,_REPORT.txt}`
- Private: `/var/lib/t2-touchid/inventory-journals/inventory-ro-501-20260930-222840.private.json` (root `0600`; also `…-222830.private.json` from same fix window)

## Public facts (vs empty pre-enroll `…-174149`)

| Field | Pre `…-174149` | Post `…-222437` / `…-222840` |
| --- | --- | --- |
| Per-user `0x42` | status 0, nil → count **0** | status 0, len 20 → count **1** |
| Global list | nil → **0** | len 40 → count **1** |
| Capacity `0x0F` | **5** | **5** |
| Free `0x41` | **0** (unusable empty picture) | **2** |
| Catacomb UUID/hash | status **22** | status **0**, lens 16 / 33 |
| Catacomb state `0x3C` words | `[0xFFFFFFFF, 1]` | **`[0xFFFFFFFF, 3, 501, 3]`** |
| SKS lock `0x27` | **21 = 0x15** cold | **16 = 0x10** warm |
| Private complete | false (gate failures) | **true**, file written |

## Hard bans (unchanged)
No Linux enroll start, no bag create, no `0x21`, no second bag, no bag writes. No commit/push this turn.

## Private presence (safe; no raw UUID/hash in git)

From root peek of `inventory-ro-501-20260930-222840.private.json` (730 B, mode `0600`):

- `schema_version=1`, `apple_uid=501`, `biometric_protocol_version=2`
- `catacomb.present=True`; `catacomb.uuid` str_len **36**; `catacomb.hash` str_len **64**; `catacomb.global_state` str_len **32**
- `per_user_identity_records` len **1** (`identity_uuid` len 36, `user_id=501`)
- `global_identity_records` len **1** (`group_type=1`, `group_uuid` len 36, `identity_uuid` len 36, `user_id=501`)
- `maximum_capacity=5`, `configured_user_free_capacity=2`, `sks_lock_state_raw=16`
- `double_collection_equal=True`
- Also present: twin private `…-222830.private.json` (same size/mode) from the fix window

Oneshot hygiene applied: `mkdir -p` → `install -d -o root -g root -m 0700` in
`/usr/local/sbin/t2-inventory-ro-501` and repo twin `t2-inventory-ro-501.sh`.
