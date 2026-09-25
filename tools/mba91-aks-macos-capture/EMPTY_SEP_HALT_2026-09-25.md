# Whole-user removal: biometric container gone, keybag remains (2026-09-25)

Branch: `research/mba91-aks-ep7`. One command `0x48` for Apple user 501.
No retry. No new bag. No enroll.

## Verdict

**Command `0x48` was accepted and the biometric user is no longer
listed. The macOS keybag is still installed at `-501`.** The
empty-SEP first-identity path was not started.

| read | before | after |
|---|---|---|
| `0x42` identity count for 501 | 2 | 0, then 0 again |
| `0x3c` non-master users | 501 | none |
| `0x38` component query | not read | status 22, zero body |
| alias `-501` | macOS bag | still present, 16-byte UUID |

The primary-identity read, operation `0x51` in the reference's
absent-primary layout, returned a remote I/O error and no absent
pattern. A present `-501` bag is enough to keep that path closed.
Their installer will not create the first identity until that read
says the primary identity is absent.

## Recovery

The Apple account and its keybag are still in the T2. The enrolled
fingers and the user component list are not. Re-enrolling from macOS
is the way back. No Linux create was sent on top of the remaining bag.
