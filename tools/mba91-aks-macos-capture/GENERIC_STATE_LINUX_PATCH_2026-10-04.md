# Generic-state Linux patch — MBA91 (2026-10-04)

The eight remaining 24G830 generic ordinals from
`GENERIC_STATE_SELECTORS_2026-10-03.md` are taught in
`src/t2_enrollment_protocol.py`. The live copy under
`/opt/t2-touchid/src` matches. Tests:
`tests.test_enrollment_protocol`,
`tests.test_fprint_enrollment_runtime`,
`tests.test_enrollment_operation`,
`tests.test_enrollment_coordinator`,
`tests.test_enrollment_finalizer`.

No identity UUIDs, keybag handles, addresses, or biometric payloads.
No enroll was started with this patch.

## Mapping

| Statuses | Action | Machine | Continue | Journal |
| --- | --- | --- | --- | --- |
| 60, 61 | `operation-state-changed` | stays `ACTIVE` | false | `ENROLL_OPERATION_STATE_OBSERVED` with `event.ordinal` |
| 51, 58, 62, 65, 80, 99, 502 | `operation-finished` | `OPERATION_FINISHED` | false | `ENROLL_TERMINAL_FAILURE_OBSERVED` with `event.ordinal` |

60 stores `changeState:` 3. 61 stores 2 without the presence
callback that status 64 uses. They are not `IGNORE_PHASE`, not
finger-removed, and not the finish used for 80.

51 and 62 use `operationEndsWithReason:` 3. 58 and 65 use 1. 80 and
99 use 2. 502 uses 4. Stored `_state` is 4 for every finish row. 66,
67, and 68 stay `processEnrollFailReason:`.

`EXACT_UNMAPPED_GENERIC_STATE_STATUSES` is empty. Accessory 501 stays
blocked.

## Next live enroll

The prior start froze after progress 355. That ordinal was not
journaled. This patch does not name it from that log. One later
`t2-touchid-enroll start` can show whether 60, 61, or a finish
follows 355, and whether the host Catacomb persists without
`recover-observed`. The two live fingers stay the specimen until that
start.

## Do-nots

- Do not map 60 or 61 onto `operation-finished`.
- Do not map 61 onto status 64.
- No `bridge-xpc-enroll-native-501.py`.
- No second bag, and no `warm-bringup-mba91.sh` while `user.kb` is
  loaded.
- No `0x40`, sensor reset, `no_catacomb`, or `0x48`.
