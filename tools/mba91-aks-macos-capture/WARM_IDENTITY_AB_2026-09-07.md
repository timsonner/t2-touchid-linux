# MBA91 warm identity A/B (2026-09-07)

Public-safe. No identity UUIDs, catacomb bytes, keybags, or raw Mesa payloads.

**Host:** MacBookAir9,1 (T2) · Omarchy hostname `MBA19-OMARCHY` · T2 NCM
`enp116s0f1u1` (PCI `0000:74:00.1`, MAC `ac:de:48:00:11:22`).  
**Peer HELO:** `bkremoted` / BridgeXPC **39** / OSBuild **23P6068**.  
**EP7 AKS:** still parked.

Related: `BRIDGEXPC_PATH.md`, `MESA_BENT_OPCODE_CROSSWALK.md`, `NEXT_STEPS.md`.

## BridgeXPC smoke (Omarchy, same day)

Read-only Multiverse → HELO → enveloped method **0** → method **1**:

| Check | Result |
| --- | --- |
| Peer HELO | `bkremoted`, BridgeXPC 39, `23P6068` |
| Method 0 | `(status=0, version=3)` |
| Method 1 | `(status=0, opened=true)` |

No method-3 / enroll / ConfirmSave / sensor reset / EP7.

## Session shape for Mesa canaries

After Multiverse open: method 0 → `setBridgeClientVersion(2)` → method 1, then
bounded method-3 (`biometric_perform_request`). Same order as bent’s
sensor-context / SKS probes.

## Cold canaries (before macOS warm handoff)

| Op | Result |
| --- | --- |
| `0x52` bio device list | status 0, 44 B, **1 builtin** |
| `0x54` accessoryInfo (type 2 + zero UUID, out cap 83) | status 0, exactly 83 B, **first_byte=0** (accessory-present false) |
| `0x27` SKS lock uid 501 | **v1** status 0, state `0x15`; v0/v2 fail `0xe00002c2` |
| `0x42` identity list uid 501 | status 0, **empty** |
| `0x08` GetIdentityRecords | **not** a clean list (v1 status 265 + zeroed buffer; v0 `0xe00002c2`) |

`0x08` is **not** an alias for bent’s `0x42` on this path.

## Warm A/B procedure

1. Existing macOS Touch ID enrollment (one finger, uid **501**) — no re-enroll.
2. Boot macOS; unlock / use Touch ID once so catacomb is live.
3. **Warm** reboot to Omarchy (no sensor reset; `fprintd` inactive).
4. Confirm T2 Multiverse (NM **Wired connection 2** pins
   `fe80::aede:48ff:fe00:1122/64` on `enp116s0f1u1`; ipv4 disabled).
5. Re-run the same canaries immediately.

## Warm vs cold

| Op | Cold | Warm |
| --- | --- | --- |
| `0x52` | 1 builtin | 1 builtin |
| `0x54` | 83 B, first_byte=0 | same — first_byte still **0** |
| `0x27` v1 | state `0x15` | state `0x10` |
| `0x42` | empty | **count=1, uid=501** (UUID redacted) |
| `0x08` | junk | still junk |

## Interpretation

- On this Air, a **warm** macOS → Omarchy reboot **preserves** at least one
  identity visible via bent’s `0x42` **without** Linux `loadCatacomb`.
- Remaining Bridge gaps:
  - **Cold** restore / `loadCatacomb` (and why `0x54` first_byte stays 0 even warm)
  - Linux-native enroll / ACM policy
  - Do not treat `0x08` as `0x42`
- Mute AKS EP7 stays parked; fingerprint path remains BridgeXPC.

## T2 NCM LL (Omarchy)

NM profile **Wired connection 2**: iface `enp116s0f1u1`, autoconnect,
`ipv4.method=disabled`, `ipv6.method=manual`,
`ipv6.addresses=fe80::aede:48ff:fe00:1122/64`.  
If Multiverse hits `ENETUNREACH`: `nmcli connection up "Wired connection 2"`.
