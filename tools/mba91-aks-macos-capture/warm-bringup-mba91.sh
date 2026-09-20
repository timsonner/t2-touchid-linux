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
# Usage (as root, from the repo root):
#   tools/mba91-aks-macos-capture/warm-bringup-mba91.sh --check
#     Verify current state only (module, nodes, keybag session file).
#     Safe any time, changes nothing.
#   tools/mba91-aks-macos-capture/warm-bringup-mba91.sh --bring-up
#     Load the module with pinned params, wait past the 9 s death
#     mark, verify all three nodes, load the keybag and write the
#     session file. Password unlock stays manual (operator terminal):
#       t2-aks-tool unlock-keybag 1 1
#       t2-aks-tool unlock-keybag 1 -501
set -euo pipefail

PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH

KO="$(dirname "$0")/../../src/t2_sep_transport.ko"
AKS_TOOL=/usr/local/sbin/t2-aks-tool
KEYBAG=/var/lib/t2-touchid/user.kb
ENV_FILE=/run/t2-touchid/keybag.env
CONF=/etc/t2-touchid.conf

fail() { echo "warm-bringup: $*" >&2; exit 1; }

[[ $(id -u) -eq 0 ]] || fail "run as root"
[[ -f $KO ]] || fail "module not built: $KO"
[[ -x $AKS_TOOL ]] || fail "missing $AKS_TOOL"
[[ -f $KEYBAG ]] || fail "missing $KEYBAG"

# vermagic must match the running kernel or insmod refuses (fail-safe).
[[ $(modinfo -F vermagic "$KO" 2>/dev/null) == "$(uname -r)"* ]] \
  || fail "vermagic mismatch: rebuild the module for $(uname -r) first"

mode=${1:-}
case $mode in
  --check)
    [[ -d /sys/module/t2_sep_transport ]] \
      && echo "module: loaded" || echo "module: NOT loaded"
    for node in /dev/t2-aks /dev/t2-acm /dev/t2-sep-lab; do
      [[ -e $node ]] && echo "$node: present" || echo "$node: MISSING"
    done
    [[ -f $ENV_FILE ]] \
      && echo "keybag.env: present" || echo "keybag.env: MISSING"
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
    "$AKS_TOOL" load-keybag "$KEYBAG" 1 | grep -q "^status=0" \
      || fail "load-keybag failed"
    "$AKS_TOOL" set-system-keybag 1 1 -501 | grep -q "^status=0" \
      || fail "set-system-keybag failed"
    install -d -o root -g root -m 0700 /run/t2-touchid
    printf 'T2_KEYBAG_SESSION=1\nT2_KEYBAG_HANDLE=1\nT2_KEYBAG_SPECIAL=-501\n' \
      >"$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo "keybag session staged (1/1/-501). Manual unlock next:"
    echo "  t2-aks-tool unlock-keybag 1 1"
    echo "  t2-aks-tool unlock-keybag 1 -501"
    ;;
  *)
    fail "usage: $0 --check | --bring-up"
    ;;
esac
