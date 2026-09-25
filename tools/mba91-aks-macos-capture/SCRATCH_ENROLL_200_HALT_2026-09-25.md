# Scratch enroll after option 0x200: still -3 (2026-09-25)

Branch: `research/mba91-aks-ep7`. Statuses and counts only. No finger
contact. No form bytes.

## Verdict

**Option `0x200` accepting the scratch reference does not make an
enroll credential.** The same live context was authorized (SEP status
0, first word 1, handle 5) and then passed to enroll `0x03` version 2,
zero-group 68 B, uid 502. Dispatch `-3`. Cancel 0. No continues.

Post-read: uid 502 still 0, uid 501 still 2. Prep was green. The
sensor was not armed.

`-3` remains "no credential offered." A password-bound context on
this same uid is seen and then refused `22` (C5). The scratch
context is not seen at all. Satisfied policy and a successful
`0x200` are not the mark enroll reads.
