# Scratch alias -502: enroll can see the bag, still status 22 (2026-09-25)

Branch: `research/mba91-aks-ep7`. Statuses and counts only. No finger
contact. No form bytes.

## Verdict

**Binding the scratch bag to `-502` changed enroll from `-3` to `22`.**
The credential is now visible. The user is still not a provisioned
account. The sensor did not open.

`set-system-keybag` of scratch handle 5 onto alias `-502` returned
status 0. Alias `-501` still names the macOS bag. `keybag.env` is
still session 1 / handle 6 / special `-501`. Option `0x200` against
`-502`, using the saved creation reference, returned SEP status 0.
Enroll `0x03` for uid 502 then returned dispatch `22`. Cancel 0.
Uid 502 remains 0 identities. Uid 501 remains 2.

`-3` was "this context was not checked against the user's registered
bag." `22` is the same account refusal C5 saw when the credential was
already visible. Prep was green.
