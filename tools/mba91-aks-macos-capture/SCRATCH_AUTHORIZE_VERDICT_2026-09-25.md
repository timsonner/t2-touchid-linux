# Scratch authorize verdict: two-context 0x100 accepted (2026-09-25)

Branch: `research/mba91-aks-ep7`. Statuses, lengths, and handles only.
No form bytes, no UUIDs, no passwords.

## Verdict

**The authorization form of operation `0x21` option `0x100` accepts
the scratch bag.** SEP status 0, response length 12, first word 1.
Reload handle 5. The two ACM contexts were distinct. The macOS bag
UUID was unchanged. No alias was written.

## What was sent

The module now allows one second ACM create while an externalized
type-5 input is still the active context. Same user only, and only
before a target exists. Deleting the target restores the input so
both contexts can be destroyed.

One shot after the warm load. The saved creation reference was
type-5 data on the input context. A second uid-502 context was the
target. The request named handle 5, both 16-byte forms, and option
`0x100`. Both contexts were deleted afterward. The authorization
does not remain live after that delete.

## Next

A finger enroll has to happen in the same hold, after this
authorization and before the target context is deleted. That window
needs a touch. It was not sent here.
