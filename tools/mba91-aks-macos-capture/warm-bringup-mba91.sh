#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
# MBA91 warm bring-up loader (research only, NOT installed).
#
# Re-establishes the warm SEP session after a reboot with the ONLY
# module parameter set proven to survive warm SEP on this Air:
#   register_ool=1 register_acm=1 aks_start_cpu=0 aks_ep0_nop=0
#   aks_discover=0 aks_device_state_canary=0
# Default params kill the machine (journal-proven 2/2) — this script
# accepts NO parameter overrides by design. Any new set is a new
# staged experiment with its own verdict note, never a flag tweak here.
#
# Keybag: MBA91 research track uses the Linux-owned durable bag
# /var/lib/t2-touchid/native-501.kb (SPECIAL=-501). Do NOT copy/rename
# that bag to user.kb. The installed t2-keybag-load.sh / systemd unit
# still expect user.kb for macOS-export flows elsewhere — this script
# is the MBA91-specific override.
#
# Usage (as root, from the repo root):
#   tools/mba91-aks-macos-capture/warm-bringup-mba91.sh --check
#     Verify current state only (module, nodes, keybag file, session).
#     Safe any time, changes nothing.
#   tools/mba91-aks-macos-capture/warm-bringup-mba91.sh --bring-up
#     Load the module with pinned params, wait past the 9 s death
#     mark, verify all three nodes, load native-501.kb and write
#     /run/t2-touchid/keybag.env from the real handle. Password unlock
#     stays manual (operator terminal):
#       t2-aks-tool unlock-keybag 1 <HANDLE>
#       t2-aks-tool unlock-keybag 1 -501
set -euo pipefail

PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH

KO="$(dirname "$0")/../../src/t2_sep_transport.ko"
AKS_TOOL=/usr/local/sbin/t2-aks-tool
# MBA91 override: native Linux -501 bag (not macOS-export user.kb).
KEYBAG=/var/lib/t2-touchid/native-501.kb
ENV_FILE=/run/t2-touchid/keybag.env
CONF=/etc/t2-touchid.conf
SESSION=1
SPECIAL=-501

fail() { echo "warm-bringup: $*" >&2; exit 1; }

[[ $(id -u) -eq 0 ]] || fail "run as root"
[[ -f $KO ]] || fail "module not built: $KO"
[[ -x $AKS_TOOL ]] || fail "missing $AKS_TOOL"
[[ -f $KEYBAG ]] || fail "missing $KEYBAG (MBA91 expects native-501.kb; do not stage user.kb)"

# vermagic must match the running kernel or insmod refuses (fail-safe).
[[ $(modinfo -F vermagic "$KO" 2>/dev/null) == "$(uname -r)"* ]] \
  || fail "vermagic mismatch: rebuild the module for $(uname -r) first"

mode=${1:-}
case $mode in
  --check)
    echo "KEYBAG: $KEYBAG (present)"
    [[ -d /sys/module/t2_sep_transport ]] \
      && echo "module: loaded" || echo "module: NOT loaded"
    for node in /dev/t2-aks /dev/t2-acm /dev/t2-sep-lab; do
      [[ -e $node ]] && echo "$node: present" || echo "$node: MISSING"
    done
    if [[ -f $ENV_FILE ]]; then
      echo "keybag.env: present"
      # Show staged values without claiming they match a live load.
      sed -n 's/^/  /p' "$ENV_FILE" 2>/dev/null || true
    else
      echo "keybag.env: MISSING"
    fi
    ;;
  --bring-up)
    [[ -d /sys/module/t2_sep_transport ]] \
      && fail "module already loaded; reboot before replacing it"
    # Pinned set — the only warm-surviving configuration. No overrides.
    insmod "$KO" \
      register_ool=1 register_acm=1 \
      aks_start_cpu=0 aks_ep0_nop=0 aks_discover=0 \
      aks_device_state_canary=0
    echo "insmod ok, waiting past the 9 s death mark..."
    sleep 12
    for node in /dev/t2-aks /dev/t2-acm /dev/t2-sep-lab; do
      [[ -e $node ]] || fail "$node missing after bring-up"
    done
    echo "nodes ok: /dev/t2-aks /dev/t2-acm /dev/t2-sep-lab"
    dmesg | tail -3 | grep -q "generation-pinned /dev/t2-acm enabled" \
      || fail "ACM enable line missing from dmesg; halt and inspect"
    # Load native-501.kb; stage keybag.env from the real SEP handle.
    # Do not copy/rename the bag to user.kb.
    output="$("$AKS_TOOL" load-keybag "$KEYBAG" "$SESSION")"
    case "$output" in
      status=0\ handle=*\ response_length=*) ;;
      *)
        fail "load-keybag failed: $output"
        ;;
    esac
    handle=${output#*handle=}
    handle=${handle%% *}
    [[ -n $handle ]] || fail "empty handle from load-keybag"
    "$AKS_TOOL" set-system-keybag "$SESSION" "$handle" "$SPECIAL" \
      | grep -q "^status=0" \
      || fail "set-system-keybag failed"
    install -d -o root -g root -m 0700 /run/t2-touchid
    umask 077
    printf 'T2_KEYBAG_SESSION=%s\nT2_KEYBAG_HANDLE=%s\nT2_KEYBAG_SPECIAL=%s\n' \
      "$SESSION" "$handle" "$SPECIAL" >"$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo "keybag session staged ($SESSION/$handle/$SPECIAL) from $KEYBAG."
    echo "Manual unlock next (local tty):"
    echo "  t2-aks-tool unlock-keybag $SESSION $handle"
    echo "  t2-aks-tool unlock-keybag $SESSION $SPECIAL"
    ;;
  *)
    fail "usage: $0 --check | --bring-up"
    ;;
esac
