# Research: MacBookAir9,1 AKS endpoint-7 bring-up

Branch: `research/mba91-aks-ep7`  
Status: **SPLIT** (updated 2026-09-06)

| Track | Status |
| --- | --- |
| Linux AKS EP7 mailbox | **PARKED** (2026-09-03/04) — mute under documented + bent-exact framing |
| macOS os_log / Mesa / BridgeXPC capture | **DONE** (2026-09-06) — cold boot + enroll + unlock; see kit docs below |
| ESP `FDRData` | **N/A** on this Air after wipe — absent; Touch ID still worked |
| Raw SEP mailbox first-txn bytes | **Still open** — os_log is not mailbox OOL capture |

Linux Touch ID remains blocked until EP7 speaks or a new bring-up lever appears.

## Hardware / software

| Item | Value |
| --- | --- |
| Machine | MacBookAir9,1 (MBA91-OMARCHY) |
| iBridge / bridgeOS | `23.16.16068` |
| Host (Linux park) | Omarchy / Arch, kernel `7.1.8-arch1-Watanare-T2-3-t2` |
| PCI SEP | `106b:1802` BAR4 (`04:00.2`) — **not** audio `04:00.3` / `106b:1803` |
| Upstream proof | MacBookPro16,2 + bridgeOS `23P1072` only |
| Host (macOS capture) | macOS 15.7.9 (24G830), boot session `2489129E-...` |
| Keybags / catacomb | Prior Linux-era exports private; fresh post-enroll export optional; **not** on this branch |

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
# Install the lab binary somewhere writable (any username):
LAB="$HOME/Private/t2-touchid/t2-sep-lab"
tools/build-t2-sep-lab.sh "$LAB"
sudo "$LAB" status
sudo "$LAB" aks --op 0x4d --ver 2 --zero-time --timeout-ms 5000
sudo "$LAB" ep0 --endpoint 12 --opcode 2 --tag 20 --size 16384 --dma in
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

1. ~~macOS os_log / Mesa / BridgeXPC enroll+unlock capture~~ — **done** (2026-09-06).
   Opcode annotations in `tools/mba91-aks-macos-capture/MESA_OPCODE_ANNOTATIONS.md`.
2. **Still open:** raw SEP **mailbox** first-txn / OOL bytes (only if still needed after os_log mining),
   or map BridgeXPC bring-up to Linux without replaying the dead EP7 ABI matrix.
3. Use discovery/`0xfd` **only** if a recovered Intel host→disc packing appears;
   bent’s probe is passive-only; our dual-phase listen was empty.
4. Optional: keybag/catacomb re-export after this enroll; upstream issue with scoreboard.
5. **Do not** invent SBIO app opcodes, xART writes, or AKS body spray.
   EP8 SET_OOL already `EREMOTEIO`; EP12 is SSE-class (OOL ACK only — no app traffic).

## References

- Upstream: https://github.com/jmurth1234/t2-touchid-linux
- Bent bring-up / codec: https://github.com/bentsignal/t2-omarchy (`docs/touch-id.md`, `prototypes/t2sep-probe/aks-transport.py`)
- Fork branch: https://github.com/timsonner/t2-touchid-linux/tree/research/mba91-aks-ep7
- Local running log (private): `~/notes/mba-touchid-sep.md`

## macOS boot / enroll capture kit

Verified on MBA91 (2026-09-06): early LaunchDaemon + unified-log stream for
AppleKeyStore / SEP / BiometricKit, plus Device Management profile for
`PRIVATE_DATA`.

Kit path: [`tools/mba91-aks-macos-capture/`](../tools/mba91-aks-macos-capture/)
(see README + CHECKLIST there).

Canonical flow: install daemon → `chmod 755` / `chmod a+r` on
`/var/log/t2-aks-capture` (so user/agent can verify without sudo) → confirm
growing `*.logstream.log` → install `EnablePrivateLogging.mobileconfig` via
System Settings → General → Device Management → confirm
`sudo log config --status` shows `PRIVATE_DATA` → cold reboot → re-chmod if
needed → enroll + lock-screen unlock → copy logs to `~/Private/` →
uninstall + remove profile.

ESP `FDRData`: **skip on this Air** (absent after wipe; not required for T2 Touch ID here).

