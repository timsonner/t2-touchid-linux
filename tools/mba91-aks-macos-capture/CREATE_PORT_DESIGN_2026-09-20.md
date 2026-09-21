# Create-port design: t2touch v5 construction via our lab path (2026-09-20)

Branch: `research/mba91-aks-ep7`. **Paper only — no code, no live
windows, no state touched.** Maps the proven MBP16,1 native-create
construction onto MBA91 hardware through our existing research lab
transport.

## Construction (theirs, verified against source)

- Body: create-keybag-v5 (`t2_aks_identity_create.py:
  AKSIdentityCreateV5Request`): `(version=5, session-u64,
  internal_flags, effective_handle=-1)` + blobs
  `(item1, item2, account_uuid[16], item3)` + `(original_flags-u64,
  scalar2-u64)` + `optional_data` blob.
- Minimal native profile (`minimal_create_request`): session,
  `internal_flags=0x4100`, handle -1, **item1 = 16 B ACM external
  form** (fresh password-bound context — a Linux-chosen password
  works; nothing macOS-derived), item2/item3 empty, fresh random
  root-owned account UUID, `original_flags=6`, `scalar2=0`.
- Transport: endpoint-7 operation `0x01` under the AKS v2 envelope.
- Response: `(version, live_handle-i32)` + KEK blob (Linux path
  DISCARDS the KEK — APFS VEK-binding is out of scope).
- Then: export via copy-keybag-v1 (session + live handle) → saved
  object → atomic persist → bag-UUID verify after every load.

## Our route (no product changes)

`/dev/t2-sep-lab` + `t2-sep-lab aks --op 0x01 --ver 2 --body-hex`
sends arbitrary EP7 ops today (lab AKS path has no operation
whitelist; RESEARCH_MBA91_AKS.md). The staged probe is a small
python script driving the lab ioctl directly with wipeable
bytearray buffers (their `inspect_mutable` pattern — KEK bytes
must never reach stdout/logs/disk), NOT the C tool (which
hexdumps responses to stdout).

## Version question (one variable, decided live)

Their tree selects v4 vs v5 per firmware (MBP16,2/23P2048 takes
v4). Reference MBP16,1 ran `23P6068` — our peer HELO string — but
SEP images differ per board by their own warning. C1 runs v5
(the v5 decoder is confirmed against a `23P6068` SEP app in their
static analysis); v4 is the single fallback, never combined.

## C-series (ascending, one shot each, never combined)

| ID | Shot | Gates | Prediction |
|---|---|---|---|
| C1 | v5 create-only via lab path (fresh ACM form from operator password, fresh random account UUID), parse live_handle + KEK length, wipe all secret buffers, read back bag UUID (op `0x06`), STOP — no bind, no delete | warm SEP, module loaded, LIVE default-off + confirm, journal intent pre-dispatch (private path, counts/versions only) | SEP status 0 + valid handle, or a refusal vocabulary entry |
| C2 | Same with v4 | same, only if C1 refuses | 0 or refusal |
| C3+ | Export → persist → bag-UUID verify → bind → enroll-native | only on C1/C2 success, each separately staged | product track |

## Risks (stated plainly)

- Additive, not destructive: a new bag handle touches no
  template, no macOS bag, no identity. Worst case is an orphan
  handle (documented, left alone — no delete path staged until
  D-series discipline extends here).
- KEK/secrets discipline: wipeable buffers only, truncated
  diagnostics (lengths/statuses), privacy scan before any commit.
- Non-atomic failure windows (per FINDINGS) apply to full
  account+bag BINDING, not to a bare create probe — C1/C2 do not
  bind anything, which bounds the blast radius by construction.

## Do-nots

No bind/delete, no APFS/OD side effects, no product wiring, no
`0x40`/reset, no default-param anything (module already pinned),
no KEK persistence anywhere.
