# MBA91 Omarchy host-parity canaries (2026-09-07 night)

Public-safe. After Sequoia warm handoff → Omarchy. Script:
`~/Projects/t2sep-probe/mba91-host-parity-canaries.py` (local, not in git).

## Context

Sequoia private capture showed macOS does `0x52`→`0x54` (all-zero) then still
caches the builtin and `loadCatacomb`s. Plan: stop chasing nonzero `0x54`;
check whether Linux already has sensor/MSR-visible state.

## Results (read-only)

| Probe | Result |
| --- | --- |
| Bridge open | Multiverse → 0 → client-ver 2 → 1 OK |
| `0x53` sensor readiness | status 0, **ready=1** |
| `0x10` provisioning | status 0, **state=5** (matches macOS loadMSRk provisioningState 5) |
| `0x35` sensor info | status 0, len 12 |
| `0x28` biometrickitd info | status 0, **calibration_present=True** |
| `0x4c` xART | v1 status 0 **avail=True**; v2 `0xe00002c2` |
| `0x52` | records=1, builtin=1 |
| `0x42` | **count=1** uid=501 (warm identity present) |
| `0x54` | still all-zero (not re-probed here; known) |

## Implication

Linux **already matches** the *readable* host side of macOS init (ready /
prov 5 / cal-present / builtin list). The missing piece for prior `0x40`→257
is **not** “sensor looks dead” and **not** “must flip `0x54` first_byte.”

Still unknown / not implemented in bent:

- actual `loadMSRkData` / `loadCalibrationData` **write** opcodes (README:
  absent; calBLOBSource 3 on macOS)
- whether `0x40` 257 is a different envelope/component issue once host-cache
  is treated as “`0x52` is enough”

## Next

1. Supervised **no-reset** `0x40` with explicit preflight order  
   `0x53 → 0x10 → 0x35 → 0x28 → 0x52 → (optional 0x54 ignore) → 0x40`  
   using Private LTFC — success = status 0 + `0x42` still ≥1 (or restored).  
2. If still 257: escalate to MSR/cal **load** opcode hunt on Sequoia private
   stream / bent Catalina symbols — not more accessory type enums.
