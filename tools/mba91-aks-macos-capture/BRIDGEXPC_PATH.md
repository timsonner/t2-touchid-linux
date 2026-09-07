# BridgeXPC biometric path (MBA91 exploration map)

Date: 2026-09-07. Parallel to parked Linux **AKS EP7** mute.
Host facts below are from live MacBookAir9,1 / macOS **15.7.9 (24G830)** unless
noted as bent’s Linux work.

## Why this avenue

Fingerprint on Intel T2 macOS does **not** ride the Linux AKS mailbox (EP7).
It rides **BridgeXPC** from `biometrickitd` into bridgeOS `bkremoted`, then Mesa
opcodes. Linux can speak that stack over the T2 NCM IPv6 link once the
handshake/activation matches current macOS.

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

## Where bent is stuck (Linux)

1. Multiverse directory works; BiometricKit service advertised.
2. TCP connect to service port → **server-first HELO** validates as `bkremoted`,
   BridgeXPC **39**, bridgeOS **`23P6068`**.
3. Reconstructed client HELO + **method 0** (`getBridgeVersion`) → peer ACKs TCP
   but **no application reply** (bounded waits). Method **3** is intentionally
   gated until that handoff is byte-exact.
4. Ruled out (bent): wrong TCP delivery, HELO/method barrier ordering alone,
   stale directory port, Catalina-fixed 52032 without discovery, speculative
   `RSDCheckin` prefix (caused RST when mis-ordered).

**MBA91 implication:** same BridgeXPC 39 + same `23P6068` build string means this
Air is a good place to capture the **missing macOS outbound transcript** on
`en3`, not a SKU dead-end for the HELO layer.

## What MBA91 already contributes above the handshake

From capture-kit Mesa/os_log work (see sibling docs):

- Cold-boot / enroll / unlock **opcode timelines**
- `loadCatacomb` vs save cluster (`60/61/62/63`)
- Opcode **8** GetIdentityRecords decode
- On-disk catacomb = NSKeyedArchiver → `LTFC` v10 (`CATACOMB_ONDISK.md`)

Those matter **after** method 3 works. They do not fix method 0 silence.

## Ranked next experiments

1. **macOS `en3` pcap during biometrickitd traffic** (lock→unlock or
   `killall biometrickitd` + wait for relaunch). Private only. Sanitize with
   bent’s `sanitize-macos-enrollment-pcap.py` (or a thin MBA91 wrapper) to a
   credential-free BridgeXPC transcript. **Success:** byte-exact client HELO +
   method-0 (+ any remoted handoff) frames. Needs one sudo/tcpdump auth prompt.
2. **Compare transcript to Linux codec** (`bridge-protocol.py` /
   `macos-bridge-wire-compare.py`) — fix HELO/method-0 encoding only.
3. **Re-run Linux probe on Omarchy** (when MBA91 is back on Linux or another T2
   host) with the corrected first-write sequence; only then enable method 3 /
   Mesa opcode 8 canaries.
4. Do **not** spray method-3 / SBIO guesses while method 0 is silent.
5. Do **not** confuse this with AKS EP7 unmute — keep EP7 parked.

## Private artifacts

`$HOME/Private/t2-bridgexpc-research/` — iface inventory, hashes (no pcaps yet).
