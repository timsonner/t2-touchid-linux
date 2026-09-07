# MBA91 BridgeXPC `en3` capture (Private)

Goal: byte-exact Sequoia macOS BridgeXPC transcript on the T2 NCM link
(HELO + enveloped method-0/3). bent already fixed activation on 23P6068; this
captures MBA91/Air framing for compare and cold-restore research — it is not
a method-0 unblocker.

## One-shot (Terminal on the Air)

```bash
# If you don't have the kit checked out yet:
cd ~/src   # or wherever you keep clones
git clone -b research/mba91-aks-ep7 https://github.com/timsonner/t2-touchid-linux.git
cd t2-touchid-linux/tools/mba91-aks-macos-capture

# Or if already cloned on that branch:
# cd /path/to/t2-touchid-linux && git pull && cd tools/mba91-aks-macos-capture

chmod +x capture-en3-bridgexpc.sh
./capture-en3-bridgexpc.sh
```

Default output: `~/Private/t2-bridgexpc-research/capture-<UTC>/` (mode `700`).

When it says waiting: **lock + Touch ID unlock** (best), or
`sudo killall biometrickitd`. Window defaults to **90s**
(`DURATION_SECONDS=120 ./capture-en3-bridgexpc.sh` to lengthen).

## What you get

| File | Sensitivity |
| --- | --- |
| `en3.pcap` | **PRIVATE** — never git |
| `en3-sanitized-bridgexpc.json` | Credential-free transcript (still keep Private until reviewed) |
| `unified-log.ndjson` | PRIVATE |
| `capture-sha256.txt` | hashes |

## Afterward

Ping Rook. We review the sanitized JSON for HELO / method-0 bytes, then compare
to bent’s `bridge-protocol.py` / `macos-bridge-wire-compare.py`.

See also [BRIDGEXPC_PATH.md](BRIDGEXPC_PATH.md).
