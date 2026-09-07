# MBA91 Touch ID / BridgeXPC — next steps

Branch tip context: `research/mba91-aks-ep7`. EP7 AKS mailbox stays **parked**.
Fingerprint path is **BridgeXPC** (`BRIDGEXPC_PATH.md`).

## Done recently

- Sequoia AKS extract: no pre-`0x4d` surprise (`LEVERS_2026-09-07.md`)
- Catacomb on-disk = NSKeyedArchiver → `LTFC` v10 (`CATACOMB_ONDISK.md`)
- bent BridgeXPC status corrected: past method-0; gaps are cold restore / enroll
- `en3` tcpdump: BPF blind on this Air; os_log unlock timelines are good
- Mesa ↔ bent codec crosswalk (`MESA_BENT_OPCODE_CROSSWALK.md`)
- **Omarchy BridgeXPC smoke** on MBA91: Multiverse → HELO (`bkremoted` / 39 /
  `23P6068`) → method 0 `(0,3)` → method 1 opened (`WARM_IDENTITY_AB_2026-09-07.md`)
- **Read-only Mesa canaries** cold + **warm identity A/B**: `0x42` empty →
  count=1 uid=501 after macOS→Omarchy warm reboot; `0x54` first_byte still 0
  (`WARM_IDENTITY_AB_2026-09-07.md`)
- T2 NCM IPv6 LL pinned via NM on Omarchy (`enp116s0f1u1` /
  `fe80::aede:48ff:fe00:1122`)
- **Warm catacomb probes:** `0x42` still 1 while `0x38`/`0x3c`/`0x50` fail `0xe00002c2`; `0x3a` v1 ok 33 B; `0x54` first_byte still 0 (`WARM_CATACOMB_PROBES_2026-09-07.md`)
- **Omarchy soft-reboot A/B:** `0x42` still count=1 after Linux→Linux reboot (not power-off); `0x38`/`0x3c` still fail (`COLD_SOFT_REBOOT_AB_2026-09-07.md`)

## Next (in order)

### 1. Cold restore / accessory path

- **Full power-off A/B** (optional): does `0x42` survive true cold?
  Soft reboot already preserves (`COLD_SOFT_REBOOT_AB_2026-09-07.md`)
- Why warm `0x42` works but `0x38`/`0x3c` fail and `0x54` first_byte stays **0**
- Bounded `0x40` loadCatacomb once Private `.cat`/CFTL is on the Air (no enroll)
- Compare to bent’s cold `loadCatacomb` / no-reset identity gap

### 2. Linux-native enroll / ACM policy

Only after cold restore is understood. No ConfirmSave spray until then.

### 3. Only if Bridge path stalls

SIP-off EP7 first-txn capture — explicit Tim OK. Not before 1–2.

## Parked

- More `pktap,en3` tcpdump on macOS Sequoia  
- Mute AKS EP7 ABI variants  
- Treating `0x08` GetIdentityRecords as bent `0x42` (disproven on Omarchy)  
