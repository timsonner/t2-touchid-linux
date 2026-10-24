# WPA3-Personal on this Air under Omarchy

Branch: `research/mba91-aks-ep7`
Status: runbook; root cause source-verified, **not yet confirmed on this unit**

Scope: WPA3-Personal (SAE) on the `BCM4377b` in a MacBookAir9,1. Not
802.1X/Enterprise, not WPA3-Transition-Mode tuning. Background and the
schematic side: [`HARDWARE_A2179.md`](HARDWARE_A2179.md) §3.1.

Keep the network name and passphrase out of this repo, out of commits and
out of pasted logs. Use a local variable:

```sh
SSID='your-network'      # set in your shell, never commit
```

## 0. What "working" means

Three separate things, in order. Most failed attempts stop at the first:

1. the driver exposes an SAE path at all,
2. the supplicant completes SAE and the association,
3. DHCP and routing come up afterwards.

Only step 1 is broken by Omarchy's quirk.

## 1. Baseline

```sh
cd ~/Projects/t2-touchid-linux
./tools/wifi-wpa3-check.sh
```

On a stock Omarchy install on this Air you should see:

```
feature_disable 532480 (0x82000)
FAIL  BRCMF_FEAT_SAE is disabled (bit 19) ...
FAIL  BRCMF_FEAT_FWSUP is disabled (bit 13) ...
```

`532480` is `0x82000`. Write down the value so step 4 has something to
compare against.

## 2. Clear the Omarchy quirk

The shipped file is `/etc/modprobe.d/brcmfmac.conf`. Do not edit it —
Omarchy re-checks it on update. Add an override that sorts after it; for a
repeated module parameter the last assignment wins, so this survives
`omarchy-update` re-running `migrations/1786391100.sh`.

```sh
sudo cp -a /etc/modprobe.d/brcmfmac.conf /root/brcmfmac.conf.omarchy.bak

sudo tee /etc/modprobe.d/zz-brcmfmac-sae.conf >/dev/null <<'EOF'
# Omarchy's brcmfmac.conf sets feature_disable=0x82000. In
# brcmfmac/feature.h bit 19 (0x80000) is BRCMF_FEAT_SAE, not FWAUTH
# (bit 20, 0x100000), and cfg80211 only advertises SAE offload behind
# FWSUP. This firmware has no host-side SAE path, so the quirk leaves no
# WPA3-SAE route at all. Clear it.
options brcmfmac feature_disable=0
EOF
```

If `modinfo -n brcmfmac` printed nothing in step 1, brcmfmac is built in
and modprobe.d is ignored — put `brcmfmac.feature_disable=0` on the kernel
command line instead and skip to step 3.

## 3. Reboot

```sh
sudo reboot
```

A module reload (`modprobe -r brcmfmac && modprobe brcmfmac`) can work, but
the radio is usually in use and the firmware has to re-download.

## 4. Confirm the capability came back

```sh
./tools/wifi-wpa3-check.sh
cat /sys/module/brcmfmac/parameters/feature_disable    # want 0
iw phy | grep -iE 'sae|mfp'
```

Want: `0`, plus at least one SAE line (normally `SAE_OFFLOAD`) and one MFP
line. If there is still no SAE line, stop — see step 7.

## 5. Join

Pick whichever front end is active (the check script prints it):

```sh
# iwd / impala
iwctl station list
iwctl station wlan0 scan
iwctl station wlan0 get-networks
iwctl station wlan0 connect "$SSID"     # prompts for the passphrase

# or the TUI
impala

# NetworkManager
nmcli device wifi connect "$SSID" password "$PW"
```

A failed attempt leaves a profile behind, and iwd will keep reusing it:

```sh
sudo ls /var/lib/iwd/                   # filenames are SSIDs, do not paste
sudo rm "/var/lib/iwd/$SSID.psk"
```

Then `iwctl station wlan0 disconnect && iwctl station wlan0 connect "$SSID"`.

## 6. Prove it is actually up

```sh
iw dev wlan0 link
ip -4 addr show wlan0
ip route | head -3
gw=$(ip route | awk '/default/ {print $3; exit}')
ping -c3 "$gw"
ping -c3 1.1.1.1
getent hosts archlinux.org
journalctl -b -u iwd | grep -iE 'sae|pmf|handshake|reason|deauth' | tail -20
```

Good: `link` shows the AP and a bitrate, `wlan0` has a DHCP address, the
gateway and `1.1.1.1` both answer, DNS resolves, and the journal is not
repeating `reason=` / deauth lines.

`iw dev wlan0 link` prints the SSID to your terminal. That is fine locally;
do not paste it into an issue.

## 7. If it still does not connect

| Symptom | Cause | Next |
| --- | --- | --- |
| No SAE line in `iw phy` after `feature_disable=0` | firmware has no `sae_ext` and no offload | WPA3-only is impossible on this chip; run the AP in WPA2 or WPA2/WPA3 transition mode |
| SAE advertised, association times out | PMF, stale profile, or band | check `DisablePMF` is not `true` in `/etc/iwd/main.conf`, delete the `.psk` profile, retry on 5 GHz, disable BT (2.4 GHz interference) |
| Associates, no DHCP | not an SAE problem | check `systemd-networkd` / NetworkManager, `networkctl status` |
| WPA2 worked before and broke now | re-enabling FWSUP restored the broken 4-way offload | roll back (step 8) and choose which network matters |
| Worked, then failed after an update | quirk re-applied, or kernel/firmware changed | re-run the check script; `omarchy-update` can rewrite `/etc/modprobe.d` |

Also worth reading: `dmesg | grep -i brcmf` for firmware load errors, and
`journalctl -b -u iwd` around the attempt.

## 8. Rollback

```sh
sudo rm /etc/modprobe.d/zz-brcmfmac-sae.conf
sudo reboot
```

The Omarchy file was never modified, so nothing else to undo.

## 9. Why this is the opposite of the usual advice

The common `brcmfmac.feature_disable=0x82000` advice fixes wpa_supplicant
2.11's broken four-way-handshake offload on chips whose firmware *also*
offers host-side SAE. On the `C-4377__s-B3` firmware there is no host SAE,
so clearing `SAE` removes the only path to WPA3. Hence `0` here, `0x82000`
elsewhere — same driver, different firmware capability.

Upstream: [omarchy#9802](https://github.com/omacom/omarchy/issues/9802),
bit definitions in
`drivers/net/wireless/broadcom/brcm80211/brcmfmac/feature.h`, and the
`FWSUP` gate in `brcmf_setup_wiphy()`.
