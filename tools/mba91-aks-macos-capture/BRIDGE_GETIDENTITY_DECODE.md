# Bridge/Mesa payload decode: GetIdentityRecords (+ neighbors)

Mined from MBA91 captures (enroll `2489129E` raw timeline + enrolled reboot
`28BE7F9F` logstream). os_log truncates long hex with `...`; fields below are
only what is grounded in logs + known identity metadata.

## Command mapping (high confidence)

| Mesa `performCommand` opcode | API / log name | Notes |
| --- | --- | --- |
| **8** | **`performGetIdentityRecordsCommand`** | Request: version=1, inValue=0, inSize=0. Reply extracted as 40-byte record(s). |
| **17** | `getNodeTopologyForIdentity` | inSize=20 (identity ref); reply **3060** bytes |
| **39** | `performGetSKSLockStateCommand` | Reply 4 bytes `0x10000000` (BeforeFirstUnlock-ish) |
| **60/61/62/63** | catacomb prepare/complete/confirm | **62** reply can be large **CFTL** blob |

Evidence (enroll, 21:10:25.355):

```text
performCommand:version:...: 8 1 0 ...
MCDMExtractMessageData 3825172483 (0xe3ff8003) ordinal=2 len=40
  bytes = 0xf5010000 7c66170e 39d344eb 8def9173 ... 00000000 00000000
performGetIdentityRecordsCommand: -> 0   # (seen on enrolled reboot path)
```

Same 40-byte pattern on enrolled reboot BridgeConnection reply immediately before
`performGetIdentityRecordsCommand: -> 0`.

## 40-byte identity record (partial layout)

Logged identity: `userID:501`, UUID `7C66170E-39D3-44EB-8DEF-9173BF839790`,
accessory `type:1 uuid:0 flags:0x6`.

| Offset | Bytes (hex) | Decode |
| --- | --- | --- |
| 0–3 | `f5 01 00 00` | **uid 501** little-endian (`0x1f5`) — **confirmed** |
| 4–15 | `7c 66 17 0e 39 d3 44 eb 8d ef 91 73` | UUID bytes 0–11 big-endian — **confirmed** |
| 16–19 | `(ellipsis)` | Almost certainly UUID bytes 12–15 `bf 83 97 90` |
| 20–31 | `(ellipsis)` | Accessory / flags / group — **not fully dumped** |
| 32–39 | `00 00 00 00 00 00 00 00` | Trailing zeros — **confirmed** |

Reconstructed best-effort (UUID complete; trailer zero-padded — **do not treat
offsets 20–31 as proven**):

```text
f5 01 00 00  7c 66 17 0e  39 d3 44 eb  8d ef 91 73
bf 83 97 90  ?? ?? ?? ??  ?? ?? ?? ??  00 00 00 00
00 00 00 00
```

Related tiny status extracts (same enroll second), also uid-prefixed:

```text
MCDMExtract 0xe3ff800a len=6: f5010000 0400
MCDMExtract 0xe3ff800a len=6: f5010000 0002
MCDMExtract 0xe3ff800a len=6: f5010000 0802
```

These sit next to `getEnabledForUnlock` / SKS chatter — likely per-user flag
words, not full identity records.

## Neighbor: getNodeTopology (opcode 17)

```text
performCommand:version:...: 17 1 0 <20-byte in> ...
BridgeConnection reply length=3060
  head: f4 0b 03 00  2c 01 06 00  ff ff 00 00  ff ff 00 00 ...
getNodeTopologyForIdentity: -> {length=3060, ...}
```

`0x0bf4` = 3060 decimal — first LE u16/u32 may be length/count. Rest is opaque
template/topology blob (not decoded here).

## Neighbor: CompleteSave outBuffer (opcode 62)

```text
BridgeConnection reply length=11354
  head: 4c 54 46 43  0a 00 00 00  f5 01 00 00  00 00 00 00 ...
```

- `4C 54 46 43` = ASCII `LTFC` = FourCC **`CFTL`** as little-endian u32
- next u32 `0x0000000a` = 10 (version/count?)
- next u32 `0x000001f5` = **uid 501** again
- payload is the catacomb component blob written via `prepare/` then ConfirmSave (63)

This is the on-wire shape of what lands in `user_000001f5.cat` / `master.cat`,
not an AKS EP7 mailbox frame.

## Enrolled-reboot GetIdentity sequence (compressed)

```text
Bridge v3 → MSR/calibration → loadCatacomb Master+User
  unarchive user_000001f5.cat → addIdentityObjects (7C66170E-…)
  → Mesa opcode 8 GetIdentityRecords → 40-byte record (uid+UUID…)
  → opcode 17 getNodeTopology (when clients ask)
  → restoreAndSyncTemplates identities 1
  → bridgeBootUUID / serviceMatch
```

## Limits / next instruments

1. os_log **always truncates** mid-buffer — need dtrace/frida/BridgeXPC dump or
   `log` stream with a custom os_log that prints full NSData to recover bytes 16–31.
2. Opcode **8** should be promoted to **high** in Mesa annotations (was unmarked /
   low).
3. Still **not** Linux EP7 AKS framing — these are BridgeXPC↔Mesa userspace
   payloads inside `biometrickitd`.
