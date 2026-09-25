# Scratch reload halt after reboot (2026-09-25)

Branch: `research/mba91-aks-ep7`. The saved scratch bag was not
installed as `-501`. No Catacomb save. No enroll. No finger contact.

## Verdict

**The scratch bag file will not load on this boot.** Warm bring-up
succeeded: macOS `user.kb` is session 1 / handle 1 / special `-501`.
`load-keybag` of `native-scratch.kb` returned SEP status `-9`. The
alias install was not attempted.

User 501 still has 2 identities. Its Catacomb UUID query returns
status 0 with a nonzero component. `-501` was left on the macOS bag.
