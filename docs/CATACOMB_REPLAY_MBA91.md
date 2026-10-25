# Catacomb replay: Linux → macOS — MBA91

Status: procedure, **not yet run**. Written 2026-10-24.

This tests one question: does macOS load a Catacomb component that Linux
emitted, and keep the second identity?

No identity UUIDs, keybag handles, hardware UUIDs, or blob bytes belong
in this file or in a commit.

## What it does not need

Not encryption. `0x3d` sends SEP a 24-byte descriptor and returns a
length; `0x3e` returns the blob. **SEP produces the blob from its own
state.** The Linux component already contains a genuine, SEP-sealed
two-identity blob, so replay is a byte copy into `0x40`, not a crypto
problem. See [`OPCODES.md`](OPCODES.md) and
[`CATACOMB_BLOB_STATEFUL_2026-10-24.md`](../tools/mba91-aks-macos-capture/CATACOMB_BLOB_STATEFUL_2026-10-24.md).

What is unknown is SEP's load policy: whether it accepts a seal older
than its current state. The 2026-10-04 boot is the reason this is worth
testing — macOS loaded an **older** one-identity component over a newer
two-identity SEP state and got status 0.

## Preconditions

- macOS 15.7.9 (24G830), Finger 1 unlocks.
- `bioutil -c` reads **1**.
- A USB stick that macOS mounts without sudo (exFAT or FAT32).
- The Linux component: 39314 bytes, two identities.

Stop at any failed precondition. Do not improvise around it.

## Stage 1 — stage the component from Omarchy

```sh
sudo install -d -m 0700 /tmp/catacomb-replay
sudo cp /var/lib/t2-touchid/catacomb/*/user_000001f5.cat /tmp/catacomb-replay/
sha256sum /tmp/catacomb-replay/user_000001f5.cat
stat -c '%s %a %U:%G' /tmp/catacomb-replay/user_000001f5.cat
```

Expect `39314` bytes. Copy to the stick:

```sh
usb=/run/media/$USER/<label>
sudo cp /tmp/catacomb-replay/user_000001f5.cat "$usb/"
sync
```

Only `user_000001f5.cat` travels. Do **not** bring the Linux
`master.cat` or `biolockout.cat`; the macOS ones stay.

## Stage 2 — M1, decode a copy (safe)

On macOS, on a copy. This never touches `/Library/Catacomb`.

```sh
cp /Volumes/<label>/user_000001f5.cat /tmp/replay.cat
shasum -a 256 /tmp/replay.cat
cd ~/Projects/t2-linux
./tools/catacomb-decode-fixture.swift /tmp/replay.cat
```

Pass: `identityCount` 2, `decode` ok, `secureDecode` ok, the same six
top-level keys, no unknown keys. **Stop if `secureDecode` fails** — the
error names the class or key, and that is the finding.

A pass does not authorize Stage 4. It only rules out the schema.

## Stage 3 — back up before anything moves

```sh
stamp=$(date +%Y%m%d-%H%M%S)
backup="$HOME/Private/catacomb-backup-$stamp"
sudo ditto /Library/Catacomb "$backup"
sudo shasum -a 256 /Library/Catacomb/*/*.cat "$backup"/*/*.cat
```

The two sets of hashes must match, file for file. Then take a second
copy **off the machine**, because the failure mode we are guarding
against is error-269 deleting Catacomb files:

```sh
sudo ditto "$backup" /Volumes/<label>/catacomb-backup
sync
```

Record `$backup` and the stick path. Do not reboot until both copies
exist.

Baseline immediately before the replace:

```sh
bioutil -c        # must be 1
```

## Stage 4 — replace only the user component

Only with explicit operator approval, and only after Stage 2 passed and
Stage 3 verified.

```sh
dir=$(sudo ls -d /Library/Catacomb/*/ | head -1)
sudo install -o root -g wheel -m 0644 /tmp/replay.cat "$dir/user_000001f5.cat"
sudo shasum -a 256 "$dir/user_000001f5.cat" /tmp/replay.cat
```

The two hashes must match. Nothing else in the directory changes.

## Stage 5 — reboot and read

```sh
sudo reboot
```

After boot:

```sh
bioutil -c
log show --last boot --predicate 'process == "biometrickitd"' --style compact 2>/dev/null \
  | grep -E 'restoreAndSyncTemplates|removing SEP identity|loadCatacombForUser'
```

An empty `log show` means the predicate or retention, not a result.

| Outcome | Read |
| --- | --- |
| **Success** | `bioutil -c` = 2, `restoreAndSyncTemplates identities 2`, no `removing SEP identity`, and the second finger matches |
| **Partial** | count 2 but the second finger fails: the host list came back, the template did not. Record, then reconcile on Linux |
| **Failure** | count 1 and `removing SEP identity` fires again: SEP or the host dropped it. Record the status lines, then roll back |

Test the second finger at the lock screen, not in System Settings. Do
not re-enrol it as part of this test.

## Rollback

Only after re-checking the backup hashes:

```sh
sudo rm -rf /Library/Catacomb
sudo ditto "$backup" /Library/Catacomb
sudo reboot
```

If error-269 emptied the directory, this is the same restore. Confirm
`bioutil -c` is 1 and Finger 1 unlocks afterwards.

## Why the odds are not zero

- The 10-04 boot accepted an older blob with status 0.
- The blob grows with identity count (~37.8 kB for two against 28.4 kB
  for one), which is what per-identity data looks like.
- The keybag is the same file both OSes already use, and unchanged.

If it still fails, the answer is no for this bridgeOS, and the record
should say which stage failed.

## Do nots

- No `loadCatacomb` or `0x40` from Linux as a shortcut; that path has
  cleared identities here and has no equivalent backup story.
- No replace of `master.cat`, `biolockout.cat`, or the directory.
- No second Apple UID, no new identity, no `recover-observed`.
- No commit of the staged component, the backup, or the journal.
- No proceeding on a partial M1, a hash mismatch, or `bioutil -c` ≠ 1.
