# Generic state selectors — eight fail-closed ordinals (24G830)

Same boot as `STATUS80_SELECTOR_2026-10-03.md`. Normal macOS 15.7.9
build 24G830. Cache family `dyld_v1 x86_64h`, cache UUID
`FDD97301-9818-3865-A1D2-FEC1D3914796`. BiometricKit image UUID
`099725C6-A182-39C2-8104-DA810DE9EDD7`.

These are the other members of `EXACT_UNMAPPED_GENERIC_STATE_STATUSES`:
**51, 58, 60, 61, 62, 65, 99, 502**. Ordinal 80 is already recorded.
No enroll, no keybag or Catacomb export, and no edit to
`src/t2_enrollment_protocol.py`. The Linux client still freezes on
all nine.

## Shared path

None of the eight is handled by `BKEnrollTouchIDOperation` or
`BKEnrollOperation`.

Touch ID's progress range is 100–355. Its capture helper handles
78–88 and 98 only. Each of these eight misses both, so the capture
helper returns no capture error, `fingerprintCaptureOperation:encounteredCaptureError:`
is skipped, and the method forwards `statusMessage:client:`.

`BKEnrollOperation` handles progress 100–355, statuses 66–70, and
501. Each of these eight misses those and forwards
`statusMessage:client:` with the original status. The `enrollContinue`
call in that class is on the progress path. None of the eight reaches
it.

`BKOperation statusMessage:client:` is the handler. No class sends
`enrollContinue` (wire `0x0e`) for any of them. The image names no
enum for the reason or state integers below. The log lines are
`operationEndsWithReason: %ld` and `changeState %ld`.

## Finish, same method as 80

`operationEndsWithReason:` ignores its argument when it stores state.
It always calls `changeState:` with **4**, so `BKOperation._state`
becomes 4 when it differed. It may then notify
`operation:stateChanged:` with 4. If the delegate responds, it sends
`operation:finishedWithReason:` with the reason below, on the
operation's `dispatchQueue`. It then sends `setDelegate:` nil and
`invalidateConnection` on `BiometricKitXPCClient`.

That is an operation finish. It is not presence, progress, or retry.
Enrollment must not mirror it as finger feedback, must not send
`enrollContinue`, and must not treat it as a phase wait. Do not map
these onto `IGNORE_PHASE`.

| Status | `operationEndsWithReason:` |
| --- | --- |
| 51 | 3 |
| 58 | 1 |
| 62 | 3 |
| 65 | 1 |
| 99 | 2 |
| 502 | 4 |

51 and 62 are the same host effect. 58 and 65 are the same host
effect. 99 uses reason 2, the same reason as ordinal 80. The stored
state is 4 for every row, because the reason is not the state value.
Keep the ordinals distinct in a later patch. Do not retune them by
copying one row onto another.

## State only

These two call `changeState:` from the status switch. They do not
call `operationEndsWithReason:`. They do not notify
`operation:finishedWithReason:`, do not clear the XPC client, and do
not send `enrollContinue`.

| Status | `changeState:` |
| --- | --- |
| 60 | 3 |
| 61 | 2 |

`changeState:` stores that integer in `BKOperation._state` when it
differs, and may notify `operation:stateChanged:` with it. That
callback is not finger feedback. The operation is still running.
Status 64, already mapped, also stores state 2, and it does so only
after `operation:presenceStateChanged:` false. Status 61 stores state
2 without the presence callback.

Do not give 60 or 61 the finish transition used for 80. Do not
describe the handler as a silent no-op: it does change
`BKOperation._state`. The broker has no wire command to send.

## Still fail-closed

The live enroll froze on 80, not on these eight. A Linux patch for
80 stays the next protocol change. These eight stay in
`EXACT_UNMAPPED_GENERIC_STATE_STATUSES` until their own change, and
that change must not fold 60 or 61 into the finish path.
