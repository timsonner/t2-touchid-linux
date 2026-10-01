# Inventory RO 501 — 2026-09-30 22:24 MDT (post macOS one-finger enroll + warm reboot)

## Verdict
**YES — macOS enroll survived into Linux.** Per-user `0x42` fingerprint/identity count is **non-zero (1)**. Catacomb user component is present. SKS lock warmed from cold `0x15` → `0x10`.

## Transport / port
- Kernel: `7.2.7-arch1-Watanare-T2-2-t2`
- `/dev/t2-aks` present; `lsmod`: `t2_sep_transport` loaded (plus t2bce_*)
- BiometricKit BridgeXPC port this boot: **49183** (prior empty-501 boot used 49208)
- Host `fe80::aede:48ff:fe33:4455` iface `enp116s0f1u1` uid **501**
- Command: systemd oneshot `t2-inventory-ro-501.service` → `/usr/local/sbin/t2-inventory-ro-501` (repo twin `tools/mba91-aks-macos-capture/t2-inventory-ro-501.sh`)
- Service: active (exited) success at **22:24:38 MDT**; public `rc=0`
- Artifacts: `INVENTORY_RO_501_20260930-222437.{json,log,_REPORT.txt}`
- Private dump **attempted** (`private_inventory_complete=true` in public JSON) but **write failed**: `PermissionError: private inventory parent must be root-owned mode 0700` under `/var/lib/t2-touchid/inventory-journals`. Needs Tim `sudo` to `chown root:root` + `chmod 0700` that dir, then clear `/run/t2-touchid/inventory-ro-501.done` and re-run oneshot — or one-shot private-only under fixed dir. **Public facts alone are enough for the yes/no.**

## 0x42 / identity inventory (critical)
| Field | Pre-enroll `…-174149` (17:41 MDT) | Post-enroll `…-222437` (22:24 MDT) |
| --- | --- | --- |
| Per-user `0x42` | status 0, **nil** → count **0** | status 0, output_length **20** → count **1** |
| `identity_record_bytes_valid` | false | **true** |
| Global identity list | nil → count **0** | output_length **40** → count **1** |
| `configured_identity_records_reconciled` | false | **true** |
| `biometric_protocol_v2_attested` | false | **true** (`v2-global-identity-command`) |
| Snapshot A/B `full_snapshot_repeat_equal` | true | **true** |

**Answer: 0x42 count = 1 (> 0).** One enrolled fingerprint/identity slot for uid 501 is visible from Linux after warm reboot.

## Capacity
- `identity_maximum_capacity` (**0x0F**): **5** (unchanged)
- `identity_free_count` (**0x41**): **2** (was **0** while empty/nil — now a usable free-slot picture with Catacomb present)

## Catacomb / SKS
| Field | Pre (`…-174149`) | Post (`…-222437`) |
| --- | --- | --- |
| Catacomb UUID (`0x38`) / hash (`0x3A`) | status **22** | status **0**, lengths valid |
| `catacomb_component_present` | (absent / gate fail) | **true** |
| Catacomb state (`0x3C`) words | `[0xFFFFFFFF, 1]` | **`[0xFFFFFFFF, 3, 501, 3]`** |
| SKS lock (`0x27`) | **21 = `0x15`** (cold) | **16 = `0x10`** (warm enrolled coloring) |

## Gate / private
- Public gate failures: **none** (`private_inventory_gate_failures: []`, `private_inventory_complete: true`)
- Private file not persisted solely due to journal-dir mode/ownership (not due to incomplete inventory)

## Hard bans (unchanged)
No Linux enroll start, no bag create, no `0x21`, no second bag, no bag writes.

## Next recommended step
**Interpret this RO result; do not Linux-enroll yet.**

1. Optional hygiene (Tim sudo): fix `/var/lib/t2-touchid/inventory-journals` to root:root mode 0700, then re-run private dump for UUID/hash bytes if needed for match research.
2. Compare Catacomb UUID/hash and identity record layout to prior macOS-bag working boots before any password-bound Linux add-finger / match.
3. Still **no** Linux enroll / create / `0x21` until that interpretation is written down.
