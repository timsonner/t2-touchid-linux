# Policy compare: scratch stamp matches a real password bind (2026-09-25)

Branch: `research/mba91-aks-ep7`. Policy fields only. No password, no
form bytes, no enroll.

## Verdict

**The scratch bag's option-`0x200` result leaves the same policy
record as a macOS-password bind.** Handle 6, a second load of the
macOS bag. One password verification, SEP accept (`bind_exit` 0).
The context was deleted afterward.

| | satisfied | type | state | flags |
|---|---|---|---|---|
| before password | false | 1 | 1 | 1 |
| after password | true | 1 | 2 | 1 |
| scratch bag, earlier | true | 1 | 2 | 1 |

State 1 is the unfulfilled passcode requirement. State 2 is the
fulfilled one. The scratch context had already reached state 2.

## What this decides

Enroll does not use this tuple to tell the two contexts apart. A
uid-502 context password-checked against the macOS bag is visible
and then refused `22` (C5). A uid-502 context checked against the
scratch bag, with this same fulfilled record, is invisible (`-3`).
The difference is which bag performed the verification, not the
policy fields.
