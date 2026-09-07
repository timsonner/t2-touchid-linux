#!/bin/bash
# Install early-boot AKS/SEP unified-log capture (LaunchDaemon).
# Run on the MacBook Air in macOS Terminal:
#   chmod +x install.sh && sudo ./install.sh
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Re-run with sudo." >&2
  exit 1
fi

LIBEXEC="/usr/local/libexec"
HERE="$(cd "$(dirname "$0")" && pwd)"
PLIST_SRC="$HERE/com.timsonner.t2-aks-boot-capture.plist"
SCRIPT_SRC="$HERE/t2-aks-boot-capture.sh"
PLIST_DST="/Library/LaunchDaemons/com.timsonner.t2-aks-boot-capture.plist"
LOG_DIR="/var/log/t2-aks-capture"

mkdir -p "$LIBEXEC" "$LOG_DIR"
chmod 700 "$LOG_DIR"

install -m 755 "$SCRIPT_SRC" "$LIBEXEC/t2-aks-boot-capture.sh"
install -m 644 "$PLIST_SRC" "$PLIST_DST"
chown root:wheel "$PLIST_DST" "$LIBEXEC/t2-aks-boot-capture.sh"

launchctl bootout system/com.timsonner.t2-aks-boot-capture 2>/dev/null || true
launchctl bootstrap system "$PLIST_DST"
launchctl enable system/com.timsonner.t2-aks-boot-capture
launchctl kickstart -k system/com.timsonner.t2-aks-boot-capture

echo
echo "Installed. Live stream is running for THIS session already."
echo "Logs: $LOG_DIR"
echo
echo "Next (full procedure: see README.md):"
echo "  1) Open log dir for non-root / agent read:"
echo "       sudo chmod 755 $LOG_DIR"
echo "       sudo chmod a+r $LOG_DIR/*"
echo "       ls -lt $LOG_DIR   # need growing *.logstream.log"
echo "  2) Enable private data BEFORE reboot:"
echo "       open EnablePrivateLogging.mobileconfig"
echo "       System Settings → General → Device Management → Install"
echo "       sudo log config --status   # expect PRIVATE_DATA"
echo "  3) Reboot once (cold-boot capture); chmod a+r again if needed."
echo "  4) Log in, enroll Touch ID while capture is running."
echo "  5) Copy newest files from $LOG_DIR off-machine."
echo "  6) sudo ./uninstall.sh  (+ remove the Device Management profile)"
echo
launchctl print system/com.timsonner.t2-aks-boot-capture 2>/dev/null | head -n 40 || true
ls -la "$LOG_DIR" || true
