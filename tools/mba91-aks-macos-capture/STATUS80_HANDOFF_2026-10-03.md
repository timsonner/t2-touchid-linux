# Status 80 handoff — MBA91 Linux enroll (2026-10-03)

Branch: `research/mba91-aks-ep7`. One macOS finger already verifies.
Linux enroll accepted the keybag password, returned status 0, and
froze on BiometricKit status **80** before any finger prompt.

No identity UUIDs, keybag handles, addresses, or biometric payloads.

Two agents, in order. The macOS agent does the first section and
stops. The Linux agent does not enroll until that note is back and
the patch below exists.

## macOS agent — do this, then stop

You are on the MacBookAir9,1 **normal macOS install**. Not Recovery.
Not Omarchy. Not the BaseSystem cache.

The Linux checkout sits on the encrypted Omarchy volume. Read this
file from the branch. Your product is a short note with the four
facts below. You do not enroll a finger, and you do not patch Linux.

1. Run `sw_vers`. Continue only when `ProductVersion` is **15.7.9**
   and `BuildVersion` is **24G830**. Any other build is a different
   binary. Stop and report the versions you actually saw.
2. Disassemble the live `BiometricKit` image:
   `/System/Library/PrivateFrameworks/BiometricKit.framework/Versions/Current/BiometricKit`.
   The matching cache family is `dyld_v1 x86_64h`, cache UUID
   `FDD97301-9818-3865-A1D2-FEC1D3914796`. Record the image UUID you
   actually decoded.
3. Walk only ordinal **80** through
   `BKEnrollTouchIDOperation` → `BKEnrollOperation` → `BKOperation`.
   The first two classes may pass it upward. The generic superclass
   is the one that changes operation state.
4. Write down these four facts, and nothing inferred past them:
   - the Objective-C selector the generic handler calls
   - the host state it changes, and whether enrollment must mirror
     that state or only wait
   - whether the handler sends `enrollContinue` (wire command `0x0e`)
   - whether any delegate callback is enrollment feedback (presence,
     retry, progress) or something the enroll broker must ignore

The Touch ID capture-status mapper sends statuses 79 through 84 to
"no capture error". That is a different switch. It does not mean
ordinal 80 is a silent `BKOperation` no-op. The generic superclass
still changes operation state for 80. Do not collapse those two
results.

Reject these substitutes:

- Recovery / BaseSystem cache UUID
  `E0F2B6DB-51BF-359C-90DC-331DE06552E8`. It has no `BiometricKit`
  image. An earlier copy of that cache lived at
  `~/.local/share/t2-touchid/macos-system/` and is macOS 26.1.
- A public symbol-server image with a different UUID.
- Mesa opcode 80 and Catacomb command `0x50`. Those numbers are a
  different command space (`CATACOMB_BRIDGE_SEQUENCE.md`,
  `MESA_BENT_OPCODE_CROSSWALK.md`).

Stop when the four facts and the image UUID are written down. Do not
enroll, delete, rename, or replace a finger. Do not export a new
keybag or Catacomb. The one existing finger is the specimen. Do not
edit `src/t2_enrollment_protocol.py` from macOS.

## Linux agent — after that note returns

Boot back to Omarchy and stop at the note. Alias `-501` does not
survive reboot. `t2-keybag-load.service` loads
`/var/lib/t2-touchid/user.kb` again. Do not run
`warm-bringup-mba91.sh`; it loads `native-501.kb`.

Then apply the patch shape below, for ordinal 80 only. One
`t2-touchid-enroll start` comes after that patch, on a terminal the
operator can see. Another unmapped ordinal means
`t2-touchid-enroll recover-outcome` and a stop.

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
Both keybags stayed unlocked on that boot. `/dev/t2-aks` stayed present.
A no-identity-delta on this run is not the recovery above. The client
froze before the finger loop.

## What status 80 is

It is a generic `BKOperation` status ordinal on service envelope
`0xe3ff8001`. The exact 24G830 chain puts these nine ordinals in the
state-changing set, and this client still refuses them:

`51`, `58`, `60`, `61`, `62`, `65`, **`80`**, `99`, `502`.

They are not silent phase no-ops. The no-op domain is already encoded
in `EXACT_NOOP_PHASE_RANGES` inside `src/t2_enrollment_protocol.py`.
Status 80 is in `EXACT_UNMAPPED_GENERIC_STATE_STATUSES`, and
`_freeze` raises before any finger feedback or `enrollContinue`.
`enrollment_research/README.md` and the conformance matrix in
`enrollment_research/FINDINGS.md` are the write-up. This tree does
not contain the `BiometricKit` binary. The protocol was not changed.

## Patch shape, after the selector is known

Touch only ordinal 80. Do this on Linux, after the macOS note exists.

- Remove `80` from `EXACT_UNMAPPED_GENERIC_STATE_STATUSES`.
- Add the recovered transition in `accept`. Do not send `enrollContinue`
  unless the handler does.
- In `tests/test_enrollment_protocol.py`,
  `test_unmapped_generic_operation_states_remain_fail_closed` must keep
  `51`, `58`, `60`, `61`, `62`, `65`, `99`, and `502` fail-closed.
  Status 80 gets its own assertion for both envelope versions 1 and 2.
- Do not retune the other eight ordinals in the same change.

## Live enroll after that patch

Linux only. The macOS agent does not run this command.

The gate was clear on the 2026-10-03 boot. Preflight had passed. The
Catacomb backup was installed. Password fallback was exercised with
`sudo -k`. After the return boot, load `user.kb` again before this
command. The backup check is unchanged: exactly one private
SHA-256-named archive under `/var/lib/t2-touchid/backups/`.

```bash
sudo t2-touchid-enroll start \
  --acknowledge-password-fallback-tested \
  --acknowledge-live-fingerprint-enrollment \
  --acknowledge-local-catacomb-mutation
```

Run it from the desktop user through sudo, on a terminal the operator
can see. It asks for the macOS login password, then the new finger.
One start. If it stops on another unmapped ordinal, reconcile with
`t2-touchid-enroll recover-outcome` and stop.

## Do-nots

- No enroll, delete, or keybag/Catacomb export on the macOS boot.
- No second `t2-touchid-enroll start` while status 80 is still unmapped.
- No mapping of 80 onto `IGNORE_PHASE` or an invented `enrollContinue`.
- No `bridge-xpc-enroll-native-501.py`, and no creation-reference
  `0x21` option `0x100` or `0x200`.
- No second bag, and no copy of `native-501.kb` onto `user.kb`.
- No `warm-bringup-mba91.sh` while `user.kb` is the loaded bag.
- No `0x40`, sensor reset, `no_catacomb`, or `0x48`.
- No commit of journals, inventory logs, or the Catacomb archive.
