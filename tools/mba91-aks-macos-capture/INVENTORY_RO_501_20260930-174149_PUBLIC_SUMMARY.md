# Inventory RO 501 — 2026-09-30 17:41 MDT (public facts only)

## Transport / port
- `/dev/t2-aks` present; `t2_sep_transport` + patched `applesmc` boot_state OK
- BiometricKit BridgeXPC port rediscovered via `t2-biometric-port-refresh`: **49208**
- Host `fe80::aede:48ff:fe33:4455` iface `enp116s0f1u1` uid **501**
- Artifacts: `INVENTORY_RO_501_20260930-174149.json` + `_REPORT.txt`
- Private dump **not** written (`private_inventory_complete=false`); expected for this state

## 0x42 / identity inventory
- Per-user `0x42`: status **0**, output **nil-placeholder** → effective count **0** (no enrolled templates for 501)
- Global `0x51`: status **0**, output **nil-placeholder** → global count **0**
- `identity_record_bytes_valid` / `global_*` / reconciled: **false** (nil, not a 20/40-byte record stream)
- Snapshot A/B: all inventory fields **repeat_equal true** (stable)

## Capacity
- `identity_maximum_capacity` (**0x0F**): **5**
- `identity_free_count` (**0x41**): **0** (with nil `0x42`; treat as “no usable free-slot picture” until Catacomb/user component exists — not “5 fingers enrolled”)

## Catacomb / SKS-ish (public)
- Catacomb UUID (`0x38`) / hash (`0x3A`): status **22** (`0x16`) — **no user component** for 501
- Catacomb state (`0x3C`): status 0, words **`[0xFFFFFFFF, 1]`**
- SKS lock (`0x27`): **21 = `0x15`** (cold/unwarmed coloring on this platform; warm enrolled path historically `0x10`+)
- Protocol cmd-1: status `0xe00002c2`; `biometric_protocol_v2_attested=false`
- Bridge negotiated client version **2** (bridge advertises 3)

## Gate failures (why private refused)
`identity_lists_reconciled`, `protocol_v2_attested`, `catacomb_uuid_length`, `catacomb_hash_length`

## Recommendation (next)
**Prefer macOS re-enroll (one finger) over another Linux password-bound enroll attempt on this empty 501.**

Rationale:
1. Live SEP shows **empty** 501 inventory + **no Catacomb UUID/hash component** (status 22) + cold SKS `0x15` — matches STATUS1 empty/component-missing picture.
2. Prior Linux-only enroll attempts on this bag class failed credential-class gates; enroll/start/create/`0x21`/second-bag remain hard-banned.
3. One macOS System Settings Touch ID enroll for uid 501 is the proven producer of Catacomb component + warm SKS + non-nil `0x42`; then Linux re-inventory (read-only) before any password-bound add-finger/match research.

Password-bound Linux enroll is a post-Catacomb research track — not before.

## Oneshot fix
`t2-inventory-ro-501` resolves port from env → `/var/lib/t2-touchid/biometric-port` → refresh; waits for cache; public-first; private only if gate complete; unit `Wants=` port-refresh.
