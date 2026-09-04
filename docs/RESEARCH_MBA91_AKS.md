# Research: MacBookAir9,1 AKS endpoint-7 bring-up

Branch: `research/mba91-aks-ep7`  
Status: **PARKED** (2026-09-03/04) — Touch ID blocked on mute AppleKeyStore EP7.
Linux-side documented AKS framing is exhausted; next lever is macOS first-txn
capture on this bridgeOS (or park).

## Hardware / software

| Item | Value |
| --- | --- |
| Machine | MacBookAir9,1 (MBA91-OMARCHY) |
| iBridge / bridgeOS | `23.16.16068` |
| Host | Omarchy / Arch, kernel `7.1.8-arch1-Watanare-T2-3-t2` |
| PCI SEP | `106b:1802` BAR4 (`04:00.2`) — **not** audio `04:00.3` / `106b:1803` |
| Upstream proof | MacBookPro16,2 + bridgeOS `23P1072` only |
| Keybags / catacomb | Exported privately; **not** on this branch |

## Final scoreboard

### Cold-boot transport (research DKMS)

| Path | Result |
| --- | --- |
| Cold mailbox | `inbox/outbox=0x20001` after full power-off |
| SEP CPU at load | **Stopped** (`+0x8028=0x7f`); Apple start → `0x7a` / `+0x8048=0x1` |
| MSI (2 vectors) | Allocates; both fire on EP0 NOP / ACM |
| EP0 control NOP | **Reply ~1 ms** |
| EP0 AKS OOL register | **Success** (16 KiB in/out) |
| Passive `0xfd` discovery | **Empty** — 1 s and dual **10 s** phases `pre-ool` + `post-acm` (`records=0`) |
| ACM EP10 SCRD init | **Reply ~1 ms** |
| AKS EP7 `0x19` | **Timeout** `-110`, `ool_out_nonzero=0` |
| AKS EP7 `0x4d` | **Timeout** `-110`, `ool_out_nonzero=0` |
| `/dev/t2-aks` | Never created (capability hard-fails) |
| `/dev/t2-sep-lab` | Registered even when capability fails (`aks_lab`) |

### In-session (same conclusions, lab path)

| Probe | Result |
| --- | --- |
| Lab `aks` `0x4d`/`0x19`/`0x06` (v1/v2, time, bodies, mb-length matrix) | All **ETIMEDOUT**, TX/outbox only |
| Lab `aks` `0x2a` set_env (bent body) | **ETIMEDOUT** |
| Bent **exact** full-wire `0x4d`/`0x2a` via `ool-write`+`raw` | **ETIMEDOUT**, `ool_out=0` (rules out lab header/codec) |
| EP0 presence map Mandt EPs | **ACK:** 7, 10, **12**; **EREMOTEIO:** 1, 2, 3, 5, 8, 11 |
| EP0 opcodes `4`/`5` (size) on 7/10/12 | **EREMOTEIO**, SEP result `0x1` (answered reject; not silence) |
| EP0 opcodes `2`/`3` (addr) | **ACK** on 7/10/12 |
| EP0 `SECMODE_REQUEST` (op 20) | **OK** (data `1`) |

### Conclusion

Intel SEP **mailbox transport is healthy** on this Air (EP0 + MSI + startCPU +
EP10 ACM + EP12 SET_OOL). **AppleKeyStore service traffic on EP7 does not
answer** any documented opcode tried — including bent’s exact codec wires.
Silence is true (no mailbox reply and no OOL DMA write). This is not a simple
host wire-format bug relative to bent/MBP.

Touch ID (keybag load → unlock → match → PAM) stays **parked** until EP7 speaks
or a macOS capture shows a different bring-up/endpoint identity.

## Falsified hypotheses

