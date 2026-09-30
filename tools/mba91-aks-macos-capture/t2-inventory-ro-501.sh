#!/usr/bin/env bash
# Read-only full inventory for macos uid 501. No enroll/create/0x21/second bag.
set -euo pipefail
REPO=/home/tim/Projects/t2-touchid-linux
STAMP=/run/t2-touchid/inventory-ro-501.done
OUT_DIR=/var/lib/t2-touchid/inventory-journals
NOTE_DIR=$REPO/tools/mba91-aks-macos-capture
PORT_FILE=/var/lib/t2-touchid/biometric-port
mkdir -p /run/t2-touchid "$OUT_DIR"
if [[ -e $STAMP ]]; then
  echo "already ran this boot" >&2
  exit 0
fi
for i in $(seq 1 30); do
  [[ -e /dev/t2-aks ]] && break
  sleep 1
done
if [[ ! -e /dev/t2-aks ]]; then
  echo "FAIL: /dev/t2-aks missing after wait" | tee "$NOTE_DIR/INVENTORY_RO_501_FAIL_$(date +%Y%m%d-%H%M%S).txt"
  exit 1
fi
CONF=/etc/t2-touchid.conf
HOST=$(sed -n 's/^T2_TOUCHID_HOST=//p' "$CONF" | tail -n1)
IFACE=$(sed -n 's/^T2_TOUCHID_INTERFACE=//p' "$CONF" | tail -n1)
UID501=$(sed -n 's/^T2_TOUCHID_MACOS_USER_ID=//p' "$CONF" | tail -n1)
UID501=${UID501:-501}

PORT=${T2_TOUCHID_PORT:-}
if [[ -z ${PORT} && -r $PORT_FILE ]]; then
  PORT=$(tr -d '[:space:]' <"$PORT_FILE" || true)
fi
if [[ ! ${PORT:-} =~ ^[0-9]+$ || ${PORT:-0} -lt 49152 || ${PORT:-0} -gt 65535 ]]; then
  for i in $(seq 1 45); do
    if [[ -r $PORT_FILE ]]; then
      PORT=$(tr -d '[:space:]' <"$PORT_FILE" || true)
      [[ ${PORT:-} =~ ^[0-9]+$ && $PORT -ge 49152 && $PORT -le 65535 ]] && break
    fi
    sleep 1
  done
fi
if [[ ! ${PORT:-} =~ ^[0-9]+$ || ${PORT:-0} -lt 49152 || ${PORT:-0} -gt 65535 ]]; then
  if [[ -x /usr/local/sbin/t2-biometric-port-refresh ]]; then
    /usr/local/sbin/t2-biometric-port-refresh
    PORT=$(tr -d '[:space:]' <"$PORT_FILE")
  fi
fi
if [[ ! ${PORT:-} =~ ^[0-9]+$ || $PORT -lt 49152 || $PORT -gt 65535 ]]; then
  echo "FAIL: no valid BiometricKit port (set T2_TOUCHID_PORT or run t2-biometric-port-refresh)" | \
    tee "$NOTE_DIR/INVENTORY_RO_501_FAIL_$(date +%Y%m%d-%H%M%S).txt"
  exit 2
fi
export T2_TOUCHID_PORT=$PORT

TS=$(date +%Y%m%d-%H%M%S)
PRIV=$OUT_DIR/inventory-ro-501-$TS.private.json
PUB=$NOTE_DIR/INVENTORY_RO_501_$TS.json
LOG=$NOTE_DIR/INVENTORY_RO_501_$TS.log
if [[ -x /opt/t2-touchid/.venv/bin/python && -f /opt/t2-touchid/src/bridge-xpc-probe.py ]]; then
  PY=/opt/t2-touchid/.venv/bin/python
  PROBE=/opt/t2-touchid/src/bridge-xpc-probe.py
  cd /opt/t2-touchid/src
else
  PY=python3
  PROBE=$REPO/src/bridge-xpc-probe.py
  cd "$REPO/src"
fi

set +e
"$PY" "$PROBE" \
  --host "$HOST" \
  --interface "$IFACE" \
  --port "$PORT" \
  --macos-user-id "$UID501" \
  --initialize \
  --full-inventory \
  --stability-check \
  >"$PUB" 2>"$LOG"
rc=$?
set -e

priv_rc=1
if [[ $rc -eq 0 && -s $PUB ]]; then
  if "$PY" -c 'import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get("private_inventory_complete") else 1)' "$PUB"; then
    set +e
    "$PY" "$PROBE" \
      --host "$HOST" \
      --interface "$IFACE" \
      --port "$PORT" \
      --macos-user-id "$UID501" \
      --initialize \
      --full-inventory \
      --stability-check \
      --private-inventory-output "$PRIV" \
      >/dev/null 2>>"$LOG"
    priv_rc=$?
    set -e
  fi
fi

{
  echo "rc=$rc priv_rc=${priv_rc:-n/a}"
  echo "host=$HOST iface=$IFACE port=$PORT uid=$UID501"
  echo "private=$PRIV"
  echo "--- public ---"
  cat "$PUB" 2>/dev/null || true
  echo "--- log ---"
  cat "$LOG" 2>/dev/null || true
  echo "--- dmesg sep ---"
  dmesg | grep -iE 't2_sep|applesmc.*sep|boot.state|response-received|EFMV' | tail -40 || true
  echo "--- mod ---"
  ls -la /dev/t2-aks 2>&1 || true
  modinfo t2_sep_transport 2>&1 | head -8 || true
} >"$NOTE_DIR/INVENTORY_RO_501_${TS}_REPORT.txt"
chmod 0644 "$NOTE_DIR/INVENTORY_RO_501_${TS}_REPORT.txt" "$PUB" "$LOG" 2>/dev/null || true
[[ -f $PRIV ]] && chmod 0600 "$PRIV" 2>/dev/null || true
if [[ $rc -eq 0 && -s $PUB ]]; then
  touch "$STAMP"
fi
exit $rc