Agent visibility on MBA91: with the Mac registered/connected, tools can read
logs as the login user after chmod; interactive sudo is not available to the
agent.

Does **not** capture raw SEP mailbox OOL bytes; that remains a later lever if
os_log sequence is insufficient.


## macOS capture — verified session (2026-09-06)

Status: **verified** on this Air (macOS 15.7.9). ESP FDR checked afterward — absent / N/A.

Kit: [`tools/mba91-aks-macos-capture/`](../tools/mba91-aks-macos-capture/) —
see [`VERIFIED_SESSION_2026-09-06.md`](../tools/mba91-aks-macos-capture/VERIFIED_SESSION_2026-09-06.md).

| Step | Result |
| --- | --- |
| Cold-boot LaunchDaemon + `log stream` | New boot UUID `2489129E-…`; stream grew (MB-class) |
| `PRIVATE_DATA` | Device Management profile (CLI `private_data:on` dead) |
| Non-root log read | Need `chmod 755` + `a+r` on `/var/log/t2-aks-capture` |
| Touch ID enroll (right index) | Captured: `biometrickitd` → Mesa / BridgeTransport / BridgeXPC |
| Lock-screen unlock | Captured: AKS lock-state; `getEnabledForUnlock→1`; catacomb `master.cat` save/confirm |
| Private log copy | `~/Private/t2-aks-capture/` (do this **before** EFI work) |

Raw logs / FDR / keybags are **not** on this branch.

Next: optional keybag/catacomb export; uninstall capture daemon + remove
profile. ESP FDR backup: **skipped** — path absent / not required (see below).


## ESP FDRData — absent / not required (2026-09-06)

Mounted `disk0s1` EFI after the verified capture session:

- `/Volumes/EFI` essentially **empty** (~844 KiB metadata only)
- **No** `EFI/APPLE/EMBEDDEDOS/FDRData` (and no `EMBEDDEDOS` on Preboot in a targeted search)
- Touch ID enroll + unlock had **already succeeded** without that tree

**Takeaway:** T1Bridge’s “preserve ESP FDR” gate does **not** apply as a hard requirement on this T2 Sequoia Air. Post-wipe macOS did not recreate the Apple EFI FDR path; biometric state observed in-capture is Mesa/BridgeXPC + catacomb (`master.cat`), not ESP FDR. Installing Omarchy/Linux will **not** regenerate Apple FDR — only dual-boot lab value.

Private capture logs remain under `~/Private/t2-aks-capture/` (not in git).

## Backup + teardown

Verified USB backup of capture logs, catacomb UUID tree, and keybags, plus
LaunchDaemon uninstall: see
[`tools/mba91-aks-macos-capture/BACKUP_AND_TEARDOWN.md`](../tools/mba91-aks-macos-capture/BACKUP_AND_TEARDOWN.md).

## Catacomb + Bridge sequence (lane B)

Mined load/save ordering from the verified macOS capture:
[`tools/mba91-aks-macos-capture/CATACOMB_BRIDGE_SEQUENCE.md`](../tools/mba91-aks-macos-capture/CATACOMB_BRIDGE_SEQUENCE.md).

Next A/B without dual-boot: cold reboot **with** enrollment present and compare
`loadCatacomb` / `restoreAndSyncTemplates` to the empty-store Phase A.

### Enrolled reboot A/B (done)

Boot `28BE7F9F-…`: `restoreAndSyncTemplates identities 1`, hash len=32, identity `7C66170E-…`. Catacomb dir UUID == Hardware UUID. Details in `CATACOMB_BRIDGE_SEQUENCE.md` Phase A′.

## EP7 wake from macOS?

See [`tools/mba91-aks-macos-capture/EP7_FROM_MACOS_NOTES.md`](../tools/mba91-aks-macos-capture/EP7_FROM_MACOS_NOTES.md).

Installed 24G830 AKS is SOURCE_VERSION `1827.120.2.703.1` (UUID `ef0c4f28-…`).
bent’s analysis already says capabilities is the first protected call; MBA91’s
failure mode is **mailbox silence**, not their framing bug. Fingerprint/Bridge
captures do not supply EP7 wake bytes.
