# Catacomb / identity layout vs pre-enroll (2026-09-30 ~22:28 MDT)

Read-only interpretation after macOS one-finger enroll + warm reboot +
private inventory persist (`INVENTORY_RO_501_20260930-222840_*`).
**No Linux enroll / create / `0x21` / second bag.**

## Compare

| Signal | Pre-enroll `…-174149` | Post `…-222437` / `…-222840` |
| --- | --- | --- |
| `0x42` (per-user list) | status **0**, nil → count **0** | status **0**, 20 B → count **1** |
| Global list | nil → **0** | 40 B → count **1** |
| `0x0F` capacity | **5** | **5** |
| `0x41` free (uid-scoped) | **0** (empty / unusable picture) | **2** |
| `0x38` / `0x3A` | status **22** (no user component) | status **0**, lens **16** / **33**, `catacomb_component_present=true` |
| `0x3C` state words | `[0xFFFFFFFF, 1]` (8 B, master-only) | **`[0xFFFFFFFF, 3, 501, 3]`** (16 B) |
| SKS `0x27` | **21 = 0x15** cold | **16 = 0x10** warm |
| Private dump | gated incomplete | **written** (`priv_rc=0`, root `0600` under inventory-journals) |

## What the state words mean

`0x3C` is a list of `(user_id u32, state u32)` pairs (see
`CATACOMB_PRESENCE_2026-09-25.md`):

1. **`0xFFFFFFFF` / `3`** — master Catacomb component present, state word **3**
   (pre-enroll master was state **1** with no user row).
2. **`501` / `3`** — uid **501** is listed in the Catacomb state table with
   state **3** (pre-enroll: **no** 501 row; after `0x48` empty-SEP halt, 501
   disappeared from this list and `0x38` went to 22).

So Linux now sees the same structural picture as a working macOS-enrolled
501: master + user component, UUID/hash queryable, one identity record.

## What status 0 + `0x42=1` + free 2/5 mean for Linux work

- **Inventory gate is green:** protocol v2 attested, lists reconciled,
  Catacomb component present — private inventory is allowed and has been
  persisted for match/UUID research.
- **One enrolled slot, four device max unused, free count 2:** treat `0x41`
  as the SEP’s uid-scoped free-slot figure (not “2 of 5 fingers left” in a
  naive arithmetic sense without more decoding). Capacity stays 5. Do not
  invent a Linux enroll to “fill” free slots yet.
- **SKS `0x10`:** warm enrolled coloring (vs cold `0x15`) — consistent with
  prior successful macOS→Linux warm handoffs.
- **Identity layout:** one 20-byte per-user record + matching global
  40-byte list entry; snapshot A/B stable. Enough to compare UUID/hash
  presence against prior working boots **from the private file**, without
  printing key material into chat/git.

## Hard ban remains

**No Linux enroll-start, bag create, `0x21`, or second bag** until a
deliberate password-bound **match** (or other non-enroll) research step is
chosen. Catacomb presence removes the “empty 501 / status 22” blocker that
made first-finger Linux enroll a dead end; it does **not** authorize a
mutation broker run.

## Recommended next single step (do not run enroll)

**Password-bound match research prep (read-only compare first):**

1. With root, presence-only inspect the private inventory UUID/hash fields
   against a prior working private baseline under Tim’s Private storage
   (do not commit):
   ```bash
   sudo python3 -c 'import json; d=json.load(open("/var/lib/t2-touchid/inventory-journals/inventory-ro-501-20260930-222840.private.json")); print(sorted(d.keys()))'
   ```
2. Then follow the match design / NEXT_STEPS password-ACM path docs — **not**
   enroll:
   - Design: `tools/mba91-aks-macos-capture/MATCH_BROKER_DESIGN_2026-09-20.md`
   - Standing bans + history: `tools/mba91-aks-macos-capture/NEXT_STEPS.md`
   - Credential-in-payload notes: `MATCH74_CREDENTIAL_IN_PAYLOAD_DESIGN.md`

The live match canary named here was approved and run on 2026-10-01.
Handle-1 unlock returned SEP `-5`, so the canary stopped before
`verify-password-acm`. Current orders are the standing block in
`NEXT_STEPS.md`. This note is the Catacomb layout record, not a
permission gate.

## Hygiene leftover

Oneshot still uses `mkdir -p` for `inventory-journals` (umask → `0755` can
re-break private writes). Prefer `install -d -o root -g root -m 0700` in
`/usr/local/sbin/t2-inventory-ro-501` and the repo twin
`tools/mba91-aks-macos-capture/t2-inventory-ro-501.sh`.
