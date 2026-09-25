# Scratch create halt: endpoint 7 silent on this boot (2026-09-24)

Branch: `research/mba91-aks-ep7`. No keybag was created, exported,
bound, or unlocked. No alias was written. `user.kb` was not modified.
Shapes and statuses only.

## Verdict

**The scratch create did not run, because endpoint 7 is not answering
on this boot.** The warm loader survived (nodes present, past the 9 s
mark, ACM SCRD replied in 1 ms), then `load-keybag` of the existing
macOS bag timed out twice. Mailbox inbox stayed `0x25501` across both
posts; outbox advanced `0x26601` then `0x27701`; MSI counts stayed 0;
OOL out stayed empty. Two messages went out and nothing came back.

Probe-entry CPU controls were `+0x8028=0x7f +0x8040=0x0 +0x8048=0x0`.
The pinned warm set does not start the CPU. That set loaded this same
keybag on 2026-09-20 after a Linux reboot. This boot follows a
multi-day power-off, so the SEP is not in that warm-reboot condition.
Starting the CPU now would be a different experiment: OOL is already
registered and two endpoint-7 posts are unanswered. It was not tried.

## What did land

The module now accepts ACM command `0x28`, the type-5 identity-secret
set, with the same context match, empty response, and fixed framing
as externalize. That is the credential producer a Linux-owned bag
needs, and it does not use the macOS password. Unit tests cover the
lifecycle and the command bytes. The running module is that build.
`/dev/t2-aks`, `/dev/t2-acm`, and `/dev/t2-sep-lab` are up, and the
module is pinned until reboot.

## Next boot

Reboot before another attempt. `rmmod` cannot drop the OOL
registration. On the next boot, bring the transport up with the same
pinned warm set and require one successful `load-keybag` before any
create. If endpoint 7 is silent again, stop. A CPU-start trial is a
separate, cold-boot window, not a follow-up poke on a pinned module.
