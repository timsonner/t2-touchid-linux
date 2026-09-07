#!/bin/bash
# MBA91: Private T2-only BridgeXPC pcap (+ optional unified log), then sanitize.
# Raw pcaps stay under the output directory (mode 700). Do not commit them.
set -euo pipefail

if [[ $(uname -s) != Darwin ]]; then
  echo "Run this on macOS (MBA91)." >&2
  exit 2
fi

script_dir=$(cd -- "$(dirname -- "$0")" && pwd -P)
sanitizer=$script_dir/sanitize-bridgexpc-pcap.py
log_sanitizer=$script_dir/sanitize-bridgexpc-log.py
duration_seconds=${DURATION_SECONDS:-90}

if [[ ! -f $sanitizer ]]; then
  echo "Missing sanitizer: $sanitizer" >&2
  exit 2
fi

stamp=$(date -u +%Y%m%dT%H%M%SZ)
if (( $# >= 1 )); then
  capture_dir=$1
else
  capture_dir=$HOME/Private/t2-bridgexpc-research/capture-$stamp
fi

if [[ -e $capture_dir ]]; then
  if [[ ! -d $capture_dir ]]; then
    echo "output exists and is not a directory: $capture_dir" >&2
    exit 2
  fi
  if [[ -n $(find "$capture_dir" -mindepth 1 -maxdepth 1 -print -quit) ]]; then
    echo "output directory must be empty: $capture_dir" >&2
    exit 2
  fi
fi
mkdir -p "$capture_dir"
chmod 700 "$capture_dir"

sw_vers >"$capture_dir/sw_vers.txt"
ifconfig -a >"$capture_dir/ifconfig-before.txt"
ps aux | grep -iE '[b]iometrickitd|[r]emoted' >"$capture_dir/procs-before.txt" || true

t2_interfaces=$(ifconfig -a | awk '
  /^[A-Za-z0-9][A-Za-z0-9._-]*:/ { iface=$1; sub(/:$/, "", iface) }
  /^[[:space:]]*ether ac:de:48:/ { print iface }
' | sort -u)
printf '%s\n' "$t2_interfaces" >"$capture_dir/t2-interfaces.txt"
if [[ -z $t2_interfaces ]]; then
  echo "No ac:de:48 T2 interface found." >&2
  exit 3
fi

# Prefer en3 when present (MBA91 observed), else all T2 ifaces.
if printf '%s\n' "$t2_interfaces" | grep -qx en3; then
  capture_ifaces=en3
else
  capture_ifaces=$t2_interfaces
fi
printf '%s\n' $capture_ifaces >"$capture_dir/capture-interfaces.txt"

echo "macOS will ask for your password / packet-capture authorization."
sudo -v

pids=""
log_pid=""
cleanup() {
  if [[ -n ${pids:-} ]]; then
    kill -INT $pids 2>/dev/null || true
    wait $pids 2>/dev/null || true
  fi
  if [[ -n ${log_pid:-} ]]; then
    kill -INT "$log_pid" 2>/dev/null || true
    wait "$log_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT HUP INT TERM

for interface_name in $capture_ifaces; do
  case "$interface_name" in
    *[!A-Za-z0-9._-]*) echo "unsafe interface name: $interface_name" >&2; exit 2 ;;
  esac
  # pktap+$iface avoids empty DLT_RAW on AppleUSBNCMData; -y RAW strips pktap hdr.
  capture_interface="pktap,$interface_name"
  sudo tcpdump -i "$capture_interface" -y RAW -n -s 0 -U -w \
    "$capture_dir/$interface_name.pcap" \
    >"$capture_dir/$interface_name-tcpdump.txt" 2>&1 &
  pids="$pids $!"
done

sleep 1
for capture_pid in $pids; do
  if ! kill -0 "$capture_pid" 2>/dev/null; then
    echo "tcpdump exited early — see $capture_dir/*-tcpdump.txt" >&2
    exit 4
  fi
done

log stream --style ndjson --level debug \
  --predicate 'process == "remoted" OR process == "biometrickitd" OR subsystem CONTAINS[c] "Biometric" OR subsystem CONTAINS[c] "Bridge"' \
  >"$capture_dir/unified-log.ndjson" \
  2>"$capture_dir/unified-log-errors.txt" &
log_pid=$!

cat <<PROMPT

PRIVATE BridgeXPC capture running ${duration_seconds}s → $capture_dir

Do this now (any one is enough; unlock is best):
  1) Lock the screen (Ctrl-Cmd-Q), unlock with Touch ID
  2) Or: sudo killall biometrickitd   # relaunch forces a fresh Bridge connect

Do not commit raw pcaps. Waiting…

PROMPT

sleep "$duration_seconds"

kill -INT $pids 2>/dev/null || true
kill -INT "$log_pid" 2>/dev/null || true
wait $pids 2>/dev/null || true
wait "$log_pid" 2>/dev/null || true
pids=""
log_pid=""

ifconfig -a >"$capture_dir/ifconfig-after.txt"
sudo chown "$(id -u):$(id -g)" "$capture_dir"/*.pcap 2>/dev/null || true
chmod 600 "$capture_dir"/*.pcap "$capture_dir"/*.txt "$capture_dir"/*.ndjson 2>/dev/null || true

sanitized_connections=0
for pcap_path in "$capture_dir"/*.pcap; do
  [[ -f $pcap_path ]] || continue
  interface_name=$(basename "$pcap_path" .pcap)
  out=$capture_dir/$interface_name-sanitized-bridgexpc.json
  if python3 "$sanitizer" "$pcap_path" >"$out"; then
    chmod 600 "$out"
    connection_count=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("connection_count",0))' "$out")
    sanitized_connections=$((sanitized_connections + connection_count))
    echo "sanitized $interface_name: connection_count=$connection_count → $out"
  else
    echo "sanitizer failed for $pcap_path (raw pcap kept)" >&2
  fi
done

if [[ -f $log_sanitizer && -s $capture_dir/unified-log.ndjson ]]; then
  if python3 "$log_sanitizer" "$capture_dir/unified-log.ndjson" \
      >"$capture_dir/sanitized-bridgexpc-log.json"; then
    chmod 600 "$capture_dir/sanitized-bridgexpc-log.json"
    echo "sanitized log → $capture_dir/sanitized-bridgexpc-log.json"
  fi
fi

find "$capture_dir" -type f ! -name capture-sha256.txt \
  -exec shasum -a 256 {} + >"$capture_dir/capture-sha256.txt" || true
chmod 600 "$capture_dir/capture-sha256.txt" 2>/dev/null || true

echo
echo "Done. Keep PRIVATE: $capture_dir"
if (( sanitized_connections == 0 )); then
  echo "WARNING: sanitizer saw 0 Bridge connections — try again with Touch ID unlock during the window." >&2
  exit 6
fi
