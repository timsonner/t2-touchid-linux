# Status 80 handoff — MBA91 Linux enroll (2026-10-03)

Branch: `research/mba91-aks-ep7`. The macOS bag is unlocked and one
macOS finger already verifies. This note is the blocker between that
and a second finger enrolled from Linux.

No identity UUIDs, keybag handles, addresses, or biometric payloads.

## What already happened

`t2-touchid-enroll start` ran once, from a floating terminal, with the
three live acknowledgements. The operator typed the macOS keybag
password. The sensor was never asked for a finger.

| Step | Result |
| --- | --- |
| Password prompt | shown (`macOS login password:`) |
| Enroll start | status 0, protocol version 2, 68-byte request |
| Next event | BiometricKit operation status **80** |
| Client | `unmapped generic operation state status 80` |
| Finger progress | none |
| `recover-outcome` | `outcome_unknown_reconciled` true, identity count 1, `fingerprint_mutation_performed` false, `persistent_identity_delta` false |
| Gate | `unfinished_count` 0, `live_enrollment_blocked` false |
| Identity list after the stop | count 1, free 2, capacity 5, repeats equal, status 0 |

The journal milestone chain is `BASELINE_RECONCILED`,
`ENROLL_START_INTENT`, `ENROLL_START_OBSERVED`,
`ENROLL_OUTCOME_UNKNOWN`, `E3_RECOVERY_NO_CHANGE_RECONCILED`.

`user.kb` is still 1560 bytes. `native-501.kb` is still 1540 bytes.
Both keybags stayed unlocked. `/dev/t2-aks` stayed present.

## What status 80 is

It is a generic `BKOperation` status ordinal on service envelope
`0xe3ff8001`. The exact 24G830 chain
`BKEnrollTouchIDOperation` → `BKEnrollOperation` → `BKOperation` puts
these nine ordinals in the state-changing set, and this client still
refuses them:

`51`, `58`, `60`, `61`, `62`, `65`, **`80`**, `99`, `502`.

They are not silent phase no-ops. The no-op domain is already encoded
in `EXACT_NOOP_PHASE_RANGES` inside `src/t2_enrollment_protocol.py`.
Status 80 is in `EXACT_UNMAPPED_GENERIC_STATE_STATUSES`, and
`_freeze` raises before any finger feedback or `enrollContinue`.

This ordinal is not Mesa opcode 80 and not Catacomb command `0x50`.
Those numbers appear in `CATACOMB_BRIDGE_SEQUENCE.md` and
`MESA_BENT_OPCODE_CROSSWALK.md` for a different command space. Do not
use that save cluster as the meaning of this status.

The authoritative write-up is `enrollment_research/README.md` and the
conformance matrix in `enrollment_research/FINDINGS.md`. This tree does
not contain the 24G830 `BiometricKit` binary, so the selector for
ordinal 80 was not recovered here. The protocol was not changed.

## What to recover before the next enroll

From the 24G830 `BKOperation` jump table, for ordinal 80 only:

1. The Objective-C selector the generic handler calls.
2. The host state it changes, and whether enrollment must mirror that
   state or only wait.
3. Whether the handler sends `enrollContinue` (`0x0e`). The Pro notes
   say a state-changing ordinal does not get an invented continue.
4. Whether a delegate callback is enrollment feedback (presence, retry,
   progress) or something the enroll broker must ignore.

A no-identity-delta on this one run is not that recovery. The start
returned 0 and the client froze before the finger loop, so the SEP had
little chance to save a template. That does not say what 80 means on
the next event.

## Patch shape, after the selector is known

Touch only ordinal 80.

- Remove `80` from `EXACT_UNMAPPED_GENERIC_STATE_STATUSES`.
- Add the recovered transition in `accept`. Do not send `enrollContinue`
  unless the handler does.
- In `tests/test_enrollment_protocol.py`,
  `test_unmapped_generic_operation_states_remain_fail_closed` must keep
  `51`, `58`, `60`, `61`, `62`, `65`, `99`, and `502` fail-closed.
  Status 80 gets its own assertion for both envelope versions 1 and 2.
- Do not retune the other eight ordinals in the same change.

## Live enroll after that patch

The gate is already clear. Preflight passed earlier on this boot. The
Catacomb backup is installed. Password fallback was exercised with
`sudo -k`.

```bash
sudo t2-touchid-enroll start \
  --acknowledge-password-fallback-tested \
  --acknowledge-live-fingerprint-enrollment \
  --acknowledge-local-catacomb-mutation
```

Run it from the desktop user through sudo, on a terminal the operator
can see. It asks for the macOS login password, then the new finger.
One start. If it stops on another unmapped ordinal, reconcile with
`t2-touchid-enroll recover-outcome` and stop. Do not start again until
that ordinal is recovered the same way.

## Do-nots

- No second `t2-touchid-enroll start` while status 80 is still unmapped.
- No mapping of 80 onto `IGNORE_PHASE` or an invented `enrollContinue`.
- No `bridge-xpc-enroll-native-501.py`, and no creation-reference
  `0x21` option `0x100` or `0x200`.
- No second bag, and no copy of `native-501.kb` onto `user.kb`.
- No `warm-bringup-mba91.sh` while `user.kb` is the loaded bag.
- No `0x40`, sensor reset, `no_catacomb`, or `0x48`.
- No commit of journals, inventory logs, or the Catacomb archive.
