# BridgeXPC biometric path (MBA91 exploration map)

Date: 2026-09-07. Parallel to parked Linux **AKS EP7** mute.
Host facts below are from live MacBookAir9,1 / macOS **15.7.9 (24G830)** unless
noted as bent’s Linux work.

## Why this avenue

Fingerprint on Intel T2 macOS does **not** ride the Linux AKS mailbox (EP7).
It rides **BridgeXPC** from `biometrickitd` into bridgeOS `bkremoted`, then Mesa
opcodes. Linux can speak that stack over the T2 NCM IPv6 link (bent already does
on MBP + 23P6068). MBA91 still needs to prove the same path on this Air,
then solve cold catacomb / enroll policy.

## Stack

```text
Host userspace
  biometrickitd
    RemoteServiceDiscovery (Multiverse directory)
    BridgeXPC.framework (v39 on MBA91 + bent)
        │
        │  TCP / IPv6 link-local on T2 NCM
        ▼
  fe80::aede:48ff:fe33:4455%<t2-iface>   # peer (bent recovered)
  host LL on MBA91: fe80::aede:48ff:fe00:1122%en3
        │
        ▼
bridgeOS  bkremoted
  HELO advertises process + OS build + BridgeXPC version
  methods 0..12 (see below); method 3 = PERFORM_COMMAND
        │
        ▼
  Mesa / sensor path inside bridgeOS  (opcodes 8, 17, 62, 63, …)
  (not Linux EP7 AppleKeyStore framing)
```

## MBA91 live inventory (2026-09-07)

| Item | Value |
| --- | --- |
| T2 NCM iface | **`en3`** |
| MAC | `ac:de:48:00:11:22` |
| Host inet6 | `fe80::aede:48ff:fe00:1122%en3` |
| Link status | UP / active / 100baseTX |
| BridgeXPC CFBundleVersion | **39** (stub framework; binary in dyld cache) |
| `biometrickitd` | running (`--launchd`); SHA-256 `161c88b8…e9d37c` |
| Linked | BridgeXPC **39.0.0**, RemoteServiceDiscovery **172.100.9** |
| Service names in binary | `com.apple.eos.BiometricKit`, `.ta` variant |
| bridgeOS build (iBridge) | **23P6068** (same string bent’s HELO saw) |

## BridgeXPC wire (recovered codec)

16-byte little-endian header (`bridge-protocol.py`):

| Offset | Size | Field |
| --- | --- | --- |
| 0 | 2 | magic **`0xb892`** |
| 2 | 2 | protocol version **1** |
| 4 | 4 | kind: 0 noop / **1 HELO JSON** / **2 binary-plist message** |
| 8 | 8 | body length |

Inner biometric request (inside method-3 payload) starts with magic **`0x4d42`**
(`MB`) + command/version/value (`<HHHH`) — this is the Mesa opcode carrier we
already mined from os_log (GetIdentityRecords=8, topology=17, ConfirmSave=63, …).

### Method table (BridgeXPC / BiometricKitBridge)

| # | Name (bent codec) |
| --- | --- |
| 0 | `GET_BRIDGE_VERSION` / `getBridgeVersion:` |
| 1 | `GET_SERVICE_OPENED` |
| 2 | `GET_SYSTEM_BOOT_TIME` |
| **3** | **`PERFORM_COMMAND`** ← actual Mesa ops |
| 4 | `SET_IOREGISTRY_PROPERTY` |
| 5 | `CALIBRATION_DATA_FROM_EEPROM` |
| 6 | `MACH_CONTINUOUS_TIME` |
| 7 | `GET_MACH_TIMEBASE_INFO` |
| 8 | `GET_OS_VERSION` |
| 10 | `SET_BRIDGE_CLIENT_VERSION` |
| 11 | `CALIBRATION_DATA_FROM_FDR` |
| 12 | `SET_OS_TRANSACTION_RETAINED` |

Method **3** request shape: `[3, command, NSData, output_capacity]` as bplist.
`biometric_perform_request` wraps the `0x4d42` inner header as Bridge command **0**.

