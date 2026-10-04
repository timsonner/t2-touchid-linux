# Findings

Last updated 2026-10-04 (identity-2 Linux return). Branch
`research/mba91-aks-ep7`.

This is the current narrative for humans and agents. The protocol ledger
is [`enrollment_research/FINDINGS.md`](../enrollment_research/FINDINGS.md).
Dated MBA91 session notes are under
[`tools/mba91-aks-macos-capture/`](../tools/mba91-aks-macos-capture/).
Operator standing is
[`NEXT_STEPS.md`](../tools/mba91-aks-macos-capture/NEXT_STEPS.md).

No identity UUIDs, keybag handles, DMA addresses, or biometric payloads
belong in this file.

## What this software is

Experimental, fail-closed Touch ID for Intel T2 Macs. It talks to
bridgeOS BiometricKit over BridgeXPC and exposes a verification-only
`fprintd` facade for PAM. Enrollment is a separate root-only CLI
(`t2-touchid-enroll`), not `fprintd-enroll`.

macOS remains the recovery environment and the source of the keybag and
Catacomb export.

## Proven machines

| Machine | bridgeOS | What is proven |
| --- | --- | --- |
| MacBookPro16,2 | 23P1072 | Full research: verify, Linux enroll, rename, post-reboot proof, PAM |
| MacBookPro15,2 | 23P350 | Authentication path only (network, keybag, sudo/lock Touch ID) |
| MacBookAir9,1 | 23P6068 / 23.16.16068, BridgeXPC 39 | Keybag unlock, PAM, Linux enroll of a second finger, both fingers `verify-match` after a Linux reboot. A following macOS boot deletes that second SEP identity |

Linux AppleKeyStore **endpoint 7** on the Air is mute. Touch ID on that
Air uses BridgeXPC, not EP7. The EP7 scoreboard is
[`RESEARCH_MBA91_AKS.md`](RESEARCH_MBA91_AKS.md).

## MBA91 path that worked (2026-10-03 / 2026-10-04)

1. Export macOS `user.kb` and Catacomb. Install `user.kb` at
   `/var/lib/t2-touchid/user.kb`. Provision the Catacomb. Load with
   `t2-keybag-load.service`. Unlock both handles. `fprintd-verify`
   matched the macOS finger. PAM fingerprint sudo worked.
2. Linux-owned `native-501.kb` stays unloaded. Password unlock of that
   file returned SEP **-5**. Do not copy it onto `user.kb`.
3. `bridge-xpc-enroll-native-501.py` (creation-reference `0x21` option
   `0x100`) returned status **1** on an empty inventory. That script
   stays parked (`STATUS1_DIAG_2026-09-30.md`).
4. First `t2-touchid-enroll start` accepted the macOS password, start
   status 0, then froze on BiometricKit status **80** before a finger
   prompt. `recover-outcome` found no identity delta.
5. macOS 15.7.9 build 24G830 disassembly: ordinal 80 is
   `operationEndsWithReason:` reason 2, `_state` 4, no `enrollContinue`.
   Linux patch `ddfcdf6` taught `operation-finished`.
6. Second start sent `enrollContinue` through progress 70, 160, 220,
   275, 339, 341, 345, **355**. Then a protocol freeze. The next ordinal
   was not journaled. The SEP had **2** identities; the host Catacomb
   still had 1. `recover-observed` persisted the new one.
7. After reboot, `verify-post-reboot` returned identity count 2.
   `fprintd-verify -f any` matched the macOS index finger, then the
   Linux-enrolled finger.
8. The remaining generic ordinals from the same 24G830 walk are taught
   (`0b81657`): 60 and 61 stay running (`operation-state-changed`);
   51, 58, 62, 65, 80, 99, 502 finish like 80. Journals record the
   event ordinal. That live enroll has not been re-run.
9. Booting this Mac after the Linux enroll, `biometrickitd` loaded
   the one-finger `/Library/Catacomb` and
   `syncTemplateListForUser:` removed the extra SEP identity because
   it was not in biometrickitd. `bioutil` showed one template for uid
   501. The Linux finger does not unlock macOS. Finger 1 still does.
   The Linux Catacomb still holds two identities. Write-up:
   `MACOS_IDENTITY2_UNLOCK_2026-10-04.md`.
10. The next Omarchy boot loaded `user.kb` and unlocked both handles.
    Finger 1 still matched. Identity 2 failed. `t2-touchid-enroll list`
    exited 2: local and live inventories disagree. Linux did not put
    identity 2 back on SEP. Write-up:
    `MACOS_IDENTITY2_LINUX_CONFIRM_2026-10-04.md`. Next:
    `IDENTITY2_NEXT_HANDOFF_2026-10-04.md`.

