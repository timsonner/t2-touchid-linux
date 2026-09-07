# Catacomb on-disk layout (MBA91, public-safe)

Date: 2026-09-07. Host: MacBookAir9,1 / macOS 15.7.9. Dir UUID =
Hardware UUID / Provisioning UDID (example pattern only in live notes).

## Files

Under `/Library/Catacomb/<HardwareUUID>/`:

| File | Role |
| --- | --- |
| `user_<uid_hex>.cat` | Per-user archive (uid 501 → `user_000001f5.cat`) |
| `master.cat` | Machine-level archive (`CatacombUserID` = -1) |
| `biolockout.cat` | Lockout record (`HRLB` secure blob) |

## Container format

Each `.cat` is an **NSKeyedArchiver** binary plist (`$archiver` =
`NSKeyedArchiver`), **not** a raw CFTL file.

### `user_*.cat` top keys

- `CatacombVersion` — observed **196608** (`0x30000`)
- `CatacombUserID` — POSIX uid (501)
- `CatacombUserUUID` / `CatacombUserKeybagUUID` — NSUUID
- `CatacombIdentityList` — array of `BiometricKitIdentity` (name, match counts,
  creation time, identity UUID, accessory Builtin, …)
- `CatacombSecureData` — `NSMutableData` whose bytes are a **CFTL** blob

Identity **metadata is plaintext** in the archive. The biometric template /
SEP-sealed payload lives only inside `CatacombSecureData`.

### `master.cat` top keys

- `CatacombVersion` 196608
- `CatacombUserID` **-1**
- `CatacombEnrollmentCount`
- `CatacombCurrentDate`
- `CatacombSecureData` — smaller CFTL blob

### `biolockout.cat`

- `BioLockoutRecordVersion` 65536
- `BioLockoutRecordSecureData` — magic **`HRLB`** (LE), version field 2

## CFTL (`LTFC` on disk) header

Observed layout (little-endian):

| Offset | Field | user.cat | master.cat |
| --- | --- | --- | --- |
| 0 | FourCC | `LTFC` | `LTFC` |
| 4 | type/version | **10** (`0xa`) | **10** |
| 8 | uid | **501** | **0xffffffff** |
| 12 | pad/flags | 0 | 0 |
| 16..31 | zeros | 0 | 0 |
| 32+ | sealed body | ~26 KiB | 244 B total file payload |

Same FourCC family as Mesa CompleteSave opcode **62** reply (`LTFC` / `CFTL`).
The identity UUID from `CatacombIdentityList` does **not** appear in the clear
inside the CFTL body (SEP-sealed).

## Implication for Linux / Omarchy

- Copying `.cat` files preserves enroll metadata + sealed blobs for later
  `loadCatacomb`-class restore **after** a working biometric transport exists.
- It does **not** unmute AKS EP7 and does **not** replace BridgeXPC/Mesa.
- Do not commit raw `.cat` / CFTL binaries to git.

Private extracts (hashes only in public notes): `$HOME/Private/t2-aks-research/cftl-extract/`.
