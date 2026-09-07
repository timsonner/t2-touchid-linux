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
