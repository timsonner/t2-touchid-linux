#!/bin/bash
# t2-aks-boot-capture.sh — early-boot unified-log stream for AKS/SEP/BiometricKit research.
set -uo pipefail

LOG_DIR="${T2_AKS_LOG_DIR:-/var/log/t2-aks-capture}"
mkdir -p "$LOG_DIR"
chmod 700 "$LOG_DIR"

BOOT_ID="$(sysctl -n kern.bootsessionuuid 2>/dev/null || true)"
[[ -n "${BOOT_ID}" ]] || BOOT_ID="$(date -u +%Y%m%dT%H%M%SZ)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PREFIX="${LOG_DIR}/${STAMP}-${BOOT_ID}"

MARKER="${PREFIX}.boot.txt"
STREAM_LOG="${PREFIX}.logstream.log"
SNAP_LOG="${PREFIX}.snapshot.log"

# Marker first so we always leave evidence even if later steps die.
{
  echo "=== t2-aks-boot-capture marker ==="
  echo "utc_start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "boot_session: ${BOOT_ID}"
  echo "host: $(scutil --get LocalHostName 2>/dev/null || hostname)"
  echo "os: $(sw_vers 2>/dev/null | tr '\n' ' ')"
  echo
  echo "=== hardware (short) ==="
  system_profiler SPHardwareDataType 2>/dev/null | sed -n '1,40p' || true
  echo
  echo "=== interfaces ==="
  ifconfig -a 2>/dev/null || true
} >"$MARKER" 2>&1 || true
chmod 600 "$MARKER" 2>/dev/null || true

# Light snapshot in background (capped) — never block the live stream.
(
  echo "=== log show --last 5m (capped) ==="
  echo "utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  /usr/bin/log show --last 5m --info --style compact --predicate '
    subsystem CONTAINS[c] "KeyStore"
    OR subsystem CONTAINS[c] "Biometric"
    OR subsystem CONTAINS[c] "sep"
    OR subsystem CONTAINS[c] "LocalAuthentication"
    OR subsystem CONTAINS[c] "coreauth"
    OR subsystem CONTAINS[c] "credential"
    OR process CONTAINS[c] "biometrickit"
    OR process CONTAINS[c] "coreauthd"
    OR process CONTAINS[c] "akd"
  ' 2>&1 | /usr/bin/head -n 5000 || true
) >"$SNAP_LOG" 2>&1 &
chmod 600 "$SNAP_LOG" 2>/dev/null || true

# Live stream is the main job (foreground for KeepAlive).
# Prefer ProcessType Interactive in the plist so launchd does not SIGTERM us as "inefficient".
exec /usr/bin/log stream --level debug --style compact --predicate '
  subsystem CONTAINS[c] "KeyStore"
  OR subsystem CONTAINS[c] "Biometric"
  OR subsystem CONTAINS[c] "sep"
  OR subsystem CONTAINS[c] "LocalAuthentication"
  OR subsystem CONTAINS[c] "coreauth"
  OR subsystem CONTAINS[c] "credential"
  OR subsystem CONTAINS[c] "Bridge"
  OR process CONTAINS[c] "biometrickit"
  OR process CONTAINS[c] "coreauthd"
  OR process CONTAINS[c] "akd"
  OR process CONTAINS[c] "sepd"
  OR process CONTAINS[c] "AppleCredential"
  OR category CONTAINS[c] "AKS"
  OR eventMessage CONTAINS[c] "AppleKeyStore"
  OR eventMessage CONTAINS[c] "SEP"
' >>"$STREAM_LOG" 2>&1
