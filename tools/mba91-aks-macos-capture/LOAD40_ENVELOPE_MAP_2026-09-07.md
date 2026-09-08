# MBA91 `0x40` envelope map (macOS Common vs Mesa LTFC push)

Public-safe. Draws on `CATACOMB_ONDISK.md`, `CATACOMB_BRIDGE_SEQUENCE.md`, bent
README / `biometric-command.py`, and MBA91 Omarchy load A/Bs through
`LOAD_CAL_0x20_2026-09-07.md`.

## Two different “loads”

| Path | What it does | Evidence |
| --- | --- | --- |
| **A. macOS Common filesystem load** | `loadCatacomb` → `loadCatacombForComponent` → read `.cat` → **`unarchiveCatacombData`** → `addIdentityObjects` / `restoreAndSyncTemplates` | Sequoia boot logs (enrolled + empty). Heavy Mesa catacomb opcodes (**60/61/62/63**) are on **save**, not this boot load |
| **B. Mesa `0x40` LoadCatacomb** | Push an opaque blob on the wire (`COMMAND_LOAD_CATACOMB`) | bent `current_catacomb_secure_data_fields` / `load_catacomb_fields`; our Omarchy probes |

We have been exercising **B** with LTFC extracted from `.cat`’s
`CatacombSecureData`. macOS warm/enrolled bring-up that restores `0x42` is
primarily **A** (and SEP already holding templates — matches power-off
preserve without Linux `0x40`).

**Implication:** status **257** on **B** does not prove macOS “loadCatacomb”
failed; it may mean “this Mesa push is rejected in the current SEP/host
state,” including **already-populated** catacomb.

## What we send (path B)

bent:

```text
0x40, version=1, value=0, payload=<opaque bytes>, out_cap=0
```

- `current_catacomb_secure_data_fields(blob)` — any nonempty opaque ≤ max  
- `load_catacomb_fields(user_id, blob)` — also requires `uid` at LTFC offset **8**

MBA91 Private extracts (from NSKeyedArchiver `.cat`):

| Blob | len | LTFC @0 | ver @4 | uid @8 |
| --- | --- | --- | --- | --- |
| master | 244 | `LTFC` | 10 | `0xffffffff` |
| user 501 | 24542 | `LTFC` | 10 | 501 |

Same family as CompleteSave **62** replies (`LTFC`/`CFTL`) per on-disk notes —
but we have **not** proven SecureData extract ≡ wire CompleteSave body.

## What macOS `.cat` contains (path A input)

NSKeyedArchiver, **not** raw CFTL:

- metadata: version, uid, UUIDs, **plaintext** `CatacombIdentityList`
- `CatacombSecureData` → CFTL/LTFC bytes (what we extracted)

Boot **A** unarchives the whole archive on the host; SEP templates are synced
via `restoreAndSyncTemplates`, not necessarily by re-pushing LTFC through
Mesa `0x40`.

## bent’s own 257 ladder (still open there too)

After readiness / sensor-info / cal-present / one builtin / cancel /
`NoCatacomb(0xffffffff)`, bent still sees **general `0x40` → 257**. They
explicitly say missing host catacomb-map bookkeeping + cold NoCatacomb do
**not** fully explain it. MBA91 is not uniquely broken; we are on the same
cliff with better macOS contrast.

## Ruled out on MBA91 (for warm/`cal_present` state)

| Hypothesis | Result |
| --- | --- |
| Need nonzero `0x54` | macOS also all-zero; still loads via **A** |
| Need host-parity reads | ready/prov5/cal/`0x52` green; `0x40` still 257 |
| Need FDR Mesa `0x20` | status **0**; `0x40` still 257 |
| Reset + `NoCatacomb` then `0x40` | still 257 (prior supervised run) |

## Open envelope / semantics questions

1. **Is Mesa `0x40` even used on enrolled macOS boot?**  
   No captured `performCommand … 64` (decimal) in our streams; Common
   `loadCatacomb*` dominates. Need a targeted Sequoia mine or accept that
   **A ≠ B**.

2. **Wrong blob class?**  
   SecureData LTFC vs CompleteSave(62) body vs full archived `.cat` bytes on
   the wire.

3. **Wrong `value` / component selector?**  
   We always send `value=0`. Unknown whether Master vs User is selected only
   by uid inside LTFC or also by `inValue`.

4. **State gate: “already loaded”?**  
   Warm `0x42` count≥1 may mean SEP rejects another `0x40` until a true empty
   catacomb (post-`NoCatacomb` *and* something bent still lacks).

5. **Host map bookkeeping** bent mentions — no Bridge opcode known; may be
   purely in-process on macOS after unarchive.

## Next probes (prefer read-only / docs first)

1. Diff CompleteSave **62** public size/header notes vs SecureData LTFC header
   (no raw dumps).  
2. Sequoia (when convenient): one boot Db mine specifically for decimal **64**
   around `loadCatacombForComponent` — confirm presence/absence of Mesa `0x40`.  
3. Only if (2) shows macOS **does** `0x40`: capture inSize/value and compare.  
4. If (2) shows **no** Mesa `0x40` on enrolled boot: treat Linux `0x40` as a
   **restore-into-empty-SEP** tool; next live work is “empty then load” with a
   clearer empty definition than `NoCatacomb` alone — or stop chasing `0x40`
   for warm match (warm path already has identities).

## Practical fork for Tim

- **Want match on Omarchy with current warm SEP?** You may not need `0x40` at
  all — `0x42` already lists uid 501; chase **match** (`0x04`) / ACM, not load.  
- **Want cold Linux-native restore from USB `.cat`?** Stay on envelope + empty
  SEP semantics; expect more 257 until blob class / empty gate is solved.
