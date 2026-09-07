# MBA91 AKS capture — command checklist

## Canonical (next time)

```bash
tar -xvf mba91-aks-macos-capture.tar.gz
cd mba91-aks-macos-capture
chmod +x install.sh uninstall.sh t2-aks-boot-capture.sh
sudo ./install.sh
sudo ls -lt /var/log/t2-aks-capture/    # need growing *.logstream.log

open EnablePrivateLogging.mobileconfig
# System Settings → General → Device Management → Install
#   "Enable Unified Log Private Data (T2 research)"
sudo log config --status                # expect PRIVATE_DATA

# reboot → login → enroll Touch ID

sudo ls -lt /var/log/t2-aks-capture/
# copy newest *.boot.txt *.logstream.log *.snapshot.log to USB
# also copy EFI/APPLE/EMBEDDEDOS/FDRData off-machine

sudo ./uninstall.sh
# Device Management → remove the private-data profile
```

## As-run on MBA91 (2026-09-06)

```bash
tar -xvf mba91-aks-macos-capture.tar.gz
cd mba91-aks-macos-capture
chmod +x install.sh uninstall.sh t2-aks-boot-capture.sh
chmod +x enable-private-data-system.sh
sudo ./install.sh
sudo ./enable-private-data-system.sh    # alone: no PRIVATE_DATA yet
sudo log config --status

sudo ls -lt /var/log/t2-aks-capture/
sudo ps aux | grep -E '[l]og stream|[t]2-aks-boot'
sudo launchctl kickstart -k system/com.timsonner.t2-aks-boot-capture
sleep 3
sudo ls -lt /var/log/t2-aks-capture/

open EnablePrivateLogging.mobileconfig  # Device Management → Install
sudo log config --status                # INFO STREAM_LIVE PRIVATE_DATA
```

Never use: `sudo log config --mode 'private_data:on'` (Invalid Modes on modern macOS).
