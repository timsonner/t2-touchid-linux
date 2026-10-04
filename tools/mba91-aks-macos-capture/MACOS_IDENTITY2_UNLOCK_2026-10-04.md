# macOS unlock of the Linux-enrolled finger — MBA91 (2026-10-04)

Branch: `research/mba91-aks-ep7`. Normal macOS 15.7.9 build 24G830.
One macOS finger already unlocks this Mac. The Linux-enrolled second
finger `verify-match`es on Omarchy. It does not unlock this Mac.

No identity UUIDs, keybag handles, hardware UUIDs, or biometric
payloads.

## What was tried

The operator pressed the Linux-enrolled finger on the lock screen.
Unlock did not succeed with that finger. Finger 1 still unlocks.

## What this boot showed

Read-only. No enroll, no delete, no Catacomb copy.

`bioutil -c -s` reported **one** biometric template for uid 501.
Unlock is enabled (`bioutil -r`: biometrics for unlock 1).

`biometrickitd` at boot:

1. `loadCatacomb` / `loadCatacombForUser: 501` from
   `/Library/Catacomb` returned 0.
2. `syncTemplateListForUser: removing SEP identity [501:…] because it
   is not present in biometrickitd`
3. `restoreAndSyncTemplates identities 1`

macOS `/Library/Catacomb` still holds the one-finger archive. Linux
`recover-observed` wrote the two-identity archive only under the
Linux store. This boot loaded the macOS archive, then deleted the
extra SEP identity.

## Meaning

The SEP copy of identity 2 is gone **for this macOS session**. It is
not gone from the Linux Catacomb. The next Omarchy boot that loads
that two-identity store should put it back, the same way
`verify-post-reboot` restored count 2 after the enroll reboot. The
next macOS boot will delete it from the SEP again.

A finger press of identity 2 on this Mac cannot match. The template
is not in the live list.

## Do-nots

- Do not copy the Linux Catacomb onto `/Library/Catacomb`. The
  decoder gate for that replace is still closed
  (`enrollment_research/FINDINGS.md`).
- Do not enroll the same finger in System Settings as a debug step.
  That would be a new macOS identity, not a restore of the Linux one.
- No `0x40`, sensor reset, `no_catacomb`, or `0x48`.
- No second bag, and no copy of `native-501.kb` onto `user.kb`.

The Linux handoff is `MACOS_IDENTITY2_LINUX_HANDOFF_2026-10-04.md`.
