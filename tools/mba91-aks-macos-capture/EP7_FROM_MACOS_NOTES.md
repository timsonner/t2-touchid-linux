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
| AKS fileset content SHA-256 (naive slice) | `0bf4b320e75c76b6b8782316b37bfc24075b757ef52afe14722483d93bc426ab` |
| Bundle Info.plist | `CFBundleShortVersionString=2`, SDK `macosx15.7.internal` / `24G823` |
| Related filesets present | `AppleSEPManager`, `AppleFDEKeyStore`, … |

Also present in the same KC (prelinked / shared string tables — **not** a clean
standalone AKS Mach-O extract with stock `nm`): symbol **names**
`init_sep_endpoint`, `_ipc_get_capabilities`, `sep_action`, `_gen_ipc_header`,
`_payload_hash`.

Naive “slice to next fileset fileoff” produces a **truncated** Mach-O (segment
fileoffs point into the wider KC). Full disassembly needs a proper KC/fileset
tool (`ipsw`, etc.), not committed here. Binary stays under `$HOME/Private`
only.

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
| Example host | MBP16,2 + bridgeOS `23P1072` (their proof) | MacBookAir9,1 + iBridge **23.16.16068** |
| macOS AKS sampled | 25G83 / UUID `12144241-…` / srcver 55 | 24G830 / UUID `ef0c4f28-…` / srcver **1827.120.2.703.1** |

So “copy init_sep_endpoint order from macOS” is **already what Linux tried**.
The open gap is **why this SEP/bridgeOS never answers EP7**, not a missing
pre-`0x4d` userspace dance visible in biometric logs.

## What would still move EP7

1. **Proper KC extract + disasm** of this 1827.x `AppleKeyStore` vs Linux codec
   (confirm Sequoia didn’t add a real prerequisite bent’s older note missed).
2. **bridgeOS / SEP firmware** side: endpoint bring-up, xART, or SKU differences
   vs MBP16,2 — needs firmware/Bridge instrumentation, not Touch ID os_log.
3. **Raw first-txn capture** under macOS (hypervisor / custom kext / SEP trace) —
   only path to actual EP7 mailbox bytes; os_log will not provide them.
4. **Non-EP7 Linux path**: BridgeXPC-class userspace to bridgeOS for biometrics
   (parallel to mute AKS).

## Do not expect

- Fingerprint enroll/unlock captures to reveal EP7 wake.
- Keybags/catacomb alone to unmute EP7.
- Replaying Mesa opcodes 8/17/62 as mailbox frames.

## Private artifacts (not in git)

`$HOME/Private/t2-aks-research/` — KC hash, FINDINGS.txt, partial AKS slice.
