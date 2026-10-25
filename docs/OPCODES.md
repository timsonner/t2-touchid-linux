# Opcode reference — canonical

One table per protocol layer. Dated notes under
`tools/mba91-aks-macos-capture/` are the evidence; this file is the
index. Where the two disagree, the dated note wins and this file is
wrong.

Confidence is about **our** evidence, not about the vendor's naming:
**high** = repeated co-occurrence or a byte-exact decode, **medium** =
one clean observation, **low** = a guess worth testing.

## Read this first

There are three different number spaces. Equal hex across them is **not**
the same command.

| Layer | Carried by | Example |
| --- | --- | --- |
| BridgeXPC service envelope | `SERVICE_HEADER` (`<QIIQ`) | `0xE3FF8001` |
| Biometric command | `performCommand` / `<HHHH` header | `0x3d` |
| SEP/Catacomb state | command replies and on-disk `.cat` | state word `3`, `0x04` |

Two known traps, both recorded in
[`MESA_BENT_OPCODE_CROSSWALK.md`](../tools/mba91-aks-macos-capture/MESA_BENT_OPCODE_CROSSWALK.md):

- `0x08` (macOS `GetIdentityRecords`) and `0x42` (Linux identity list)
  do the same job with different commands. Not aliases.
- `0x27` is SKS lock state in our decode. Another tooling path uses
  `0x27` for something else; do not merge them.

## Layer 1 — BridgeXPC service envelopes

From `src/t2_enrollment_protocol.py`.

| Value | Name | Use |
| --- | --- | --- |
| `0xE3FF8000` | `BRIDGE_SERVICE_STATUS` | bridge-level status |
| `0xE3FF8001` | `SERVICE_STATUS` | enrollment status/events |
| `0xE3FF8003` | `SERVICE_ENROLLMENT_RESULT` | terminal enrollment result |
| `0xE3FF8004` | `SERVICE_STATISTICS` | counters |
| `0xE3FF800A` | `SERVICE_SKS_LOCK_STATE` | SKS lock state |
| `0xE3FF800E` | `SERVICE_ACCESSORY_AUTHORIZATION` | accessory auth |

## Layer 2 — Biometric command space

`in`/`out` are the `performCommand` payload and reply capacity, not
wire sizes. **Destructive** means it has cleared identities or Catacomb
state on this Air; do not run it as a probe.

| dec | hex | Name | ver | in | out | Conf | Destructive |
| ---: | ---: | --- | --- | --- | --- | --- | --- |
| 3 | `0x03` | enroll start | 1–2 | ACM/policy, 48 or 68 B | status | high | yes |
| 8 | `0x08` | GetIdentityRecords | — | empty | 40 B/record | high | no |
| 12 | `0x0c` | cancel / stop | 1 | empty | 0 | high | no |
| 14 | `0x0e` | enrollContinue | — | empty | 0 | high | no |
| 15 | `0x0f` | maximum capacity | 1 | empty | 4 (`5` here) | high | no |
| 17 | `0x11` | getNodeTopology | — | ~20 B | 3060 B | high | no |
| 33 | `0x21` | creation reference | 1 | option `0x100` | status | medium | yes |
| 39 | `0x27` | SKS lock state | 0–2 | uid u32 | 4 | high | no |
| 40 | `0x28` | biometrickitd info | 1 | empty | 23 | high | no |
| 44 | `0x2c` | accessory/bridge probe | — | — | — | low | no |
| 46 | `0x2e` | protected config | 1 | uid u32 | 32 | medium | no |
| 48 | `0x30` | getEnabledForUnlock | — | — | flag | high | no |
| 56 | `0x38` | Catacomb UUID | 0 | uid u32 | 16 | high | no |
| 58 | `0x3a` | Catacomb hash | 1 | uid u32 | 33 (status + 32) | high presence, low meaning | no |
| 60 | `0x3c` | Catacomb state list | 0 | empty | `<II>` records | high | no |
| 61 | `0x3d` | PrepareSaveCatacomb | 2 | 24 B context | 4 (blob size) | high | yes |
| 62 | `0x3e` | CompleteSaveCatacomb | 2 | 24 B context | `LTFC` blob | high | yes |
| 63 | `0x3f` | ConfirmSaveCatacomb | 2 | 24 B context | 0 | high | yes |
| 64 | `0x40` | LoadCatacomb | 1 | opaque `LTFC` blob | 0 | medium | yes |
| 65 | `0x41` | free capacity | 1 | uid u32 | 4 (`2` here) | high | no |
| 66 | `0x42` | per-user identity list | — | uid u32 | N × 20 B | high | no |
| 72 | `0x48` | delete user's identities | — | uid u32 | status | high | yes |
| 74 | `0x4a` | match path | — | — | — | medium | no |
| 76 | `0x4c` | bridgeServiceCheck | — | — | — | low | no |
| 80 | `0x50` | Catacomb group state | 0 | empty | 56 B × 64 | medium | no |
| 81 | `0x51` | global identity list | — | empty | N × 40 B | medium | no |
| 82 | `0x52` | GetBioDeviceList A | 1 | empty | ≤ 264 (6 × 44) | high | no |
| 84 | `0x54` | GetBioDeviceList B / I/O | — | ~20 B | ~83 B | high | no |

