# C1 verdict: native keybag creation works on MBA91 (2026-09-20)

Branch: `research/mba91-aks-ep7`. C1 gate disabled (verified).
Shapes/statuses/counts/lengths only — no UUIDs, no KEK, no
passwords, no keybag bytes. The KEK (162 B measured) was wiped in
memory and never copied out; only its length is recorded anywhere.

## Verdict

**Endpoint-7 op `0x01` v5 creates a live keybag identity on this
Air, first try.** SEP status 0, live handle 8, bag UUID read back
and verified present through the allowlisted copy path. The t2touch
v5 construction ports to MBA91 byte-for-byte — no version fallback
needed, no board quirk observed. Native-only stops being theory
here.

## Run (single shot, operator-run, no finger contact)

- Warm SEP, lab + ACM nodes live, keybag session for the ACM
  ceremony. Fresh tracking context, operator password bound,
  policy-1007 SATISFIED, mandatory cleanup.
- Intent journaled pre-dispatch (request-sha256 + version, private
  path). Fresh random account UUID, Linux-side ceremony throughout
  — nothing macOS-derived except the operator's typing password
  for the ACM bind (any password works; the bag is new).
- Dispatch: `sep_status` 0, `live_handle` 8, `kek_length` 162.
  Outcome `created-unbound`. Bag UUID observed true.
- Post: SEP identities still exactly 3, repeat-equal true. The
  live handle evaporates on reboot (no export staged, by design) —
  zero durable footprint. Nothing bound, nothing deleted.

## What this unlocks (and what it doesn't yet)

- The create wall is down: v5-first-try on MBA91. C2 (v4) is moot
  unless a later board disagrees.
- Next is C3+: export → atomic persist → bag-UUID verify after
  reload → alias bind → enroll-native against the new bag. Each
  separately staged; the bind step is where FINDINGS'
  non-atomic warnings start applying, so it stays paper until C3
  design closes.
- The sudo PAM prompt fired and timed out without a touch, and
  password fallback authorized — production stack behaving, again.
