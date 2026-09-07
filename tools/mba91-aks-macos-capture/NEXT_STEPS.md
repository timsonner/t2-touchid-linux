# MBA91 Touch ID / BridgeXPC — next steps

Branch: `research/mba91-aks-ep7`. Host: MacBookAir9,1 · Omarchy `MBA19-OMARCHY` ·
bridgeOS **23P6068** · BridgeXPC **39**.  
**EP7 AKS stays parked.** Fingerprint path = **BridgeXPC** (`BRIDGEXPC_PATH.md`).

## What we know (2026-09-07)

| Fact | Evidence |
| --- | --- |
| Multiverse → HELO → method 0 `(0,3)` → method 1 opened | `WARM_IDENTITY_AB_2026-09-07.md` |
| After macOS enroll once, `0x42` shows uid 501 | warm A/B |
| `0x42` **survives soft reboot and true power-off** without Linux `loadCatacomb` | `COLD_SOFT_REBOOT_AB_2026-09-07.md`, `COLD_POWEROFF_AB_2026-09-07.md` |
| `0x38` / `0x3c` / `0x50` still fail `0xe00002c2` while `0x42` is non-empty | `WARM_CATACOMB_PROBES_2026-09-07.md` |
| `0x54` accessory-present first_byte stays **0** | all canary runs |
| `0x08` ≠ bent `0x42` | Omarchy canaries |
| USB `.cat` → LTFC extract is valid on-disk shape | Private `cftl-extract/` |
| No-reset `0x40` load → **status 257**, no canary change | `LOAD_CATACOMB_0x40_2026-09-07.md` |

**Reframe:** on this Air, bent’s “cold restore” is **not** “`0x42` goes empty after
power loss.” The open Bridge gaps are **store APIs / accessory / `0x40` preflight**
(and later Linux-native enroll).

## Next (in order)

### 1. Supervised reset-then-`0x40` A/B  ← **do this next**

Destructive by design. Expect `0x42` empty after sensor reset; then load Private
LTFC (master → user) and re-check canaries.

**Success criteria (public-safe):**

1. After reset: `0x42` count=0 (or fail), readiness/provisioning still sane  
2. `0x40` master then user → **status 0** (not 257)  
3. After load: `0x42` count≥1 uid 501; note `0x38`/`0x3c`/`0x54` first_byte  

**Do not:** enroll, ConfirmSave, `SetProtectedConfig`, EP7.  
**Script basis:** bent `external-catacomb-load-probe` preflight (reset + cancel +
calibration gate) + our Private LTFC paths — adapt locally, keep blobs out of git.

### 2. Offline: decode status **257**

Parallel / quick: map `257` (`0x101`) in bent/macOS notes vs BK error tables.
Doesn’t block (1), but write a one-liner into `LOAD_CATACOMB_0x40_2026-09-07.md`
when found.

### 3. After a successful load

- Re-check `0x54` first_byte and store APIs  
- Optional **warm match** canary (read-only path only)  
- Only then consider Linux-native enroll / ACM policy  

### 4. Only if Bridge path stalls

SIP-off EP7 first-txn — explicit Tim OK. Not before 1–3.

## Parked

- Mute AKS EP7 ABI variants  
- More Sequoia `pktap,en3` tcpdump  
- Treating `0x08` as `0x42`  
- Assuming power-off clears `0x42` on MBA91 (disproven once enrolled)  

## Doc index (this arc)

| Note | Topic |
| --- | --- |
| `WARM_IDENTITY_AB_2026-09-07.md` | smoke + warm A/B |
| `WARM_CATACOMB_PROBES_2026-09-07.md` | store API split |
| `COLD_SOFT_REBOOT_AB_2026-09-07.md` | soft reboot preserve |
| `COLD_POWEROFF_AB_2026-09-07.md` | true cold preserve |
| `LOAD_CATACOMB_0x40_2026-09-07.md` | no-reset 257 |
| `MESA_BENT_OPCODE_CROSSWALK.md` | opcode table |
| `MBA91_T2_NCM_LL.md` (local Air) | NM LL pin recipe |
