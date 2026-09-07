# MBA91 backup + teardown (verified 2026-09-06)

Paths below use `$HOME` / `~` so any macOS or Linux username works. Set `KIT` to your local copy of `tools/mba91-aks-macos-capture` (or leave the default under `$HOME/Downloads/...`). LaunchDaemon label `com.timsonner.t2-aks-boot-capture` is a reverse-DNS id, not a home path.

After cold-boot capture → enroll → lock-screen unlock, back up artifacts
**before** uninstalling the LaunchDaemon / removing `PRIVATE_DATA`.

Sensitive: keybags + catacomb. Keep off git/iCloud. Prefer USB + `~/Private`.

## What to back up

| Artifact | Source | Notes |
| --- | --- | --- |
| Capture logs | `/var/log/t2-aks-capture/` and/or `~/Private/t2-aks-capture/` | Cold-boot `*.logstream.log`, logshow backfill, Mesa notes |
| Catacomb | `/Library/Catacomb/<UUID>/` | On this Air: `64FFD0F9-9014-5F6F-BC5B-265A589D0570/` — `master.cat`, `user_000001f5.cat` (uid 501), `biolockout.cat` |
| Keybags | `macos-export-keybags.sh` output | Script may write `/private/tmp/t2-keybags.tar.gz` even if you pass a path — copy onto USB yourself |
| ESP FDR | `disk0s1` | **N/A on this wiped Air** — path absent; skip |

## USB backup (as-run)

USB volume was `/Volumes/NO NAME` (msdos). Destination used:

`/Volumes/NO NAME/mba91-backup-20260906/`

```bash
USB="/Volumes/NO NAME"
DEST="$USB/mba91-backup-$(date +%Y%m%d)"
CAT="/Library/Catacomb/64FFD0F9-9014-5F6F-BC5B-265A589D0570"

mkdir -p "$DEST/t2-aks-capture" "$DEST/catacomb" "$DEST/keybags"

# 1) capture logs (from Private copy preferred)
rsync -a ~/Private/t2-aks-capture/ "$DEST/t2-aks-capture/"

# 2) catacomb UUID tree
rsync -a "$CAT/" "$DEST/catacomb/64FFD0F9-9014-5F6F-BC5B-265A589D0570/"

# 3) keybags — export then copy (script often ignores DEST and writes /tmp)
cd /tmp
curl -fsSL -o macos-export-keybags.sh \
  https://raw.githubusercontent.com/timsonner/t2-touchid-linux/research/mba91-aks-ep7/tools/macos/macos-export-keybags.sh
chmod +x macos-export-keybags.sh
sudo ./macos-export-keybags.sh "$DEST/keybags"

# if archive is in /tmp instead:
sudo mkdir -p "$DEST/keybags"
sudo cp -p /private/tmp/t2-keybags.tar.gz "$DEST/keybags/t2-keybags.tar.gz"
sudo chown "$(whoami)" "$DEST/keybags/t2-keybags.tar.gz"
chmod 600 "$DEST/keybags/t2-keybags.tar.gz"

# optional Private mirror
mkdir -p ~/Private/t2-keybags
cp -p "$DEST/keybags/t2-keybags.tar.gz" ~/Private/t2-keybags/t2-keybags-$(date +%Y%m%d).tar.gz
chmod 600 ~/Private/t2-keybags/t2-keybags-*.tar.gz

# 4) quick verify
ls -lh "$DEST/keybags/t2-keybags.tar.gz"
tar -tzf "$DEST/keybags/t2-keybags.tar.gz" | head
du -sh "$DEST" "$DEST"/*
```

Verified layout (~11 MB capture + small catacomb/keybags):

```text
mba91-backup-20260906/
  MANIFEST.txt
  t2-aks-capture/          # logstream, logshow, notes
  catacomb/<UUID>/         # master.cat, user_*.cat, biolockout.cat
  keybags/t2-keybags.tar.gz
```

## Teardown / uninstall

Only after USB verify (and Private copies if you want):

```bash
diskutil eject "/Volumes/NO NAME"

cd "${KIT:-$HOME/Downloads/mba91-aks-macos-capture}"   # set KIT to your kit checkout
sudo ./uninstall.sh
# optional: sudo ./uninstall.sh --wipe-logs

# System Settings → General → Device Management
#   remove "Enable Unified Log Private Data (T2 research)"

sudo rm -f /tmp/t2-keybags.tar.gz /private/tmp/t2-keybags.tar.gz
sudo log config --status   # PRIVATE_DATA should be gone
```

Confirm daemon is gone:

```bash
launchctl print system/com.timsonner.t2-aks-boot-capture 2>&1 | head
# expect not found / not loaded
```

## After teardown

- Linux AKS EP7 remains **parked/mute** — bags alone do not fix that.
- Next lab choice: dual-boot Omarchy on free space, or keep mining Mesa/BridgeXPC on macOS.
