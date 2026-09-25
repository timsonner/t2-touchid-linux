# New bag on -501 and user Catacomb save: enroll still 22 (2026-09-25)

Branch: `research/mba91-aks-ep7`. Statuses and lengths only. No form
bytes, no UUIDs, no finger contact.

## Verdict

**A new bag installed as `-501`, followed by a successful user-501
Catacomb save, did not open enroll.** Dispatch stayed `22`. The two
existing identities survived. `-501` has been pointed back at the
macOS bag.

## What happened

Warm session, macOS bag on handle 1. One v5 create for account 501
returned SEP status 0, live handle 8. Export returned status 0, 1540
bytes, kept with the creation reference in `native-501.kb` and
`native-501.form`. No second alias was used.

`set-system-keybag` of handle 8 onto `-501` returned status 0. Handle
1 still named the macOS bag. User-component prepare, complete, and
confirm all returned status 0. The secure blob was 62706 bytes and
began with `LTFC`. Component state for uid 501 went from 7
(`needs_save`) to 3. Identity count stayed 2. The component UUID
query stayed status 0 with a nonzero body.

Option `0x200` against `-501` with the new creation reference returned
SEP status 0. Enroll for uid 501 then returned `22`. Cancel was 0.

## After

`-501` was bound back to handle 1 and checked: it names the macOS bag
again. Identity count 2 and Catacomb status 0 were re-read before that
restore, while the new bag was still the alias.
