# MBA91 AKS capture — command checklist

## Canonical (verified 2026-09-06 on MacBookAir9,1)

```bash
tar -xvf mba91-aks-macos-capture.tar.gz
cd mba91-aks-macos-capture
chmod +x install.sh uninstall.sh t2-aks-boot-capture.sh
sudo ./install.sh

# agent/local tools cannot sudo — open the log dir
sudo chmod 755 /var/log/t2-aks-capture
sudo chmod a+r /var/log/t2-aks-capture/*
ls -lt /var/log/t2-aks-capture/    # need growing *.logstream.log

open EnablePrivateLogging.mobileconfig
# System Settings → General → Device Management → Install
sudo log config --status                # expect PRIVATE_DATA

# reboot → login → re-chmod if needed → confirm NEW boot UUID files

# enroll Touch ID (at least one finger)
# then lock-screen Touch ID unlock (match path)

# CHECKPOINT — copy logs BEFORE EFI/FDR work
mkdir -p ~/Private/t2-aks-capture
rsync -a /var/log/t2-aks-capture/ ~/Private/t2-aks-capture/
# (re-chmod a+r first if Permission denied)

# EFI FDR — on MBA91 after wipe: path was ABSENT (empty ESP). Skip unless
# ls shows EFI/APPLE/EMBEDDEDOS/FDRData. Do not install Linux to "create" it.
# sudo mkdir -p /Volumes/EFI && sudo diskutil mount -mountPoint /Volumes/EFI disk0s1
# ls -la /Volumes/EFI/EFI/APPLE/EMBEDDEDOS/   # expect missing on this Air
# sudo diskutil unmount /Volumes/EFI

# prefer a second copy of capture logs to USB
# rsync -a ~/Private/t2-aks-capture /Volumes/USBNAME/mba91-backup-$(date +%Y%m%d)/

sudo ./uninstall.sh
# Device Management → remove the private-data profile
```

See also: [VERIFIED_SESSION_2026-09-06.md](VERIFIED_SESSION_2026-09-06.md).

Never use: `sudo log config --mode 'private_data:on'` (Invalid Modes on modern macOS).
Never commit raw logs / FDR / keybags / catacomb.

## Backup + teardown (verified)

Full write-up: [BACKUP_AND_TEARDOWN.md](BACKUP_AND_TEARDOWN.md).

```bash
# after enroll+unlock, with USB mounted e.g. "/Volumes/NO NAME"
USB="/Volumes/NO NAME"
DEST="$USB/mba91-backup-$(date +%Y%m%d)"
CAT="/Library/Catacomb/64FFD0F9-9014-5F6F-BC5B-265A589D0570"
mkdir -p "$DEST/t2-aks-capture" "$DEST/catacomb" "$DEST/keybags"
rsync -a ~/Private/t2-aks-capture/ "$DEST/t2-aks-capture/"
rsync -a "$CAT/" "$DEST/catacomb/64FFD0F9-9014-5F6F-BC5B-265A589D0570/"

# keybags: script may write /private/tmp/t2-keybags.tar.gz
cd /tmp && curl -fsSL -o macos-export-keybags.sh \
  https://raw.githubusercontent.com/timsonner/t2-touchid-linux/research/mba91-aks-ep7/tools/macos/macos-export-keybags.sh
chmod +x macos-export-keybags.sh
sudo ./macos-export-keybags.sh "$DEST/keybags"
sudo cp -p /private/tmp/t2-keybags.tar.gz "$DEST/keybags/t2-keybags.tar.gz"
sudo chown "$(whoami)" "$DEST/keybags/t2-keybags.tar.gz"
chmod 600 "$DEST/keybags/t2-keybags.tar.gz"

diskutil eject "$USB"
cd "${KIT:-$HOME/Downloads/mba91-aks-macos-capture}" && sudo ./uninstall.sh
# Device Management → remove private-data profile
sudo rm -f /tmp/t2-keybags.tar.gz /private/tmp/t2-keybags.tar.gz
```
