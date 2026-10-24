# Catacomb decoder fixture, first run — MBA91 (2026-10-24)

Branch: `research/mba91-aks-ep7`
Status: harness built and validated on the live macOS component;
**superseded as a gate on 2026-10-24** — decoding is necessary but not
sufficient, because a Linux-emitted component is a different SEP
generation and the `0x3a` hash is not a digest of the archive

No identity UUIDs, keybag handles, hardware UUIDs, or blob bytes.

## Why this exists

`IDENTITY2_NEXT_HANDOFF_2026-10-04.md` Path M needs a copy of the
Linux-emitted archive decoded by the matching macOS secure decoder, in a
disposable directory, with no load or save. There was no executable for
that gate. There is now: `tools/catacomb-decode-fixture.swift`.

## What ran

A copy of the live `/Library/Catacomb/<dir>/user_000001f5.cat` was taken
to a temp directory and decoded in-process. The tool opens
`BiometricKit.framework`, unarchives per key, and prints only counts,
key names, classes and hashes. No BridgeXPC connection, no `loadCatacomb`,
no `save`, no delete, no write anywhere near `/Library/Catacomb`.

| Field | Value |
| --- | --- |
| bytes | 29921 |
| envelope | `NSKeyedArchiver`, `$version` 100000 |
| top-level keys | `CatacombIdentityList`, `CatacombSecureData`, `CatacombUserID`, `CatacombUserKeybagUUID`, `CatacombUserUUID`, `CatacombVersion` |
| unknown top-level keys | none |
| `CatacombVersion` | 196608 (`0x00030000`) |
| `CatacombUserID` | 501 |
| identity count | 1 |
| identity class | `BiometricKitIdentity` |
| secure blob | 28394 bytes, header `4c544643 0a000000 f5010000` |
| non-secure decode | ok |
| secure decode (recovered class set) | ok |

The blob header is `LTFC`, version `10`, Apple UID `501`. It is the only
part of the blob the tool prints.

## What this proves, and what it does not

Proves: the harness resolves the private classes and passes both the
permissive and the secure decode path on a component macOS itself wrote.
It is therefore a usable oracle, and the six-key top level is the exact
schema a Linux-emitted archive has to match.

Does not prove: that SEP accepts a blob (`loadCatacomb` is out of scope,
and a rejected blob is the error-269 path that deletes Catacomb files),
or anything at all about the Linux-emitted archive.

## Next, operator

1. On Omarchy, copy the two-identity component out:
   `sudo cp /var/lib/t2-touchid/catacomb/*/user_000001f5.cat /boot/` or to
   a USB stick. It is 39314 bytes.
2. Boot macOS, copy it somewhere disposable, and run:
   `./tools/catacomb-decode-fixture.swift /tmp/user_000001f5.linux.cat`
3. Compare against the table above. Expected if the encoder is compatible:
   `identityCount` 2, `decode` ok, `secureDecode` ok, same six top-level
   keys, no unknown keys, and a larger secure blob.
4. Stop. Record the result. Do not replace `/Library/Catacomb` and do not
   call `loadCatacomb` on the strength of a decode alone.

If `secureDecode` fails, the failure message is the finding: it names the
class or key the macOS decoder would not accept, which is what the Linux
encoder has to change.
