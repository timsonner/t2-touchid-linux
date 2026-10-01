# CORRECTION — no macOS user.kb turn (2026-09-30 ~22:51 MDT)

Operator correction (Tim). No enroll / create / `0x21` / second bag from
this file.

## What was wrong

`MATCH_CANARY_PLAN_2026-09-30.md` treated missing `/var/lib/t2-touchid/user.kb`
as a blocker and preferred restoring a **macOS** bag path for F1/K2.
That was a **wrong turn** relative to standing work on this fresh volume.

- There is **no** macOS keybag export on this track.
- Before the macOS reboot, Linux work was **enroll against the
  Linux-owned `-501` bag** (`native-501.kb` / creation-ref script),
  which refused start with **status 1** (`STATUS1_DIAG_2026-09-30.md`).
- macOS one-finger was only to **populate Catacomb + `0x42`** after
  empty inventory (`0x38`/`0x3A` = 22, count 0) — not to switch Linux
  session staging to `user.kb`.
- Durable bag file remains **`/var/lib/t2-touchid/native-501.kb`**
  (NEXT_STEPS 2026-09-26 create/export/reload). Installed
  `t2-keybag-load.sh` / systemd still hardcode `user.kb` for
  macOS-export flows — leave those alone. MBA91 warm-bringup is the
  override surface.

## Standing next (unchanged intent, corrected bag)

Post `…-222840` inventory (`NEXT_STEPS_STANDING_2026-09-30.md`,
`CATACOMB_IDENTITY_LAYOUT_20260930-222840.md`):

1. **Password-bound match research** (not enroll) once a keybag
   session exists — hard bans still: no enroll start, no create, no
   creation-ref `0x21` `0x100`/`0x200`, no second bag.
2. Status-1 leading hypothesis remains **credential class**:
   creation-ref enroll token ≠ password-bound policy-1007 path that
   opened E1/E4. Catacomb/`0x42` fill removed the empty-component
   gate; it does **not** authorize another native enroll start.

## native-501.kb + keybag.env (no pretend-user.kb)

Mechanically:

```text
t2-aks-tool load-keybag /var/lib/t2-touchid/native-501.kb 1
t2-aks-tool set-system-keybag 1 <HANDLE> -501
# write /run/t2-touchid/keybag.env with SESSION/HANDLE/SPECIAL=-501
```

Do **not** copy/rename to `user.kb` to satisfy systemd. Patch the
MBA91 loader path instead (done below).

Caveat from `NATIVE_C4_VERDICT` / `NATIVE_PASSWORD_HUNT`: password
unlock / `verify-password-acm` against a **fresh native** bag answered
SEP **-5**. Staging `keybag.env` ≠ proving F1 or unlock will succeed
on this bag. K2 token-free match still needs unlock status 0 on the
bags it used (then macOS `user.kb` era). Treat unlock/F1 outcomes as
open measurements after native load — not assumed green.

## Patch applied (warm-bringup MBA91 override)

`tools/mba91-aks-macos-capture/warm-bringup-mba91.sh` now:

- Defaults `KEYBAG=/var/lib/t2-touchid/native-501.kb`
- `--check` validates that path (refuses if missing; does not look for
  `user.kb`)
- `--bring-up` loads that bag, parses the real SEP handle, runs
  `set-system-keybag` with `SPECIAL=-501`, writes
  `/run/t2-touchid/keybag.env` from session/handle/special
- Explicitly does **not** copy/rename to `user.kb`
- Leaves `src/t2-keybag-load.sh` + `t2-keybag-load.service` on
  `user.kb` for macOS-export machines

Load and unlock were later approved and run (2026-10-01). Handle 1
returned SEP `-5`. This correction still forbids copying the bag to
`user.kb`. It does not forbid Track A research, and it is not a second
approval gate. Current orders are the standing block in `NEXT_STEPS.md`.
