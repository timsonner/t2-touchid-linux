# MBA91 Mesa opcodes ↔ bent `biometric-command` codecs

Date: 2026-09-07. Offline only — no live SEP/Bridge traffic.

**Wire path (both sides):** BridgeXPC method **3** `PERFORM_COMMAND` → inner
biometric header magic **`0x4d42`** (`<HHHH` = magic, command, version, value) +
optional payload. MBA91 logs this as
`performCommand:version:inValue:inData:inSize:outData:outSize: <cmd> <ver> <val> …`.

**bent codec:** `prototypes/t2sep-probe/biometric-command.py` (Catalina 19H15 ABI,
extended for current v2 catacomb save). Field helpers return
`(command, version, in_value, payload, out_capacity)`.

**MBA91 evidence:** `MESA_OPCODE_ANNOTATIONS.md`, `BRIDGE_GETIDENTITY_DECODE.md`,
`CATACOMB_BRIDGE_SEQUENCE.md`, unlock capture timelines (2026-09-06/07).

## How to read the match column

| Tag | Meaning |
| --- | --- |
| **ALIGN** | Same opcode number + same role on both sides |
| **ALIGN\*** | Same opcode; MBA91 log name refined bent/Catalina naming |
| **PARTIAL** | Same opcode; bent uses it live but codec has no named constant / incomplete shape |
| **GAP** | MBA91 high-confidence opcode **missing** from bent codec constants |
| **CONFLICT** | Earlier MBA91 annotation disagreed; later decode or bent constant wins |

## Core crosswalk

| dec | hex | MBA91 label (confidence) | bent symbol / helper | bent shape (ver / in / out) | Match | Notes |
| --- | ---: | --- | --- | --- | --- | --- |
| 12 | `0x0c` | Cancel / stop (**high**) | `COMMAND_CANCEL` / `cancel_fields()` | v1 / empty / out 0 | **ALIGN** | |
| 14 | `0x0e` | enrollContinue (**high**) | *(no constant)* | — | **GAP** | bent enroll is `COMMAND_ENROLL` **`0x03`**, not continue `0x0e` |
| 8 | `0x08` | **GetIdentityRecords** (**high**, decode doc) | *(no GetIdentity constant)* | — | **GAP** / **CONFLICT** | Early annotation said “serviceStatus”; decode shows 40 B uid+UUID. bent list identities via **`0x42`** `COMMAND_IDENTITY_LIST` (`IDENTITY` = `<I16s`) — **different opcode** |
| 17 | `0x11` | getNodeTopology (**high**) | *(none)* | — | **GAP** | MBA91: inSize≈20, reply **3060** B |
| 39 | `0x27` | GetSKSLockState (**high** in decode) | `COMMAND_GET_SKS_LOCK_STATE` / `sks_lock_state_fields` | ver 0–2 / uid u32 / out **4** | **ALIGN\*** / **CONFLICT** | Early Mesa note said “match”; bent + decode agree **SKS lock**. MBA91 reply `0x10000000` |
| 40 | `0x28` | (seen unlock window) | `COMMAND_GET_BIOMETRICKITD_INFO` / `biometrickitd_info_fields` | v1 / empty / out **23** | **ALIGN** | Seen in 2026-09-07 unlock capture |
| 46 | `0x2e` | near bridgeServiceCheck (**low–med**) | `COMMAND_GET_PROTECTED_CONFIG` / `protected_config_fields` | v1 / uid u32 / out **32** | **ALIGN\*** | Prefer bent name over weak MBA91 label |
| 48 | `0x30` | getEnabledForUnlock (**high**) | *(none)* | — | **GAP** | Heavily used on MBA91 unlock; not in bent constant table |
| 56 | `0x38` | catacomb UUID/save family (**medium**) | `COMMAND_GET_CATACOMB_UUID` / `catacomb_uuid_fields` | ver **0** / uid / out **16** | **ALIGN\*** | |
| 58 | `0x3a` | catacomb-adjacent (**low**) | *(none)* | — | **PARTIAL** | Leave unmapped |
| 60 | `0x3c` | get-catacomb-state family (**medium**) | `COMMAND_GET_CATACOMB_STATE` / `catacomb_state_fields` | ver **0** / empty / out up to 8×256 | **ALIGN** | |
| 61 | `0x3d` | PrepareSaveCatacomb (**medium→high** w/ sequence) | `COMMAND_PREPARE_SAVE_CATACOMB` / `prepare_save_catacomb_fields` | **v2** / 24 B context / out **4** (size) | **ALIGN** | Context = `<II16s>` uid + group + zeros |
| 62 | `0x3e` | CompleteSaveCatacomb (**high** + `LTFC`) | `COMMAND_COMPLETE_SAVE_CATACOMB` / `complete_save_catacomb_fields` | **v2** / 24 B context / out = blob size | **ALIGN** | MBA91 reply head `LTFC` + ver 10 + uid — matches on-disk CFTL |
| 63 | `0x3f` | ConfirmSaveCatacomb (**high** 8/8) | `COMMAND_CONFIRM_SAVE_CATACOMB` / `confirm_save_catacomb_fields` | **v2** / 24 B context / out **0** | **ALIGN** | |
| 74 | `0x4a` | match path (**medium**) | *(none)* | — | **GAP** | |
| 80 | `0x50` | protocol/catacomb group (**low**) | `COMMAND_GET_CATACOMB_GROUP_STATE` / `catacomb_group_state_fields` | ver **0** / empty / out 56×64 | **ALIGN\*** | |
| 82 | `0x52` | GetBioDeviceList A (**high**) | `COMMAND_GET_BIO_DEVICE_LIST` / `bio_device_list_fields` | v1 / empty / out ≤ **264** (6×44) | **ALIGN** | bent Linux: one 44 B builtin record |
| 84 | `0x54` | GetBioDeviceList B / match I/O (**high**) | *(no named constant)* | bent live: often **20 B** in, ~83 B out | **PARTIAL** | Critical in bent warm-match ordering after `0x52`; codec module never named it |