Write-ups: `LINUX_ENROLL_IDENTITY_2026-10-03.md`,
`MACOS_IDENTITY2_UNLOCK_2026-10-04.md`,
`MACOS_IDENTITY2_LINUX_CONFIRM_2026-10-04.md`,
`IDENTITY2_NEXT_HANDOFF_2026-10-04.md`,
`GENERIC_STATE_LINUX_PATCH_2026-10-04.md`,
`STATUS80_SELECTOR_2026-10-03.md`,
`GENERIC_STATE_SELECTORS_2026-10-03.md`,
`BIOMETRICKIT_STATUS_TECHNIQUE_2026-10-03.md`.

## What does not work (do not retry as a new question)

| Halt | Evidence |
| --- | --- |
| Enroll with no Catacomb | `t2-touchid-enroll` requires exactly one hashed backup and a local store. Status 22 / empty inventory was closed by a macOS first finger, not a Linux bootstrap. |
| macintog/t2touch empty-SEP installer on this Air | Refuses while a fingerprint authority exists. Proven on MacBookPro16,1, not this Air. |
| `native-501.kb` unlock | SEP **-5** |
| Creation-reference enroll | status **1** |
| AKS EP7 on this Air | mute; Touch ID is BridgeXPC |
| `fprintd-enroll` / `fprintd-delete` | not exposed |
| `warm-bringup-mba91.sh` while `user.kb` is loaded | that script loads `native-501.kb` |
| `0x40`, sensor reset, `no_catacomb`, `0x48` | cleared identities on this Air in earlier runs |
| Opcode 74 as a match path | closed matrix |
| `deep` sleep | T2 communication dies until reboot; use `s2idle` |
| Single-identity deletion | not hardware-tested |
| Enroll without a Catacomb backup | broker refuses |
| Unlock this Mac with the Linux-enrolled finger | macOS `loadCatacomb` then `syncTemplateListForUser:` deletes the SEP identity that is missing from `/Library/Catacomb`. `bioutil` count 1. Finger 1 still unlocks. |
| Match identity 2 on Linux after that macOS boot | SEP no longer holds it. Linux Catacomb still lists two. `t2-touchid-enroll list` disagrees. Finger 1 still matches. |
| Copy Linux keybag onto macOS | Linux already uses the macOS `user.kb`. Identity 2 lives in the Catacomb. |
| Copy Linux Catacomb onto `/Library/Catacomb` | decoder gate still closed |

This Air's `fprintd` is verify-only. `fprintd-list` shows a compatibility
name (`right-index-finger`). After the macOS boot, SEP holds Finger 1.
`-f any` matches that remaining enrolled finger.

## Protocol (short)

`src/t2_enrollment_protocol.py` is fail-closed. Envelope `0xe3ff8001`
generic statuses:

- Progress: 100–355, `enrollContinue` required.
- Presence: 63 present, 64 removed.
- Capture feedback: 74, 78, 85–88, 93, 98.
- Enroll fail: 66 cancelled, 67 failed, 68 timed out (`processEnrollFailReason:`).
- Finish: 51, 58, 62, 65, 80, 99, 502 (`operationEndsWithReason:`, no continue).
- State only: 60 (`changeState:` 3), 61 (`changeState:` 2). Operation stays
  running. 61 is not 64.
- Accessory 501 stays blocked.
- Remaining uint32 domain is explicit no-op or freeze.

The 24G830 image UUID used for that walk is
`099725C6-A182-39C2-8104-DA810DE9EDD7`. Recovery / BaseSystem caches do
not contain `BiometricKit`.

## Open

- Linux consistency, only if the operator asks:
  `t2-touchid-manage reconcile-external-deletion` (Path L in
  `IDENTITY2_NEXT_HANDOFF_2026-10-04.md`). Drops the stale local
  identity 2. Finger 1 stays.
- Cross-OS unlock: macOS decoder-only fixture of a copy of the
  Linux-emitted Catacomb (Path M). No `loadCatacomb`, no replace of
  `/Library/Catacomb`, until that note exists.
- One enroll with the generic-state patch, to see whether the host
  Catacomb persists without `recover-observed`, and to journal the
  ordinal after 355. That start mints a new identity. The next macOS
  boot will delete it unless Path M has passed.
- Native `fprintd` enrollment/deletion exposure.
- Multi-user mapped accounts.
- Hardware deletion test.
- EP7 mailbox on Air (independent of BridgeXPC Touch ID).
- `deep` sleep.

## Privacy

Do not commit keybags, Catacomb archives, mutation journals, inventory
logs, or DMA addresses. Inventory captures under
`tools/mba91-aks-macos-capture/INVENTORY_RO_*` are gitignored except
public summaries.
