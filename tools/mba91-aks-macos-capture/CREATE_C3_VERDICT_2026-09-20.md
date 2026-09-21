# C3 verdict: native export cycle proven, UUID-verified (2026-09-20)

Branch: `research/mba91-aks-ep7`. C3 gate disabled (verified).
Shapes/statuses/counts/lengths/hashes only — no UUIDs, no KEK, no
keybag bytes. The saved blob (1540 B) rests root-only 0600 at
`/var/lib/t2-touchid/native-c3-test.kb` and MUST be deleted before
any product use; it is a test artifact, not inventory.

## Verdict

**Endpoint-7 op `0x02` exports the C1-created bag, the file
persists, reloads as a new handle, and the bag UUID matches.**
The native keybag lifecycle (create → export → persist → reload →
verify) is proven on MBA91 short of binding. No macOS artifact
was read, written, or needed at any step.

## Runs

- C3a: lab dispatch with 16 KiB response capacity → `EMSGSIZE`
  halt, no state touched. Infra bug (ours, not SEP's), fixed to
  the C tool's 4096 cap.
- C3b: `sep_status` 0, saved 1540 B, sha256 journaled (private),
  file written 0600, reload → handle 9, `reload_uuid_match: true`,
  `outcome: exported-persisted-reloaded-verified`.
- Post: SEP identities still exactly 3, repeat-equal true. Handles
  8/9 evaporate on reboot; only the test file persists (by design,
  pending deletion).

## What remains for macOS-free (C4+)

Bind (alias + password-set on the native bag) then enroll-native
against it — the FINDINGS non-atomic warnings apply from the bind
step on, so C4 stays paper until designed. Unlock-secret story is
already native-shaped (Linux-chosen password at bind time).
