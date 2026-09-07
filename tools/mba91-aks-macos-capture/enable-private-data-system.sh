#!/bin/bash
# Alternative to the .mobileconfig: write System Enable-Private-Data directly.
# sudo ./enable-private-data-system.sh
set -euo pipefail
if [[ "$(id -u)" -ne 0 ]]; then echo "Need sudo" >&2; exit 1; fi
DIR="/Library/Preferences/Logging"
mkdir -p "$DIR"
PLIST="$DIR/com.apple.system.logging.plist"
# Merge-ish: write minimal System private-data enable
defaults write "$DIR/com.apple.system.logging" Enable-Private-Data -bool true 2>/dev/null || true
# Prefer explicit plist (defaults may nest oddly)
cat > "$PLIST" <<'PL'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>Enable-Private-Data</key>
	<true/>
</dict>
</plist>
PL
chmod 644 "$PLIST"
echo "Wrote $PLIST"
echo "Verify: sudo log config --status   (look for PRIVATE_DATA)"
echo "Remove later: sudo rm -f $PLIST"
