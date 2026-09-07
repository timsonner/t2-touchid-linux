# MBA91 Touch ID / BridgeXPC — next steps

Branch tip context: `research/mba91-aks-ep7`. EP7 AKS mailbox stays **parked**.
Fingerprint path is **BridgeXPC** (`BRIDGEXPC_PATH.md`).

## Done recently

- Sequoia AKS extract: no pre-`0x4d` surprise (`LEVERS_2026-09-07.md`)
- Catacomb on-disk = NSKeyedArchiver → `LTFC` v10 (`CATACOMB_ONDISK.md`)
- bent BridgeXPC status corrected: past method-0; gaps are cold restore / enroll
- `en3` tcpdump: BPF blind on this Air; os_log unlock timelines are good
- Mesa ↔ bent codec crosswalk (`MESA_BENT_OPCODE_CROSSWALK.md`)

## Next (in order)

### 2. Omarchy on MBA91 — enveloped BridgeXPC smoke (read-only)

**Goal:** Multiverse → HELO (`bkremoted` / 39 / `23P6068`) → method **0**
`(0,3)` → method **1** opened.

**Do not:** enroll, `SetProtectedConfig`, ConfirmSave, sensor reset, EP7 probes.

**Success:** same activation bent already has on MBP+23P6068, proven on Air.

### 3. Read-only biometric canaries (after 2)

Order from crosswalk:

1. `0x52` bio device list  
2. `0x54` (20-byte in — bent live shape)  
3. `0x27` SKS lock (uid 501)  
4. Compare **`0x42` identity list** vs probe **`0x08` GetIdentityRecords**  
5. Later: `0x40` loadCatacomb with Private CFTL only  

### 4. Warm identity preserve A/B

macOS enroll → warm reboot Linux **without** sensor reset → identity count /
optional match. Tests bent’s cold-restore gap on this SKU.

### 5. Only if Bridge path stalls

SIP-off EP7 first-txn capture — explicit Tim OK. Not before 2–4.

## Parked

- More `pktap,en3` tcpdump on macOS Sequoia  
- Linux-native enroll / ACM policy until warm restore understood  
- Mute AKS EP7 ABI variants  
