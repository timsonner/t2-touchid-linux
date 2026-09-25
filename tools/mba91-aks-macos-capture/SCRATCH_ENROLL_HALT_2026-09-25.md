# Scratch enroll halt: both live forms dispatch -3 (2026-09-25)

Branch: `research/mba91-aks-ep7`. Statuses and counts only. No finger
contact. No form bytes.

## Verdict

**Do not place a finger.** Uid 502 enroll never opened. Two starts,
each after a fresh option-`0x100` authorization (SEP status 0, first
word 1), both returned dispatch `-3`. Cancel was 0. Uid 502 stayed
empty. Uid 501 stayed at 2.

`-3` is the same word the token-free enroll returns: no credential
offered. The first payload carried the authorized target context.
The second carried the type-5 input context. Session prep was green
both times (device list, sensor, config, xART, enabled-unlock).

A policy read on the target, in between, returned `satisfied: true`
with passcode requirement type 1 still present. That ACM result is
not the credential the enroll opcode accepts. The enroll that opens
on uid 501 carries a password-bound policy context. Neither scratch
form was treated as that.

## State

Scratch bag handle 5 was still live. No alias write. No continue
opcodes. The sensor was not armed.
