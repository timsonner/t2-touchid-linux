# Research: MacBookAir9,1 AKS endpoint-7 bring-up

Branch: `research/mba91-aks-ep7`

## Problem

On `MacBookAir9,1` (iBridge `23.16.16068`), stock `t2_sep_transport` with
`register_ool=1 probe_capabilities=1` registers OOL buffers successfully but
AppleKeyStore capability negotiation times out (`mailbox receive timeout`,
`-110`). Soft reboot leaves dirty SEP mailbox counters; cold power resets them
to `0x20001` / `0x20001`, but capability still times out.

Upstream is only hardware-proven on `MacBookPro16,2` / bridgeOS `23P1072`.

## Phase 1 knobs (this branch)

Module parameters (research defaults **on**):

| Param | Default | Meaning |
| --- | --- | --- |
| `aks_cap_zero_time` | true | Stamp `usec_time=0` on capability request (bent’s first live reply class) |
| `aks_cap_trace` | true | Log non-secret req/rx mailbox words, DMA addrs, status |
| `aks_cap_accept_any_ep7` | true | Accept mismatched EP7 replies for diagnostics |
| `aks_cap_timeout_sec` | 30 | Capability-only mailbox wait |
| `aks_ool_dma32` | true | Force OOL buffers into 32-bit DMA |

Do not commit keybags, catacomb, or `/etc` private config to this branch.

## Cold-boot test

```bash
# after installing this branch via DKMS / install.sh
sudo poweroff   # full power-off, wait 20s, power on
journalctl -b -k | rg 't2_sep|research capability|AppleKeyStore'
ls -l /dev/t2-aks
```

Look for `research capability rx:` (SEP spoke) vs timeout-only.

## Phase 1 result (2026-09-03)

Cold power, zero_time=1, 30s wait: `skipped=0`, true EP7 silence. OOL DMA was
`0x16753…` / `0x16752…` (above 4G). Next: `aks_ool_dma32=1`.
