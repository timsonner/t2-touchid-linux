# Status 80 Linux handoff — MBA91 (2026-10-03)

Branch: `research/mba91-aks-ep7`. The macOS notes are on this branch.
You are on Omarchy, not on the macOS boot. You patch the client, then
you run one enroll.

Later the same night: patch `ddfcdf6` was installed under
`/opt/t2-touchid/src`. One enroll ran. Status 80 did not freeze.
Progress reached ordinal 355. The SEP then had two identities.
`recover-observed` persisted the new one. Live order is
`LINUX_ENROLL_IDENTITY_2026-10-03.md` and the standing block of
`NEXT_STEPS.md`.

Read these first, and do not rediscover them:

- `STATUS80_SELECTOR_2026-10-03.md` — ordinal 80.
- `GENERIC_STATE_SELECTORS_2026-10-03.md` — the other eight. They
  stay fail-closed in this patch.
- `BIOMETRICKIT_STATUS_TECHNIQUE_2026-10-03.md` — how the notes were
  produced. Not a live-enroll step.
- `STATUS80_HANDOFF_2026-10-03.md` — the enroll that froze, the gate,
  and the do-nots. This file replaces its patch-shape section.

No identity UUIDs, keybag handles, addresses, or biometric payloads.

## Host fact to encode

On macOS 15.7.9 build 24G830, image UUID
`099725C6-A182-39C2-8104-DA810DE9EDD7`, status **80** is a generic
operation finish.

`BKEnrollTouchIDOperation` and `BKEnrollOperation` forward it.
`BKOperation` calls `operationEndsWithReason:` with reason **2**.
That method stores `BKOperation._state` **4**, may notify
`operation:finishedWithReason:` with reason 2, then clears the XPC
client with `setDelegate:` nil and `invalidateConnection`.

It does not send `enrollContinue` (wire `0x0e`). It is not presence,
progress, or retry. It is not `processEnrollFailReason:`. Status 67
is the enroll failure with reason 2. Status 80's reason 2 is a
different selector. Do not map 80 onto `FAILED`, `CANCELLED`, or
`TIMED_OUT`. Do not map it onto `IGNORE_PHASE`.

The broker leaves the finger loop and reconciles. It does not ask
for a finger and it does not send continue.

## Patch, ordinal 80 only

Load `user.kb` again with `t2-keybag-load.service` before the enroll
below. Alias `-501` does not survive reboot. Do not run
`warm-bringup-mba91.sh`.

1. In `src/t2_enrollment_protocol.py`, remove `80` from
   `EXACT_UNMAPPED_GENERIC_STATE_STATUSES`. Add one new terminal
   action and one new terminal state. A name that matches this tree
   is `operation-finished`. `accept` returns that action for status
   80 on both envelope versions. `continue_required` stays false.
   The machine leaves `ACTIVE`.
2. In `src/t2_enrollment_operation.py`, consume that action the way
   `FAILED` is consumed: do not call the finger-loop callback, do
   not send continue, append `ENROLL_TERMINAL_FAILURE_OBSERVED` with
   `"status": 80`, and return an operation result whose outcome is
   the new action value and whose reconciliation flag is true.
   The existing map writes 66, 67, or 68 into that journal field.
   Status 80 must not reuse those numbers.
3. `src/t2_enrollment_finalizer.py` already treats every outcome
   other than `identity-observed` and `result-witnessed` as the
   failure bio-lockout reconciliation. Do not add a second
   persistence path. Do confirm the new outcome takes that path.
4. `src/t2_fprint_enrollment_runtime.py` `finish` treats only
   `cancelled`, `failed`, and `timed-out` as a reconciled failure.
   Any other outcome becomes `enroll-unknown-error`. Add the new
   outcome to that reconciled-failure set. `accept` must still
   raise if this action reaches the finger loop. The operation
   layer consumes it first.
5. Do not edit the arms for `51`, `58`, `60`, `61`, `62`, `65`,
   `99`, or `502`. Six of those finish with a different reason.
   Status 60 is `changeState:` 3 and status 61 is `changeState:` 2.
   Neither is this finish.

## Tests

- `tests/test_enrollment_protocol.py`
  - `test_unmapped_generic_operation_states_remain_fail_closed`:
    the expected set loses 80 and keeps the other eight.
  - `test_every_exact_build_status_through_503_has_a_decision`:
    remove 80 from `blocked`. Assert the new action for versions
    1 and 2. Leave 501 blocked.
  - `test_terminal_failures_remain_distinct_and_67_is_generic`:
    66, 67, and 68 stay on their current actions. Add 80 as its
    own case.
- `tests/test_fprint_enrollment_runtime.py`: the reconciled-failure
  outcomes gain the new outcome and keep `cancelled`, `failed`,
  and `timed-out`.

Run the enrollment protocol tests and the fprint enrollment runtime
tests. Do not start an enroll against a failing suite.

## One enroll after the tests pass

The gate was clear on the 2026-10-03 boot. Preflight had passed.
The Catacomb backup was installed. Password fallback was exercised
with `sudo -k`. The backup check is unchanged: exactly one private
SHA-256-named archive under `/var/lib/t2-touchid/backups/`.

```bash
sudo t2-touchid-enroll start \
  --acknowledge-password-fallback-tested \
  --acknowledge-live-fingerprint-enrollment \
  --acknowledge-local-catacomb-mutation
```

Run it from the desktop user through sudo, on a terminal the
operator can see. It asks for the macOS login password, then the
new finger. One start. If it stops on another unmapped ordinal,
reconcile with `t2-touchid-enroll recover-outcome` and stop. Do
not fold that ordinal into this patch from the live log.

## Do-nots

- No second `t2-touchid-enroll start` while status 80 is still
  unmapped.
- No `enrollContinue` for status 80.
- No mapping of 80 onto `IGNORE_PHASE`.
- No mapping of 60 or 61 onto this finish.
- No `bridge-xpc-enroll-native-501.py`, and no creation-reference
  `0x21` option `0x100` or `0x200`.
- No second bag, and no copy of `native-501.kb` onto `user.kb`.
- No `warm-bringup-mba91.sh` while `user.kb` is the loaded bag.
- No `0x40`, sensor reset, `no_catacomb`, or `0x48`.
- No commit of journals, inventory logs, or the Catacomb archive.
