# BiometricKit status technique — macOS 15.7.9 (24G830)

How the 2026-10-03 notes were recovered. Repeat this only on the same
build. A different `sw_vers` or a different cache UUID is a different
binary.

No identity UUIDs, keybag handles, biometric payloads, or disassembly
listings belong in the repo. Do not commit the extracted image.

## Gate

1. `sw_vers` must report ProductVersion **15.7.9** and BuildVersion
   **24G830**. Stop on any other pair.
2. The live cache is
   `/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_x86_64h`.
   The first 16 bytes are `dyld_v1 x86_64h`. The cache UUID is the
   16 bytes at file offset `0x58`:
   `FDD97301-9818-3865-A1D2-FEC1D3914796`.
3. Reject Recovery / BaseSystem cache UUID
   `E0F2B6DB-51BF-359C-90DC-331DE06552E8`. That cache has no
   `BiometricKit` image.

The on-disk framework path
`/System/Library/PrivateFrameworks/BiometricKit.framework/Versions/Current/BiometricKit`
is a broken symlink on this boot. The image is inside the shared
cache. Subcache `.01` holds it. The sibling `.map` file names the
image and the `__TEXT` VM address; the subcache file offset is that
VM address minus the subcache's map base.

On this cache the image UUID, from `LC_UUID`, is
`099725C6-A182-39C2-8104-DA810DE9EDD7`. Stop if the decoded UUID
differs.

## Tools

`/Library/Developer/CommandLineTools/usr/bin/llvm-objdump` and
`/usr/bin/python3`. Capstone, ipsw, and a Homebrew `rg` are not
required. `llvm-objdump` on this CLT has no `-b binary` mode.

```text
llvm-objdump -d --no-show-raw-insn \
  --start-address=START --stop-address=STOP /tmp/BiometricKit.macho
```

`/tmp/BiometricKit.macho` is a private rewrite, described next. Delete
it when the note is written. Do not commit it.

## Making objdump accept the image

Copy only the `__TEXT` segment out of the subcache. A raw slice and a
naive dylib extract both fail: non-`__TEXT` section offsets run past
the copy, linkedit command payloads run past EOF, and zeroing those
commands leaves weak-dylib name offsets dangling. `MH_DYLIB` also
requires `LC_ID_DYLIB`.

The rewrite that worked:

- Keep the Mach-O header and the first `LC_SEGMENT_64` only. Set
  `ncmds` to 1 and `sizeofcmds` to that command's `cmdsize`.
- Set the file type to `MH_EXECUTE` (2).
- Set that segment's `fileoff` to 0.
- Subtract the original segment `fileoff` from each section's file
  offset.
- The copy is exactly the original `__TEXT` file size.

Virtual addresses in the listing stay the cache VMs. Use them to
cross-check selectors. Do not publish them in the status notes.

## Classes and selectors

Chained cache pointers use the low 36 bits as an offset from cache
base `0x7ff800000000`. Keep a pointer only when the rebased VM falls
in a segment named by the `.map` file.

An Objective-C class on this ABI is `isa`, superclass, cache, then
`bits`. The class data is `bits` masked with
`0x00007ffffffffff8`. In that `class_ro_t`:

| Offset | Field |
| --- | --- |
| 24 | class name |
| 32 | base method list |
| 48 | ivar list |
| 64 | property list |

The ivar list is a count followed by 32-byte records: chained offset
pointer, name, type, alignment, size. The offset pointer's target is
a 32-bit ivar offset. On `BKOperation` that names `_xpcClient` at 8,
`_delegate` at 32, and `_state` at 48.

Method lists on this image have `entsizeAndFlags` `0xC000000F`. The
stride is `entsizeAndFlags & 0xFFFC`, which is 12. Masking with
`0xFFF` yields 15 and desynchronizes every record after the first.
Each record is three int32s: name, types, IMP.

