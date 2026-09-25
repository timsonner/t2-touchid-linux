# Scratch option 0x200 verdict: selector accepts the retained form (2026-09-25)

Branch: `research/mba91-aks-ep7`. Statuses and policy fields only.
No form bytes, no finger, no enroll.

## Verdict

**Operation `0x21` option `0x200` accepts the scratch bag.** SEP status
0, response length 12, first word 1. Handle 5, the reload still live
from the authorization window. The macOS bag UUID was unchanged.

The secret was the saved 16-byte creation reference. The context it
authorized was a live uid-502 ACM context whose type-5 data was that
same reference. One shot. The context was deleted afterward.

## Policy on that context

Read after the accept, before delete:

| field | value |
|---|---|
| satisfied | true |
| requirement present | true |
| requirement type | 1 (passcode) |
| requirement state | 2 |
| requirement flags | 1 |

No earlier password-bound policy read recorded state and flags, so
this does not by itself prove the enroll stamp. It is the selector
the working enroll path uses, and it accepted this reference.

## Next

An enroll has to repeat this `0x200` and dispatch `0x03` before the
context is deleted. Status `22` remains the likely refusal if user
502 is still not a provisioned account. Not this window.
