# T-series note: lone blob needs the 0x4000 selector flag (2026-09-20)

Branch: `research/mba91-aks-ep7`. T gate open (uncommitted).
Shapes/statuses/counts only.

## Finding

Token-free opcode-4 with a 1-record counted blob but flags 0
returned terminal `false` for ALL THREE records against a ring
finger that verifies (any-of-3) the same night. The lone blob is
not honored as a selection without `MATCH_FLAG_SELECTED_IDENTITIES`
(`0x4000`) — the reference construction always pairs them, and the
SEP evidently evaluates against nothing and rejects. Framing fixed
in `bridge-xpc-match-targeted.py`; prior three falses discarded as
invalid-framing data, not identity evidence.

## Valid series (0x4000 framing, ring held)

- T0 (record 0): terminal `false`, touch registered (73 present),
  prelude all 0, cancel 0, records preserved. Record 0 is not ring.
- T1/T2 pending: record 1, then record 2 (insertion order predicts
  ring last, unproven until a `true`).

## Rules carried forward

- Stop at the first `true`; two trues or any identity change halts.
- Exactly-one-true expected; zero-true after all three with valid
  framing reopens the question (selection semantics deeper than
  one flag).