- The high flags mean relative methods and direct selectors. The name
  is `sharedCacheRelativeMethodBase + int32`, not an offset from the
  name field.
- For this cache UUID that base is the uniqued selector U+1F92F
  (UTF-8 `F0 9F A4 AF`) at VM `0x7FF82144D450`. Another copy of those
  bytes earlier in the cache is the wrong base: names come out as
  slices of unrelated strings. Confirm the base by resolving
  `statusMessage:client:` before trusting any other name.
- The IMP is relative to its own field: `field_address + int32`.
  The same field-relative rule applies to the type string.

Selector slots in `__DATA_CONST` are chained pointers to those C
strings. Rebase, then read the NUL-terminated string.

`objc_msgSendSuper2` carries the class of the method that is making
the call. Dispatch starts at that class's superclass. Record the
class the slot rebases to, then continue the walk at the superclass.

## The status walk

Walk one ordinal through three methods, in this order:

1. `BKEnrollTouchIDOperation statusMessage:client:`
2. `BKEnrollOperation statusMessage:client:`, which on this image is
   a thunk into `statusMessage:details:client:` with a nil details
   argument
3. `BKOperation statusMessage:client:`

Stop at the first method that handles the ordinal. A later generic
arm is not the enroll path if a subclass already returned.

Three compares show up, all unsigned:

- Touch ID progress is `status - 100 <= 255` (100 through 355). The
  capture helper then handles `status - 78 <= 10` (78 through 88)
  and, separately, status 98. Every other status returns no capture
  error. The method still forwards `statusMessage:client:` after
  that helper unless it took the progress path.
- Enroll progress is the same 100 through 355 range. It then handles
  `status - 66 <= 4` (66 through 70) and status 501. `enrollContinue`
  is inside the progress path and the status-70 arm. Missing those
  ranges means the method forwards `statusMessage:client:`.
- The generic handler handles `status - 51 <= 29` (51 through 80)
  with one jump table, then status 99, then status 502. Anything
  else is the common return: log and return, no selector.

The jump tables in this image are

```text
leaq   table(%rip), %rcx
movslq (%rcx,%index,4), %reg
addq   %rcx, %reg
jmpq   *%reg
```

The destination is `table_base + signed_int32`. Adding the
displacement to the address of the slot is the wrong base and lands
in the middle of instructions.

Before the generic jump, the handler sets the argument register to 3
and the selector to `changeState:`. An arm that jumps to the call
without reloading the selector is `changeState:`. An arm that reloads
`operationEndsWithReason:` and then calls is that method. Read the
instruction at the destination before naming either one. `movl $N`
immediately before the jump replaces the default argument.

`operationEndsWithReason:` always calls `changeState:` with 4. The
reason argument is not the stored state. It may then send
`operation:finishedWithReason:` with the reason, on the object's
`dispatchQueue`, and it then sends `setDelegate:` nil and
`invalidateConnection` on `_xpcClient`.

`changeState:` stores its argument in `_state` when the value
differs, and may send `operation:stateChanged:` with that argument.
It does not end the operation by itself.

`__TEXT.__oslogstring` is not a clean list of NUL-terminated C
strings. Search the raw section bytes for `BKOperation::` rather than
splitting on NUL. The formats on this image are
`operationEndsWithReason: %ld` and `changeState %ld`. They do not
name the integers.

## What not to collapse

- The Touch ID capture mapper and the generic state switch are
  different tables. Status 80 is "no capture error" in the first and
  `operationEndsWithReason:` 2 in the second.
- Mesa opcode 80 and Catacomb command `0x50` are a different command
  space.
- `processEnrollFailReason:` on statuses 66, 67, and 68 is not
  `operationEndsWithReason:`. The enroll method runs first. On this
  image it then falls through into the generic handler, which is a
  second effect of the same ordinal, not a second ordinal.
- Do not copy one recovered ordinal onto its neighbor. Read the
  destination instruction for that arm on its own.