### Catacomb load (bent has it; MBA91 mostly filesystem-side)

| dec | hex | bent | MBA91 |
| --- | ---: | --- | --- |
| 64 | `0x40` | `COMMAND_LOAD_CATACOMB` / `load_catacomb_fields` — v1 / **opaque CFTL blob** in / out 0; checks uid at blob `+8` | Host `loadCatacomb` unarchives `.cat` then Mesa sync; opcode **64** not highlighted in our Mesa tables — **watch** on Linux cold restore |

### Identity list (bent primary vs MBA91 GetIdentityRecords)

| Path | Opcode | Shape |
| --- | ---: | --- |
| bent Linux | **`0x42`** `COMMAND_IDENTITY_LIST` | in: uid u32; out: N × `<I16s>` (20 B) |
| MBA91 macOS Bridge | **`0x08`** GetIdentityRecords | in: empty; out: **40 B**/record (uid + UUID + trailer) |

Same *job* (enumerate identities), **different commands**. Do not treat `0x08` and `0x42` as aliases.

## Unlock / save sequence (MBA91) with bent names

```text
48 getEnabledForUnlock          ← GAP in bent codec
39 GetSKSLockState (0x27)       ← ALIGN
82/84 device list / I/O         ← ALIGN / PARTIAL
… match (84, 74, 12 cancel) …
60 GetCatacombState (0x3c)      ← ALIGN
61 PrepareSave (0x3d) v2        ← ALIGN
62 CompleteSave (0x3e) v2 → LTFC← ALIGN
63 ConfirmSave (0x3f) v2        ← ALIGN
56 GetCatacombUUID (0x38)       ← ALIGN*
```

## Framing sizes from MBA91 os_log (not bent)

Observed BridgeXPC body sizes during unlock (informative only):

- RX bodies often **116, 119, 149, 153, 201, 207, 213** (+ large CompleteSave)
- TX messages often **128, 162, 166, 185, 188**

These include method-3 envelope + bplist overhead — compare to bent enveloped
method-0 **113 B** / reply **132 B** only after Omarchy reproduce on Air.

## Gaps that matter for Omarchy step 2+

1. **`0x30` getEnabledForUnlock** — encode/decode unknown in bent module.
2. **`0x08` GetIdentityRecords (40 B)** vs bent **`0x42` identity list** — which
   does current `bkremoted` on **23P6068** expect after load?
3. **`0x54` companion** after **`0x52`** — bent already treats as ordering-critical;
   still unnamed in codec.
4. **`0x11` topology** — optional for unlock; needed for some clients.
5. **`0x0e` enrollContinue** — enroll path only; defer until policy work.

## Safe next Linux canaries (after enveloped 0/1)

Read-only, in order:

1. `0x52` bio device list (bent helper)
2. `0x54` with 20-byte input (bent live shape)
3. `0x27` SKS lock for uid 501
4. `0x42` identity list **and/or** probe `0x08` empty-in 40 B out — **compare**
5. Only later: `0x40` loadCatacomb with Private CFTL blob

## Sources

- bent: `biometric-command.py`, `bridge-protocol.py`, `docs/touch-id.md` (catacomb
  `0x3d/3e/3f`, device list `0x52`, `0x54` ordering)
- MBA91: `MESA_OPCODE_ANNOTATIONS.md`, `BRIDGE_GETIDENTITY_DECODE.md`,
  `CATACOMB_ONDISK.md`, Private unlock logs 2026-09-06/07

## Live Omarchy canaries (2026-09-07)

Cold + warm A/B on MBA91 Omarchy: see `WARM_IDENTITY_AB_2026-09-07.md`.
Summary: `0x52`/`0x54`/`0x27` shapes match bent; warm `0x42` count=1 uid=501;
`0x08` still not an alias for `0x42`; `0x54` first_byte remained 0 even warm.
