#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
#
# Read-only WPA3-Personal readiness check for brcmfmac on Apple/T2 Macs.
#
# Changes nothing, needs no root, and prints no network names. Exit 0 means
# the driver is exposing an SAE path and the join is worth attempting; exit 1
# means something above the supplicant has to change first.
#
# Runbook: docs/WIFI_WPA3_OMARCHY.md
#
#   ./tools/wifi-wpa3-check.sh
#
set -uo pipefail

rc=0
hdr() { printf '\n== %s\n' "$*"; }
ok() { printf '  ok    %s\n' "$*"; }
bad() { printf '  FAIL  %s\n' "$*"; rc=1; }
info() { printf '  ..    %s\n' "$*"; }

hdr "host"
info "kernel  $(uname -r)"
info "model   $(cat /sys/class/dmi/id/product_name 2>/dev/null || echo unknown)"

hdr "driver"
if [[ -d /sys/module/brcmfmac ]]; then
  ok "brcmfmac loaded"
else
  bad "brcmfmac is not loaded; nothing below applies"
fi

if modinfo -n brcmfmac >/dev/null 2>&1; then
  info "module  $(modinfo -n brcmfmac)"
else
  info "module  none (builtin?); modprobe.d will not apply, use the kernel cmdline"
fi

if [[ -r /sys/module/brcmfmac/parameters/feature_disable ]]; then
  fd=$(cat /sys/module/brcmfmac/parameters/feature_disable)
  info "feature_disable $fd (0x$(printf '%x' "$fd"))"
  if ((fd & 0x80000)); then
    bad "BRCMF_FEAT_SAE is disabled (bit 19): firmware SAE offload is off"
  fi
  if ((fd & 0x2000)); then
    bad "BRCMF_FEAT_FWSUP is disabled (bit 13): SAE offload is gated behind it, so it is off too"
  fi
  if ((fd == 0)); then
    ok "firmware supplicant and SAE offload both enabled"
  fi
fi

hdr "modprobe.d"
shopt -s nullglob
found=0
for f in /etc/modprobe.d/*.conf /run/modprobe.d/*.conf \
  /usr/lib/modprobe.d/*.conf /lib/modprobe.d/*.conf; do
  while IFS= read -r line; do
    found=1
    info "$f:$line"
  done < <(grep -nE '^[[:space:]]*options[[:space:]]+brcmfmac' "$f" 2>/dev/null || true)
done
((found)) || info "no brcmfmac options file"

hdr "kernel cmdline"
if tr ' ' '\n' < /proc/cmdline | grep -q '^brcmfmac\.'; then
  tr ' ' '\n' < /proc/cmdline | grep '^brcmfmac\.' | sed 's/^/  ..    /'
else
  info "no brcmfmac.* parameter"
fi

hdr "nl80211 capabilities"
if command -v iw >/dev/null 2>&1; then
  phy=$(iw phy 2>/dev/null || true)
  if grep -qi 'sae' <<<"$phy"; then
    ok "SAE advertised by the driver"
  else
    bad "no SAE capability in iw phy"
  fi
  if grep -qi 'mfp' <<<"$phy"; then
    ok "MFP (802.11w) advertised"
  else
    bad "no MFP capability in iw phy; WPA3 requires PMF"
  fi
  grep -iE 'sae|mfp|802\.11w' <<<"$phy" |
    sed 's/^[[:space:]]*/  ..    /' | head -8
else
  info "iw not installed (pacman -S iw); capability check skipped"
fi

hdr "supplicant"
for s in iwd NetworkManager wpa_supplicant; do
  if systemctl is-active --quiet "$s" 2>/dev/null; then
    ok "$s active"
  else
    info "$s inactive"
  fi
done
if [[ -r /etc/iwd/main.conf ]] &&
  grep -qiE '^[[:space:]]*DisablePMF[[:space:]]*=[[:space:]]*true' /etc/iwd/main.conf; then
  bad "/etc/iwd/main.conf sets DisablePMF=true; WPA3 requires PMF"
fi

hdr "firmware"
for f in /usr/lib/firmware/brcm/brcmfmac4377-pcie.bin \
  /lib/firmware/brcm/brcmfmac4377-pcie.bin; do
  [[ -f $f ]] && info "$f ($(stat -c %s "$f") bytes)"
done
if command -v ethtool >/dev/null 2>&1; then
  for i in /sys/class/net/wl*; do
    [[ -e $i ]] || continue
    ethtool -i "$(basename "$i")" 2>/dev/null |
      grep -E '^(driver|version|firmware-version)' | sed 's/^/  ..    /'
  done
fi

hdr "kernel log (brcmfmac)"
journalctl -b -k --no-pager 2>/dev/null | grep -i brcmf | tail -5 |
  sed 's/^/  ..    /' || info "nothing this boot"

hdr "verdict"
if ((rc == 0)); then
  printf '  ready: an SAE path is exposed. Attempt the join per\n'
  printf '  docs/WIFI_WPA3_OMARCHY.md step 5.\n'
else
  printf '  not ready: see the FAIL lines above.\n'
  if [[ -n ${fd:-} ]] && ((fd & 0xa000)); then
    printf '  If the SAE/FWSUP bits are the only failures, clear the Omarchy\n'
    printf '  quirk (docs/WIFI_WPA3_OMARCHY.md step 2) and re-run after reboot.\n'
  fi
fi
exit "$rc"
