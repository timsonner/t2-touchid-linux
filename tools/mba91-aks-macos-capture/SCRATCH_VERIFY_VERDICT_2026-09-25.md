# Scratch verify verdict: option 0x100 accepts the retained form (2026-09-25)

Branch: `research/mba91-aks-ep7`. Statuses, lengths, and handles only.
No form bytes, no UUIDs, no passwords.

## Verdict

**Operation `0x21` option `0x100` accepts the scratch bag.** SEP status 0,
response length 12, first word 1. The check used reload handle 3, the
same bag as the create. The macOS bag UUID was unchanged. The new
context's external form was not the retained creation reference; that
reference was the type-5 payload inside the live context.

## What was sent

One shot. A fresh uid-502 ACM context received the saved 16-byte
creation reference as type-5 data, was externalized, and stayed live
for the verify. The request was version 1, session 1, handle 3, a
16-byte secret, no target context, option `0x100`. The context was
deleted afterward. No alias write, no operation `0x18`, no second
verify.

The two-context authorization form was not sent. This module keeps a
single ACM context, and the module is pinned, so a second create would
have been rejected in the kernel before it reached the SEP. Verify-only
is the reference's no-authorization check. It proves the credential
matches. It does not satisfy policy 1007 for enrollment.

## Next

Enrollment still needs an authorized target context live at the same
time as this input. That requires the split-context ACM gate from the
reference module, then one authorization-form `0x100` against handle 3
or a later reload of the same file. Not this window.
