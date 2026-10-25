# The Catacomb secure blob is stateful, not derivable — MBA91 (2026-10-24)

Branch: `research/mba91-aks-ep7`

No identity UUIDs, keybag handles, hardware UUIDs, or blob bytes.

## Question

Is `CatacombSecureData` a function of the identity set? If it were,
a matching archive could be constructed for `/Library/Catacomb`. If it
is not, only SEP can produce one, and no amount of editing gets there.

## Method

`tools/catacomb-decode-fixture.swift` on two **macOS-written**
components that hold the same single identity:

| | A | B |
| --- | --- | --- |
| source | 2026-10-01 macOS export | live `/Library/Catacomb`, copied |
| `user_000001f5.cat` | 22963 B | 29921 B |
| mtime | 2026-10-03 18:02 | 2026-10-04 09:46 |
| state | before the Linux enroll | after the reconciliation |

The identity metadata matches in both: same name (`Finger 1`), same
creation time, same identity UUID (compared as a hash), same type,
attribute, flags and entity number, and `BKIdentityMatchCount` 1 in
both. The only difference is `BKIdentityUpdateCount`: **1 vs 2**.

## Result

| Field | A | B |
| --- | --- | --- |
| file bytes | 22963 | 29921 |
| secure blob | 21440 | 28394 |
| blob header | `LTFC` v10 uid 501 | identical |
| common prefix | 33 bytes (header only) | |
| `LTFC` occurrences in blob | 1 | 1 |
| identity count | 1 | 1 |
| blob SHA-256 | differs | |

The header is 33 bytes, so the sealed payload is 21407 B in A and
28361 B in B: **+6954 B, +32%, for the same identity set.** There is
exactly one `LTFC` envelope in each, so this is not a second record
being appended.

## What it means

- The blob is **not a function of the identity set**. Same identity,
  same list, different seal.
- It is one opaque envelope, not a per-identity container. The Linux
  two-identity component is not "two records" that can be spliced.
- So the blob cannot be computed, synthesized, or edited into agreement
  with anything. Only SEP produces one, and it re-seals on every save.
- Consequence: forging is moot. The Linux-enrolled identity is already
  SEP-sealed, by SEP, through the normal save path. The macOS boot
  still deletes it, because the deletion is a host-side list
  reconciliation, not a seal check.
- The Linux two-identity blob should be about 37.8 kB (derived from the
  39314 B file minus the ~1.5 kB envelope). Not measured.

## What it does not answer

- **Rollback policy.** Whether SEP accepts a blob it sealed two
  generations ago. That is a load test, and a rejected load is the
  error-269 path that deletes Catacomb files.
- **What the +6954 B carries.** Per-save epoch, a wrapped class key, or
  a retained template are all consistent with the sizes. The format is
  sealed and there is no public decoder.
- **Whether `0x3a` moves with the blob.** The repo records only
  presence and length: status 22 with no component, len 0 on an empty
  boot, len 32 after enroll, and v1 succeeds even when `0x38`/`0x3c`
  fail. Values are redacted in every capture, so no cross-state
  correlation exists yet.

## Reproduce

```sh
# A, from the private 2026-10-01 export
tar xzf <export>/t2-touchid-catacomb.tar.gz -C /tmp/catacomb-a
./tools/catacomb-decode-fixture.swift /tmp/catacomb-a/Library/Catacomb/*/user_000001f5.cat

# B, a copy of the live component
cp /Library/Catacomb/*/user_000001f5.cat /tmp/catacomb-b.cat
./tools/catacomb-decode-fixture.swift /tmp/catacomb-b.cat
```

Both are copies. The tool never calls `loadCatacomb`, `save`, delete,
or any biometric command.
