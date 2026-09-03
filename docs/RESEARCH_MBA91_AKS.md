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

## Phase 3 result (2026-09-03)

`aks_ool_dma32=1` allocated `ool_in_dma=0x56c58000` / `ool_out_dma=0x56c5c000`
(under 4G). Capability still timed out with `skipped=0` over 30s. DMA32
hypothesis falsified.

## Next (after DMA32 falsified)

1. On timeout, log whether `ool_out` was DMA-touched without a mailbox reply.
2. Gate module load on successful `t2-biometric-port-refresh` (RSD warm), not ping alone.
3. Phase 2 ABI matrix if still silent.

## Phase 4 result (2026-09-03)

RSD-warm gate + `ool_out` touch check on cold boot: timeout with
`skipped=0 ool_out_len=0x0 ool_out_nonzero=0`. SEP neither wrote OOL nor rang
mailbox. DMA-without-doorbell and RSD-warm hypotheses falsified.

## Phase 2: `aks_cap_variant` matrix

Module param `aks_cap_variant` (0..5), one cold boot each:

| N | Meaning |
| --- | --- |
| 0 | baseline V1 selector=1 len=0x5c |
| 1 | V1 selector=0 |
| 2 | V2 envelope + selector=1 |
| 3 | mailbox length in low 16 bits of word[1] |
| 4 | mailbox declared length = full OOL 0x4000 |
| 5 | transaction tag 3 |

```bash
# in /etc/modprobe.d/t2-sep-transport.conf options line, add e.g.:
# aks_cap_variant=1
sudo /home/tim/Private/t2-touchid/rebuild-research-aks.sh
# full power-off between variants
journalctl -b -k | rg 't2_sep|research capability|AppleKeyStore|ool_out'
```

## Phase 2 result (2026-09-03)

`aks_cap_variant` 1–5 all timed out with `skipped=0 ool_out_nonzero=0` on cold
boot. ABI framing A/B matrix falsified.

## Phase 5 / bent-compat (variant 6)

Bent’s working MBP probe uses a **different** capability frame than stock
upstream V1 (92 bytes / prefix `0x48`) and our variant 2 (prefix `0x50` /
version 2):

- mailbox length `0x00640000` (100 bytes)
- length prefix `0x50`, **version field still 1**
- digest = SHA-256 truncated over header_tail `0x38` + body at offset `0x54`
  (calendar_seconds zeros are *not* in the v1 digest input)

`aks_cap_variant=6` reproduces that exact wire + digest (+ `dma_wmb`).

## Phase 2 variant 6 result (2026-09-03)

Bent-compat frame (`aks_cap_variant=6`) still timed out with
`skipped=0 ool_out_nonzero=0`. Wire/digest parity with bent’s MBP probe is
insufficient alone on MBA91.

## Phase 5: MSI + startCPU + EP0 NOP

Research defaults (also set in modprobe conf):

| Param | Default | Meaning |
| --- | --- | --- |
| `aks_msi` | true | 2× MSI (inbox-nempty / outbox-empty) |
| `aks_start_cpu` | true | Apple `_startCPUGated` at `0x8040/0x8048/0x8028` |
| `aks_ep0_nop` | true | Control NOP (tag `0xfe`) before OOL |
| (send path) | — | fence-read outbox status after commit word |

Keep `aks_cap_variant=6` for this boot. Log lines: `research MSI`,
`research CPU controls`, `research EP0 NOP`, timeout `msi0=`/`msi1=`.

## Phase 5 results (2026-09-03)

With MSI + startCPU + EP0 NOP:

- Cold load finds SEP **stopped** (`+0x8028=0x7f`); start yields `0x7a` / `+0x8048=0x1`.
- EP0 NOP replies in ~1 ms; both MSI vectors fire.
- AKS OOL registration still succeeds.
- `aks_cap_variant=6` and **variant 0** still true-silence on `0x4d`.

Prior ABI matrix without startCPU is obsolete for conclusions about wire format alone.

## Phase 6: discovery + ACM canary

| Param | Default | Meaning |
| --- | --- | --- |
| `aks_discover` | true | 1s passive inbox listen after NOP |
| `aks_acm_canary` | true | EP10 OOL + SCRD init (`DRCS\n` + `0x28`) before AKS capability |

Look for `research discovery rx` / `research ACM SCRD rx` vs timeouts.