The 24-byte Catacomb context is `<II16s>`: uid, group, zero UUID.
`0x3d` returns the exact blob length that `0x3e` must return, and
`0x3f` commits. The full pipeline is in
[`CATACOMB_BRIDGE_SEQUENCE.md`](../tools/mba91-aks-macos-capture/CATACOMB_BRIDGE_SEQUENCE.md).

## Layer 3 — Catacomb and identity shapes

| Signal | Shape | Meaning |
| --- | --- | --- |
| `0x3c` record | `<II>` uid, state | `0xFFFFFFFF` = master; state `3` = present; `0x04` = needs save |
| `0x38` status `22` | `0x16` | no user component for that uid |
| `0x3a` reply | 33 B | byte 0 status, 32 B SEP state; **not** SHA-256 of a file |
| `0x42` record | `<I16s>` | uid + identity UUID, 20 B |
| `0x08` record | 40 B | uid + UUID + trailer |
| `0x41` / `0x0f` | u32 | free slots / capacity (this Air: 2 / 5) |
| on-disk user component | `bplist00` | `NSKeyedArchiver`, six top-level keys |
| secure blob | `LTFC` | 33-byte header (magic, version 10, uid, 21 reserved) + sealed payload |

The blob is **stateful**: the same identity re-seals to a different
length and hash. It cannot be computed or edited into agreement —
see [`CATACOMB_BLOB_STATEFUL_2026-10-24.md`](../tools/mba91-aks-macos-capture/CATACOMB_BLOB_STATEFUL_2026-10-24.md).

## Layer 4 — Enrollment statuses

From `src/t2_enrollment_protocol.py` and the 24G830 selector notes.

| Status | Meaning |
| --- | --- |
| 100–355 | progress; `enrollContinue` required |
| 60 / 61 | state changed, operation still running |
| 63 / 64 | finger present / removed |
| 51, 58, 62, 65, 80, 99, 502 | operation finished |
| 0–50, 52–57, 59, 69, 71–73, 75–77, 79, 81–84, 89–92, 94–97, 356–500, 503+ | exact no-op domain |
| `0xE3FF8001` ordinal 501 | user-501 status event |

## Sequences

```text
boot     0x52 -> 0x54 -> load user component -> 0x38/0x3a
         -> restoreAndSyncTemplates identities N
enroll   0x03 -> 0x0e (repeat) -> 0x3d -> 0x3e -> 0x3f
unlock   0x30 -> 0x27 -> 0x52/0x54 -> match (0x54, 0x4a, 0x0c)
         -> 0x3c -> 0x3d -> 0x3e -> 0x3f -> 0x38
```

## Evidence map

| Source | What it is |
| --- | --- |
| [`MESA_BENT_OPCODE_CROSSWALK.md`](../tools/mba91-aks-macos-capture/MESA_BENT_OPCODE_CROSSWALK.md) | our capture vs the bent codec, with match tags |
| [`MESA_OPCODE_ANNOTATIONS.md`](../tools/mba91-aks-macos-capture/MESA_OPCODE_ANNOTATIONS.md) | histogram and caller co-occurrence |
| [`MESA_BRIDGE_OPCODE_NOTES.md`](../tools/mba91-aks-macos-capture/MESA_BRIDGE_OPCODE_NOTES.md) | mining method and session histogram |
| [`BRIDGE_GETIDENTITY_DECODE.md`](../tools/mba91-aks-macos-capture/BRIDGE_GETIDENTITY_DECODE.md) | `0x08` record layout |
| [`CATACOMB_BRIDGE_SEQUENCE.md`](../tools/mba91-aks-macos-capture/CATACOMB_BRIDGE_SEQUENCE.md) | load/save timeline |
| [`ACCESSORY_PRIVATE_OPCODES_2026-09-07.md`](../tools/mba91-aks-macos-capture/ACCESSORY_PRIVATE_OPCODES_2026-09-07.md) | `0x52`/`0x54` accessory shapes |
| `src/bridge-xpc-probe.py` | read-only inventory opcodes |
| `src/t2_*_protocol.py` | framing, constants, fail-closed parsers |
