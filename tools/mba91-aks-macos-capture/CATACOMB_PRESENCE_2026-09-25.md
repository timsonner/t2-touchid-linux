# Catacomb presence: uid 502 is absent (2026-09-25)

Branch: `research/mba91-aks-ep7`. Statuses and counts only. Read-only.
No component bytes, no UUIDs, no enroll.

## Verdict

**User 502 has no Catacomb component. User 501 does.** Queries were
`0x38` (component UUID), `0x3a` (component hash), and one global
`0x3c` state list.

| uid | 0x38 status | UUID | 0x3a status | in the 0x3c list |
|---|---|---|---|---|
| 501 | 0 | 16 bytes, nonzero | 0, 33 bytes, present | state 7 |
| 502 | 22 | 16 zero bytes | 22 | absent |

The state list is 16 bytes, two records: the master component
(`user_id` 4294967295, state 3) and uid 501 (state 7). Status `22`
on the 502 queries is the same word enroll returns. The component
check fails before a sensor command for that user.
