# Agent entry

Start here, then follow one path. Current narrative:
[`docs/FINDINGS.md`](docs/FINDINGS.md). Map: [`docs/README.md`](docs/README.md).

| Need | Read |
| --- | --- |
| What is proven | [`docs/FINDINGS.md`](docs/FINDINGS.md) |
| Operator standing on this Air | [`tools/mba91-aks-macos-capture/NEXT_STEPS.md`](tools/mba91-aks-macos-capture/NEXT_STEPS.md) |
| Tests | [`docs/TESTING.md`](docs/TESTING.md) |
| Enrollment protocol ledger | [`enrollment_research/FINDINGS.md`](enrollment_research/FINDINGS.md) |
| Lab authorization | [`docs/LAB_PROTOCOL.md`](docs/LAB_PROTOCOL.md) |
| EP7 mailbox mute (historical) | [`docs/RESEARCH_MBA91_AKS.md`](docs/RESEARCH_MBA91_AKS.md) |

Dated MBA91 notes under `tools/mba91-aks-macos-capture/` are the evidence
log. `docs/FINDINGS.md` is the live story.

## This Air (MacBookAir9,1)

BridgeXPC Touch ID works: keybag unlock, PAM, a Linux-enrolled second
finger, both fingers `verify-match` after reboot. Linux AKS endpoint 7
is mute; that scoreboard is independent of BridgeXPC Touch ID.

Live bag is `/var/lib/t2-touchid/user.kb` via `t2-keybag-load.service`.
`native-501.kb` stays unloaded.

## Parked shots

These already answered. Another copy is not a new question.

- `bridge-xpc-enroll-native-501.py` (creation-reference `0x21` / `0x100`)
- Password unlock of `native-501.kb` (SEP **-5**)
- Copying `native-501.kb` onto `user.kb`
- `warm-bringup-mba91.sh` while `user.kb` is loaded
- `0x40`, sensor reset, `no_catacomb`, `0x48` while live fingers are the specimen
- Empty-SEP / macintog installer on this Air
- Unloading `t2_sep_transport` or `applesmc`
- Naming a live enroll ordinal from an unjournaled freeze

Linux enroll is `t2-touchid-enroll` (password-bound policy 1007) and
needs exactly one hashed Catacomb backup. One numbered T2/SEP step at
a time. Confirm before the next.

## Privacy and git

Do not commit keybags, Catacomb archives, mutation journals, inventory
json/log/REPORT files, identity UUIDs, keybag handles, DMA addresses,
or biometric payloads. Run `tools/privacy-check.sh` before a push.

Author commits as Tim Sonner
`<66705347+timsonner@users.noreply.github.com>`. Do not set git
config. Push as user `tim`. Do not force-push.