## Ports

- Catalina static table: `kEOSServiceBiometricKit` → host port **52032**.
- Current macOS: RSD Multiverse advertises a **boot-dynamic** port (bent
  observed **49165** on one boot). Always rediscover; do not hardcode forever.

## Transport envelope (easy to miss)

Method messages are **not** bare `[method, …]` on the wire. bent recovered:

- Request: `[1, false, replyUUID, logicalMessage]`
- Reply: `[1, true, sameUUID, logicalReply]`
- Bare `[0]` parses as bplist but `handleEnvelope:` **silently** ignores it
  (looked like “method 0 mute” until fixed).

Directory: Multiverse TCP **59602**; BiometricKit port is **boot-dynamic**
(bent saw 49165 / 49223). Do not pin Catalina **52032**. Do not send
`RSDCheckin` on the BiometricKit socket (RST).

## Where bent actually is (Linux) — corrected 2026-09-07

**Past** HELO / method-0 activation. On Omarchy (MBP + bridgeOS **23P6068**):

1. Multiverse → server-first HELO (`bkremoted`, BridgeXPC **39**, **23P6068**)
2. Enveloped method **0** → `(status=0, version=3)`
3. Method **1** → service opened
4. Method **3** `performCommand` with inner `0x4d42` biometric header — many
   opcodes live; warm match + fprintd verify-match / verify-no-match landed

**Current bent BridgeXPC gaps** (fingerprint UX):

- **Cold-boot identity restore** — warm match needs non-reset identity state;
  Linux sensor reset without `loadCatacomb` clears live identities
- **Linux-native enrollment** — ACM `TouchIdEnrollment` policy vs real login
  keybag session still blocks / returns policy errors; catacomb persist across
  cold Linux boot unproven

An older MBA91 note that said “method-0 gap; method-3 gated” was **stale** —
do not plan MBA91 work as if activation were still the blocker.

**MBA91 implication:** same BridgeXPC 39 + **23P6068** means we should
**reproduce bent’s working enveloped path** on this Air (SKU `J230kAP`), then
lean on our Mesa/`loadCatacomb` evidence for cold restore — not rediscover HELO.

## What MBA91 already contributes

From capture-kit Mesa/os_log work (see sibling docs):

- Cold-boot / enroll / unlock **opcode timelines** (exactly the cold-restore
  story bent still needs)
- `loadCatacomb` vs save cluster (`60/61/62/63`)
- Opcode **8** GetIdentityRecords decode
- On-disk catacomb = NSKeyedArchiver → `LTFC` v10 (`CATACOMB_ONDISK.md`)

These are first-class inputs for bent’s **current** gap, not “later.”

## Ranked next experiments (MBA91)

1. **macOS `en3` pcap** (optional Sequoia transcript) — lock→unlock or
   `killall biometrickitd`. Confirms Air’s enveloped HELO/method-0/3 sizes vs
   bent. See `BRIDGEXPC_CAPTURE.md`. Not required to “invent” method 0.
2. **Offline opcode↔codec table** — map MBA91 Mesa 8/17/63/82/84 to bent
   `biometric-command` shapes/sizes (no live writes).
3. **Omarchy on MBA91: Multiverse + enveloped method 0/1 only** — prove Air
   Linux gets `(0,3)` / opened like bent. Read-only Bridge; no enroll.
4. **Warm identity preserve A/B** — macOS enroll → warm reboot Linux **without**
   sensor reset; check identity list / optional match.
5. **Read-only `loadCatacomb`-class probes** after Private bags present — before
   native enroll.
6. Keep AKS EP7 parked; SIP-off EP7 capture only if Bridge fingerprint track
   stalls on policy/keybag with Tim’s explicit OK.

## Private artifacts

`$HOME/Private/t2-bridgexpc-research/` — iface inventory, hashes (no pcaps yet).

## Capture kit

See [BRIDGEXPC_CAPTURE.md](BRIDGEXPC_CAPTURE.md) / `capture-en3-bridgexpc.sh`.
