# Can we wake Linux EP7 from macOS? (MBA91 notes)

Date: 2026-09-06 / 2026-09-07. Host: MacBookAir9,1, macOS **15.7.9 (24G830)**.

## Short answer

**Unlikely via fingerprint / Bridge traffic.** EP7 silence on Linux is an
AppleKeyStore↔SEP **mailbox** failure mode. macOS biometrics we captured are
BridgeXPC↔Mesa inside `biometrickitd`.

macOS **does** run AppleKeyStore (kernel sels, `applekeystored`, unlock
notifications). That proves AKS is alive on this hardware under macOS — it does
**not** hand us EP7 wake bytes in os_log.

## What we recovered from the installed Boot KC (read-only)

Path: `/System/Library/KernelCollections/BootKernelExtensions.kc`

| Field | Value |
| --- | --- |
| KC UUID (otool) | `8275DA3D-3203-E636-1FB2-59F160344AAA` |
| KC SHA-256 | `7ac1232f4530b8b9a7b70f43a3b92b94e93c5fb6aa2988bbaa666ccd7e265dc0` |
| `com.apple.driver.AppleKeyStore` fileset fileoff | `0x18e9000` |
| AKS LC_UUID | `ef0c4f28-1c68-39be-b1f4-4f2e55b11c7c` |
| AKS LC_SOURCE_VERSION | **1827.120.2.703.1** |
| Bundle Info.plist | `CFBundleShortVersionString=2`, SDK `macosx15.7.internal` / `24G823` |
| Related filesets present | `AppleSEPManager`, `AppleFDEKeyStore`, … |

### Proper extract (2026-09-07)

Used `ipsw kernel extract` (v3.1.713) → standalone Mach-O **AppleKeyStore**
(847280 bytes). Binary stays under `$HOME/Private/t2-aks-research/kc/extracted/`
only (not in git).

`otool` on `AppleKeyStore::init_sep_endpoint` (Sequoia **1827.120.2.703.1**):

1. Builds transport callback args, then **`callq __ipc_get_capabilities`** with
   header version **1** (`movl $0x1, %edx`).
2. Failure → `msg_header_set_negotiated_version(1)` (“failed to negotiate,
   defaulting to v1”).
3. Success → `min(remote_version, 2)` via `msg_header_set_negotiated_version`.
4. **`AppleKeyStore::set_env(false)`** (`xorl %esi, %esi` then call).
5. `add_class_f_entropy_to_kernel_prng()`.

`__ipc_get_capabilities` ends the setup with **`pushq $0x4d; popq %rsi`** then
an indirect call through the transport callback — selector **0x4d** unchanged.

**Consequence:** Sequoia did **not** add a hidden pre-`0x4d` prerequisite.
MBA91 EP7 mute is still not explained by AKS init order.

## Bent handoff vs this Air (important)

bent’s `macos-aks-current-host-handoff` (build **25G83**) concluded:

1. Linux protected-header / `_payload_hash` ABI already matches installed AKS.
2. `init_sep_endpoint` → **`_ipc_get_capabilities` (0x4d)** immediately → then
   `set_env`. **No** hidden IPC session/nonce/keybag/ACM step before capabilities.
3. Mailbox envelope `0x00014d07` / reply bit placement matches.
4. On **their** T2 they **got replies**; the bug was response **framing**
   (v1 declared length `0x48` → 92-byte reply), not mute timeout.

MBA91 Linux scoreboard (this fork): EP7 **`ETIMEDOUT`**, `ool_out_nonzero=0`,
including bent-exact wires. Transport below AKS is healthy (EP0/MSI/startCPU/ACM).

| | bent (working mailbox) | MBA91 (this research) |
| --- | --- | --- |
| Symptom | Replies; parse/framing | **No reply** |
| Example host | MBP16,2 + bridgeOS `23P1072` (their early proof) | MacBookAir9,1 + iBridge **23.16.16068** |
| bridgeOS build string | bent later BridgeXPC HELO: **`23P6068`** | system_profiler: **`23P6068`** (same) |
| bridge-model | (see bent notes) | **`J230kAP`** |
| macOS AKS sampled | 25G83 / UUID `12144241-…` / srcver 55 | 24G830 / UUID `ef0c4f28-…` / srcver **1827.120.2.703.1** |

So “copy init_sep_endpoint order from macOS” is **already what Linux tried**.
The open gap is **why this SEP/bridgeOS never answers EP7**, not a missing
pre-`0x4d` userspace dance visible in biometric logs.

## Lever results (2026-09-07)

| Lever | Status | Result |
| --- | --- | --- |
| Proper KC extract + `init_sep_endpoint` disasm | **Done** | Same order as bent: `0x4d` then `set_env(false)`. No new pre-cap gate. |
| Offline catacomb / CFTL parse | **Done** | See `CATACOMB_ONDISK.md`. Metadata plaintext; `LTFC` body SEP-sealed. |
| bridgeOS / SKU delta | **Partial** | Firmware build string **`23P6068` matches** bent’s BridgeXPC HELO. Mute is not “wrong marketing bridgeOS string.” Board is still **J230kAP / MBA91** vs bent’s MBP proof host. |
| BridgeXPC Linux (non-EP7) | **Mapped** | bent already reaches `bkremoted` HELO on **`23P6068`**; stuck on activation / first method bytes (method 3 gated). Parallel to mute EP7 — see bent `docs/touch-id.md`. |
| Raw first-txn under macOS | **Blocked / optional** | Needs SIP-off custom kext, hypervisor SEP trace, or equivalent. os_log cannot supply mailbox bytes. Not started without Tim expanding scope. |

## What would still move EP7

1. ~~Proper KC extract + disasm~~ → **closed** (no Sequoia pre-`0x4d` surprise).
2. **SKU / SEP bring-up** beyond build string (J230kAP vs MBP; xART; endpoint map) —
   firmware/Bridge instrumentation, not Touch ID os_log.
3. **Raw first-txn capture** under macOS (hypervisor / custom kext / SEP trace) —
   only path to actual EP7 mailbox bytes; requires explicit scope expand.
4. **Non-EP7 Linux path**: finish bent’s BridgeXPC activation gap (exact macOS
   outbound HELO/method-0 / remoted handoff), then Mesa/SBIO — independent of mute AKS.

## Do not expect

- Fingerprint enroll/unlock captures to reveal EP7 wake.
- Keybags/catacomb alone to unmute EP7.
- Replaying Mesa opcodes 8/17/62 as mailbox frames.

## Private artifacts (not in git)

`$HOME/Private/t2-aks-research/` — KC copy, `ipsw` extract, FINDINGS.txt, catacomb/CFTL extracts.
