# Research: MacBookAir9,1 AKS endpoint-7 bring-up

Branch: `research/mba91-aks-ep7`  
Status: **PARKED** (2026-09-03) — Touch ID blocked on mute AppleKeyStore EP7.

## Hardware / software

| Item | Value |
| --- | --- |
| Machine | MacBookAir9,1 (MBA91-OMARCHY) |
| iBridge / bridgeOS | `23.16.16068` |
| Host | Omarchy / Arch, kernel `7.1.8-arch1-Watanare-T2-3-t2` |
| PCI SEP | `106b:1802` BAR4 |
| Upstream proof | MacBookPro16,2 + bridgeOS `23P1072` only |
| Keybags / catacomb | Exported privately; **not** on this branch |

## Final scoreboard (clean cold boot, research DKMS)

| Path | Result |
| --- | --- |
| Cold mailbox | `inbox/outbox=0x20001` after full power-off |
| SEP CPU at load | **Stopped** (`+0x8028=0x7f`); Apple start → `0x7a` / `+0x8048=0x1` |
| MSI (2 vectors) | Allocates; both fire on EP0 NOP / ACM |
| EP0 control NOP | **Reply ~1 ms** |
| EP0 AKS OOL register | **Success** (16 KiB in/out) |
| Passive `0xfd` discovery (1 s) | **Empty** (no ads) |
| ACM EP10 SCRD init | **Reply ~1 ms** |
| AKS EP7 `0x19` get_device_state | **Timeout** `-110`, `ool_out_nonzero=0` |
| AKS EP7 `0x4d` get_capabilities | **Timeout** `-110`, `ool_out_nonzero=0` |
| `/dev/t2-aks` | Never created (capability hard-fails) |

### Conclusion

Intel SEP **mailbox transport is healthy** on this Air (EP0 + MSI + startCPU +
EP10 ACM). **AppleKeyStore on fixed endpoint 7 does not answer** any probed
opcode; silence is true (no mailbox reply and no OOL DMA write). This is not
explained by the falsified hypotheses below. Likely Air/bridgeOS-specific AKS
availability, endpoint mapping, or a missing SEP-side bring-up step that MBP
`23P1072` does not need — not a simple host wire-format bug.

Touch ID (keybag load → unlock → match → PAM) is **parked** until EP7 speaks.

## Falsified hypotheses

| Hypothesis | Result |
| --- | --- |
| `usec_time=0` alone | Still silent |
| OOL must be DMA32 (&lt;4G) | Still silent under 4G |
| RSD / biometric-port warm before load | Still silent |
| DMA-without-doorbell (`ool_out` touch, no ring) | `ool_out_nonzero=0` |
| ABI matrix `aks_cap_variant` 1–5 | All silent |
| Bent-compat frame (variant 6: prefix `0x50`, ver 1, 100 B, bent digest) | Silent without and with startCPU |
| Missing MSI + `_startCPUGated` + EP0 NOP | Bring-up works; AKS still silent |
| Only `0x4d` broken (try `0x19`) | `0x19` also silent |

## Research module parameters (this branch)

Defaults are research-oriented (on). Do not ship these as upstream defaults.

| Param | Default | Meaning |
| --- | --- | --- |
| `aks_cap_zero_time` | true | Stamp `usec_time=0` on capability |
| `aks_cap_trace` | true | Log non-secret mailbox / DMA / status |
| `aks_cap_accept_any_ep7` | true | Accept mismatched EP7 replies |
| `aks_cap_timeout_sec` | 30 | Capability mailbox wait |
| `aks_ool_dma32` | true | Force 32-bit coherent OOL |
| `aks_cap_variant` | 0 | 0 stock; 1–5 framing A/B; 6 bent-compat |
| `aks_msi` | true | 2× MSI before start/OOL |
| `aks_start_cpu` | true | Apple `_startCPUGated` (`0x8040/0x8048/0x8028`) |
| `aks_ep0_nop` | true | EP0 NOP (tag `0xfe`) after start |
| `aks_discover` | true | 1 s passive inbox listen after NOP |
| `aks_acm_canary` | true | EP10 OOL + SCRD init canary |
| `aks_device_state_canary` | true | AKS `0x19` before capabilities |

## Install notes (Air)

- Full **power-off** between tests (soft reboot leaves dirty mailbox counters).
- `dkms remove` can restore an archived **stock** module into
  `extra/t2_sep_transport.ko` and win over an empty DKMS tree — always verify
  `modinfo -n` is under `updates/dkms/` and research parms exist before reboot.
- Helper used on MBA91: `~/Private/t2-touchid/force-rebuild-research-aks.sh`
  (fail-closed parm check). Not committed here (private paths).

## If resumed later

Priority order (do not re-burn falsified items unless paired with a new lever):

1. Map service endpoints (SBIO `0x08`, other IDs) — which apps answer on Air?
2. Capture macOS-side first AKS txn on this bridgeOS vs MBP `23P1072` (header only).
3. Consider upstream issue on `jmurth1234/t2-touchid-linux` with this scoreboard.
4. Only then revisit AKS wire / endpoint identity.

## References

- Upstream: https://github.com/jmurth1234/t2-touchid-linux  
- Bent bring-up / MSI / startCPU: https://github.com/bentsignal/t2-omarchy (`docs/touch-id.md`, `prototypes/t2sep-probe/`)  
- Fork branch: https://github.com/timsonner/t2-touchid-linux/tree/research/mba91-aks-ep7  
