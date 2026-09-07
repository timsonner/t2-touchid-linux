#!/bin/bash
# Remove AKS boot-capture LaunchDaemon. Keeps /var/log/t2-aks-capture unless --wipe-logs.
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Re-run with sudo." >&2
  exit 1
fi

LABEL="com.timsonner.t2-aks-boot-capture"
PLIST="/Library/LaunchDaemons/${LABEL}.plist"
SCRIPT="/usr/local/libexec/t2-aks-boot-capture.sh"

launchctl bootout system/"$LABEL" 2>/dev/null || true
rm -f "$PLIST" "$SCRIPT"

if [[ "${1:-}" == "--wipe-logs" ]]; then
  rm -rf /var/log/t2-aks-capture
  echo "Daemon removed and logs wiped."
else
  echo "Daemon removed. Logs kept in /var/log/t2-aks-capture"
  echo "Wipe with: sudo $0 --wipe-logs"
fi