| Hypothesis | Result |
| --- | --- |
| `usec_time=0` alone | Still silent |
| OOL must be DMA32 (<4G) | Still silent under 4G |
| RSD / biometric-port warm before load | Still silent |
| DMA-without-doorbell | `ool_out_nonzero=0` |
| ABI matrix `aks_cap_variant` 1–5 | All silent |
| Bent-compat frame (variant 6) | Silent |
| Missing MSI + startCPU + EP0 NOP | Bring-up works; AKS still silent |
| Only `0x4d` broken | `0x19` and `0x2a` also silent |
| Missed early `0xfd` ads (short listen) | Dual 10 s pre-ool + post-acm still empty |
| Lab AKS header ≠ bent codec | Bent exact wires still silent |
| Mandt standalone OOL size ops `4`/`5` | Rejected (`0x1`); addr ops `2`/`3` work |
| ACM OOL alias caused AKS mute | Restored ACM OOL; AKS still silent |
| Wrong PCI function (audio vs SEP) | SEP is `04:00.2`; audio is separate `04:00.3` |

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
| `aks_start_cpu` | true | Apple `_startCPUGated` |
| `aks_ep0_nop` | true | EP0 NOP (tag `0xfe`) after start |
| `aks_discover` | true | Passive inbox listen for ads |
| `aks_discover_ms` | 10000 | Listen window; phases `pre-ool` and `post-acm` |
| `aks_acm_canary` | true | EP10 OOL + SCRD init canary |
| `aks_device_state_canary` | true | AKS `0x19` before capabilities |
| `aks_lab` | true | Register `/dev/t2-sep-lab` even if capability fails |

## In-session lab

After research DKMS with `register_ool=1`, capability may still time out — that
**no longer** blocks userspace. `aks_lab` registers root-only `/dev/t2-sep-lab`
even if `/dev/t2-aks` stays disabled. OOL DMA remains pinned; `rmmod` blocked
until reboot.

```bash
tools/build-t2-sep-lab.sh /home/tim/Private/t2-touchid/t2-sep-lab
sudo /home/tim/Private/t2-touchid/t2-sep-lab status
sudo /home/tim/Private/t2-touchid/t2-sep-lab aks --op 0x4d --ver 2 --zero-time --timeout-ms 5000
sudo /home/tim/Private/t2-touchid/t2-sep-lab ep0 --endpoint 12 --opcode 2 --tag 20 --size 16384 --dma in
```

Ioctls: `STATUS`, `RAW_MB`, `OOL`, `EP0`, `AKS` (lab AKS path has **no**
operation whitelist). Do not log OOL payload contents from the driver.

Private MBA helpers (not in git): `force-rebuild-research-aks.sh`,
`ep0-ool-grid.sh`, `bent-exact-wire-canary.py`, `send-bent-wire.sh`,
`bent-codec/aks-transport.py` (from bentsignal).

## Install notes (Air)

- Full **power-off** between cold tests.
- `dkms remove` can restore stock into `extra/` — verify `modinfo -n` under
  `updates/dkms/` and research parms before reboot.
- Lab babysitting on MBA91: LUKS keyfile unlock, Grok Bot autostart, narrow
  sudoers for rebuild/lab/poweroff, stay-awake during long sessions.

## If resumed later

Priority (do not re-burn falsified Linux framing unless paired with a new lever):

1. **macOS first AKS txn capture** on Air bridgeOS `23.16.16068` vs MBP `23P1072`
   (header/endpoint/OOL sizes only — no secrets).
2. Use discovery/`0xfd` **only** if a recovered Intel host→disc packing appears;
   bent’s probe is passive-only; our dual-phase listen was empty.
3. Optional: upstream issue on `jmurth1234/t2-touchid-linux` with this scoreboard.
4. **Do not** invent SBIO app opcodes, xART writes, or AKS body spray.
   EP8 SET_OOL already `EREMOTEIO`; EP12 is SSE-class (OOL ACK only — no app traffic).

## References

- Upstream: https://github.com/jmurth1234/t2-touchid-linux
- Bent bring-up / codec: https://github.com/bentsignal/t2-omarchy (`docs/touch-id.md`, `prototypes/t2sep-probe/aks-transport.py`)
- Fork branch: https://github.com/timsonner/t2-touchid-linux/tree/research/mba91-aks-ep7
- Local running log (private): `~/notes/mba-touchid-sep.md`
