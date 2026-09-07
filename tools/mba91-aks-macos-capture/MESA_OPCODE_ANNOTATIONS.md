# Mesa `performCommand` opcode annotations (MBA91)

Source: private cold-boot capture `2489129E-…` (2026-09-06 MT), mined from
`biometrickitd` `Daemon-Mesa` / BridgeXPC logs.

**Method:** for each `performCommand:version:inValue:… <opcode> …` call site,
look at the preceding ~12 log lines for the highest-priority wrapper
(`performGetBioDeviceListCommand`, `enrollContinue`, `performConfirmSaveCatacombCommand`,
etc.). Verify with co-occurrence counts. Cross-check decimal↔hex against public
RE notes where they claim the **same** Mesa command space.

**Caution:** other writeups sometimes use a different BridgeXPC/`biometric_command`
opcode space. Equal hex values are **not** automatically the same command.
Confidence = how well *our* capture supports the label.

## Verified mapping (this capture)

| dec | hex | n | Annotation | Confidence | Verification |
| --- | --- | ---: | --- | --- | --- |
| 82 | `0x52` | 21 | **GetBioDeviceList phase A** (after `getCommProtocolVersion`) | **high** | 21/21 near `performGetBioDeviceListCommand`; 15/21 followed within ~20 lines by `84` |
| 84 | `0x54` | 38 | **GetBioDeviceList phase B** / general Mesa I/O during **match** | **high** | 20× device-list + 15× match; public QuickTouch notes Tier‑1 carrier `0x54` for biometric payloads — consistent with heavy use as message/data path |
| 12 | `0x0c` | 15 | **Cancel / stop bio operation** | **high** | 13/15 near `cancel`; header has `performCancelCommand` |
| 14 | `0x0e` | 12 | **Enroll continue / enroll path** | **high** | 12/12 near `enrollContinue` |
| 48 | `0x30` | 5 | **getEnabledForUnlock-related** | **high** | 5/5 near `getEnabledForUnlock` |
| 17 | `0x11` | 1 | **getNodeTopology** | **high** | 1/1 near `getNodeTopology` |
| 63 | `0x3f` | 8 | **ConfirmSaveCatacomb** wire command | **high** | **8/8** near `performConfirmSaveCatacombCommand` |
| 56 | `0x38` | 4 | **Catacomb confirm/save family** | **medium** | 4/4 near ConfirmSaveCatacomb; public note cites `0x38` in a catacomb-related command space (treat as supportive, not proof) |
| 60 | `0x3c` | 3 | **saveCatacomb / catacomb-state family** | **medium** | 2/3 near `saveCatacombForComponents`; public note cites `0x3c` get-catacomb-state in another tooling path |
| 61 | `0x3d` | 8 | **Catacomb load/save family** | **medium** | Clustered with 62/63 around catacomb save; often preceded by `getCommProtocolVersion` |
| 62 | `0x3e` | 8 | **Catacomb load/save family** | **medium** | Same cluster as 61/63 |
| 39 | `0x27` | 13 | **Match / bridge-status related** | **medium** | 7× match in our window; **do not** equate to other RE’s `0x27` SKS-lock without proving same space |
| 74 | `0x4a` | 8 | **Match path / catacomb-adjacent** | **medium** | Mixed match + confirm-save proximity |
| 8 | `0x08` | 7 | **serviceStatus-related** | **medium** | 7× near `serviceStatus` |
| 44 | `0x2c` | 8 | Accessory/bridge probe? | **low** | Weak caller signal |
| 46 | `0x2e` | 5 | Near `bridgeServiceCheck` | **low–medium** | |
| 58 | `0x3a` | 5 | Possible catacomb-adjacent | **low** | Weak; not as clean as 56/63 |
| 76 | `0x4c` | 4 | Near bridgeServiceCheck | **low** | Public `0x4c` catacomb-state claims are a **different** tooling path until proven |
| 80 | `0x50` | 3 | Near protocol/version bring-up | **low** | |
| 15 | `0x0f` | 1 | Near enroll | **low** | Single sample |
| 3,4,26,38,40,65 | various | 1 each | Unannotated | **low** | Too few samples |

## Sequence patterns we verified

### Device list (boot + settings)

```
getCommProtocolVersion → Success
performCommand 82 (0x52)
performCommand 84 (0x54)
performGetBioDeviceListCommand → 0
```

`82` then `84` paired **15/21** times in this capture.

### Enroll

- Heavy `14` (`0x0e`) with `enrollContinue`
- Lots of `84` / BridgeXPC TX/RX during finger captures
- Ends with `12` (`0x0c`) cancel/stop when UI tears down

### Unlock + catacomb persist

- `48` (`0x30`) with `getEnabledForUnlock → 1`
- Catacomb cluster: `61/62/63` and `56`; **`63` uniquely glued to ConfirmSaveCatacomb (8/8)**
- Log text: `master.cat`, `saveCatacombForComponents`, `saveTemplateListAfterTemplateUpdate`

## Cross-checks vs public notes

| Claim | Our stance |
| --- | --- |
| QuickTouch: Tier‑1 `0x54` carries biometric payloads | **Supports** our high use of `84` as generic Mesa I/O / device-list B / match path — not a contradiction |
| Other tooling: `0x38` / `0x3c` catacomb-ish | **Weak support** for our `56`/`60` — same hex, unclear if same space; keep medium |
| Other tooling: `0x27` = SKS lock | **Not adopted** for our `39` — our evidence says match/bridge; possible collision across protocol layers |
| Headers: `performCancelCommand`, `getEnabledForUnlock`, `performConfirmSaveCatacombCommand`, `getNodeTopology` | **Align** with behavioral labels for `12`, `48`, `63`, `17` |

## Relation to mute Linux AKS EP7

These opcodes are **`biometrickitd` → BridgeXPC → Mesa** commands, not the
Linux `t2_sep` mailbox AppleKeyStore EP7 capability frames we falsified.
Annotation helps understand macOS biometric ordering (device list → enroll/match
→ catacomb save). It does **not** by itself give a drop-in EP7 replay list.

## Files

- Full tagged timeline (private): `~/Private/t2-aks-capture/mesa-bridge-timeline.txt`
- Earlier histogram: [MESA_BRIDGE_OPCODE_NOTES.md](MESA_BRIDGE_OPCODE_NOTES.md)

## Follow-up mining (2026-09-06 evening)

See [CATACOMB_BRIDGE_SEQUENCE.md](CATACOMB_BRIDGE_SEQUENCE.md) for load vs save
ordering, `/Library/Catacomb/<uuid>/prepare/` staging, and the cold-boot empty
`loadCatacomb` path (filesystem Common logs before Mesa confirm cluster).
