# W1 verdict: bound native bag still -5 on ACM verify (2026-09-20)

Branch: `research/mba91-aks-ep7`. C4b gate disabled (verified).
No state change. (Side note, by design: C4b never involves the
fingerprint sensor — password ceremony only.)

## Verdict

**Binding does not enable password ops.** Fresh handle 14 bound to
scratch alias `-502` (`status=0`, UUID live), then
`verify-password-acm` with the creation password: SEP `-5` twice
(second run with certain password). Combined with C4 (`-5` ×3
paths unbound), the wall is now: bound-or-not, both boots,
password correct-or-not cannot be distinguished from outside, but
the consistent `-5` against certainty-corrected input means no
password credential exists on native bags. Their flow's password
never touches a fresh bag directly either — activation (mapping /
owner proofs) is the unported piece, now the sole open direction.

## Standing state

Gates closed. `-502` parked on test handle 14 (reboot clears it).
macOS bags/aliases/templates untouched; SEP 3/3 intact (verify
with a read-only inventory any time — nothing here mutates).
