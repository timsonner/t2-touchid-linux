# Scratch create verdict: Linux-owned bag persisted (2026-09-25)

Branch: `research/mba91-aks-ep7`. Lengths, statuses, and handles only.
No passwords, no UUIDs, no keybag bytes.

## Verdict

**One scratch keybag was created, exported, and reloaded on MBA91
after the macOS fingerprint handoff.** Endpoint 7 answered. The
macOS bag's UUID was unchanged, and the new bag's UUID is distinct.
The 16-byte creation reference was retained. No alias was written.

## Bring-up

Clean Linux boot after a macOS Touch ID unlock and a warm restart.
Pinned warm set, no CPU start. `load-keybag` of the existing macOS
bag returned success and staged session 1 / handle 1 / special
`-501`. No mailbox timeout.

## Create

ACM command `0x28` installed a random type-5 secret on a fresh
context for scratch uid 502, then externalized that context. One
endpoint-7 operation `0x01` version 5 (`internal_flags=0x4100`,
`original_flags=6`) returned SEP status 0, live handle 2, KEK
length 162. Immediate operation `0x02` export returned status 0,
saved length 1540. Reloading that file produced handle 3, and its
bag UUID matched handle 2. The ACM context was deleted afterward.

Root-only files, mode 0400 for the reference and the account UUID,
mode 0600 for the saved bag:

- `/var/lib/t2-touchid/native-scratch.kb`
- `/var/lib/t2-touchid/native-scratch.form`
- `/var/lib/t2-touchid/native-scratch.account`

Handles 2 and 3 evaporate on reboot. The files are the durable copy.
The macOS bag stays handle 1, still bound to `-501`.

## Next

Activation is a separate window. The retained form is the old
credential for the change-secret path. It has not been presented
back to the SEP yet. No enroll, no daemon cutover.
