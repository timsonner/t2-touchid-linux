# Status 80 selector — MBA91 macOS 15.7.9 (24G830)

Branch: `research/mba91-aks-ep7`. Normal macOS install, not Recovery.
`sw_vers` on this boot: ProductVersion **15.7.9**, BuildVersion
**24G830**.

Cache family `dyld_v1 x86_64h`, cache UUID
`FDD97301-9818-3865-A1D2-FEC1D3914796`.
BiometricKit image UUID `099725C6-A182-39C2-8104-DA810DE9EDD7`.

Walked ordinal **80** only, through `BKEnrollTouchIDOperation` →
`BKEnrollOperation` → `BKOperation`. No enroll, no keybag or Catacomb
export, and no edit to `src/t2_enrollment_protocol.py`.

The Touch ID capture-status mapper is a different switch. For status
80 it returns no capture error and skips
`fingerprintCaptureOperation:encounteredCaptureError:`. That does not
make ordinal 80 a silent `BKOperation` no-op.

## Facts

1. **Selector.** `BKEnrollTouchIDOperation` does not handle 80. It
   forwards `statusMessage:client:` to its superclass.
   `BKEnrollOperation statusMessage:client:` is a thunk into
   `statusMessage:details:client:` with nil details. Status 80 is
   outside the progress range 100–355, outside 66–70, and is not 501,
   so that method forwards `statusMessage:client:` to `BKOperation`.
   The generic handler calls **`operationEndsWithReason:`** with
   reason **2**. It does not call `changeState:` from the status
   switch itself.

2. **Host state.** `operationEndsWithReason:` always calls
   `changeState:` with **4**. The reason is not the state value.
   `changeState:` stores 4 in `BKOperation._state` when the previous
   value differs, and may then notify `operation:stateChanged:` with
   4. The same finish method then clears the XPC client:
   `setDelegate:` nil, then `invalidateConnection`, both on
   `BiometricKitXPCClient`. Enrollment must not mirror state 4 or
   reason 2 as a finger-capture state, and must not treat 80 as a
   phase wait. The host is finishing the generic operation. Do not
   map 80 onto `IGNORE_PHASE`.

3. **`enrollContinue`.** No. None of the three classes sends
   `enrollContinue` (wire `0x0e`) for status 80. The `enrollContinue`
   call in `BKEnrollOperation` is on the progress path, which 80 does
   not reach.

4. **Delegate.** Not enrollment feedback. The capture-error delegate
   is skipped. There is no presence, percent, or progress callback.
   If the operation delegate responds, `operationEndsWithReason:`
   sends `operation:finishedWithReason:` with reason 2 on the
   operation's `dispatchQueue`. `changeState:` may call
   `operation:stateChanged:` with 4. Those are operation-lifecycle
   callbacks. The enroll broker must ignore them as finger feedback.

## Bounds

Statuses 51, 58, 60, 61, 62, 65, 99, and 502 stay unmapped. In this
same switch, 60 and 61 call `changeState:` directly. Status 99 also
reaches `operationEndsWithReason:` with reason 2, and 502 uses reason
4. This note does not retune them.

The Linux client still freezes on unmapped status 80. The protocol
patch is a later Linux boot, after `user.kb` is loaded again by
`t2-keybag-load.service`.
