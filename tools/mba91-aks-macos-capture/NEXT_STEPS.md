# MBA91 Touch ID / BridgeXPC — next steps

Branch: `research/mba91-aks-ep7`. Host: MacBookAir9,1 · Omarchy `MBA19-OMARCHY` ·
bridgeOS **23P6068** · BridgeXPC **39**.  
Fingerprint path = **BridgeXPC** (`BRIDGEXPC_PATH.md`). This work is
conducted under **Track A** — independent ownership research
([`docs/LAB_PROTOCOL.md`](../../docs/LAB_PROTOCOL.md)); the earlier 2026-09-08
park is lifted. See `PARKED_2026-09-08.md` for the authorization record.

## Standing state (2026-10-03, enroll stopped on status 80)

Track A is the approval for this machine (`docs/LAB_PROTOCOL.md`,
`PARKED_2026-09-08.md`). The halts in this block are results of that
research. They do not withdraw the approval, and they are not a request
for another permission check.

The macOS bag is unlocked, fingerprint `sudo` works, and one macOS
finger verifies. A Linux enroll through `t2-touchid-enroll start`
accepted the macOS password and the enroll start returned status 0.
The client then froze on BiometricKit status **80** before any finger
prompt. `recover-outcome` closed that journal: identity count stayed
**1**, `fingerprint_mutation_performed` false,
`persistent_identity_delta` false, and `live_enrollment_blocked` is
false. The full handoff is `STATUS80_HANDOFF_2026-10-03.md`.

Status 80 is a `BKOperation` finish, recovered in
`STATUS80_SELECTOR_2026-10-03.md`. It is not Mesa opcode 80 and not
Catacomb command `0x50`. The Linux client still freezes on it, so
another start will stop in the same place until the protocol patch.

| Fact | Evidence |
| --- | --- |
| Enroll start | status 0, protocol v2, 68-byte request. Password prompt appeared. No finger-progress line was printed |
| Stop | `unmapped generic operation state status 80` |
| `recover-outcome` | `outcome_unknown_reconciled` true, identity count 1, no fingerprint mutation, no persistent delta |
| Gate after recovery | `unfinished_count` 0, `live_enrollment_blocked` false |
| Read-only identity list after the stop, before recovery | count 1, free 2 / capacity 5, both repeats equal, status 0 |
| `user.kb` / `native-501.kb` | 1560 and 1540 bytes, unchanged by the enroll |
| Backup | `/var/lib/t2-touchid/backups/<catacomb-sha256>.tar.gz` is installed, mode 0600. The hash is in `EXPORT_RETURN_FINDINGS_2026-10-03.md` |

## Measured halts

These shots have answered. Another copy of the same shot is not a new
question.

- Do not run `t2-touchid-enroll start` again until status 80 has a
  recovered `BKOperation` transition in `t2_enrollment_protocol.py`.
  The 2026-10-03 start already proved the password and the start.
- Do not map status 80 to a silent no-op or to `IGNORE_PHASE`.
  The 24G830 handler calls `operationEndsWithReason:` with reason 2,
  which stores state 4 and does not send `enrollContinue`
  (`STATUS80_SELECTOR_2026-10-03.md`).
- Do not run `bridge-xpc-enroll-native-501.py`. Its creation-reference
  `0x21` option `0x100` was accepted, and the zero-group start returned
  status **1** (`STATUS1_DIAG_2026-09-30.md`).
- Password unlock of `native-501.kb` returned SEP **-5** on 2026-09-20
  and again on 2026-10-01. That file stays unloaded. The macOS
  `user.kb` unlock is a different shot and returned 0.
- No second bag, and no copy of `native-501.kb` to `user.kb`.
- Do not run `warm-bringup-mba91.sh` on this boot. It loads
  `native-501.kb`. The live loader is `t2-keybag-load.service`.
- `0x40`, sensor reset, `no_catacomb`, and `0x48` cleared identities on
  this Air in earlier approved runs. Leave them unused while this
  finger is the specimen.
- Opcode 74 is a closed matrix (`SESSION74_VERDICT_2026-09-17.md`).
- This Air's `fprintd` is verify-only. It cannot enroll.

## Next

The macOS selector note is `STATUS80_SELECTOR_2026-10-03.md`.
Enrollment stays on Linux, after the patch. Do not enroll on this
macOS boot.

1. Done on macOS 15.7.9 build 24G830. Image UUID
   `099725C6-A182-39C2-8104-DA810DE9EDD7`. Ordinal 80 calls
   `operationEndsWithReason:` with reason 2. That stores
   `BKOperation` state 4, may notify `operation:finishedWithReason:`
   with reason 2, and does not send `enrollContinue`.
2. Back on Omarchy, load `user.kb` again with `t2-keybag-load.service`.
   Do not run `warm-bringup-mba91.sh`. Teach only that transition in
   `t2_enrollment_protocol.py`, with a test that keeps the other eight
   unmapped ordinals fail-closed. Do not send `enrollContinue`. Do not
   map 80 onto `IGNORE_PHASE`.
3. Only after that patch: `t2-touchid-enroll start` again. The macOS
   password, then the new finger.

## Dated records below

## Prior standing state (2026-10-03, macOS export return)

Track A is the approval for this machine (`docs/LAB_PROTOCOL.md`,
`PARKED_2026-09-08.md`). The halts in this block are results of that
research. They do not withdraw the approval, and they are not a request
for another permission check.

The 2026-10-01 macOS export is installed and the macOS bag unlocked.
`fprintd-verify -f any tim` returned `verify-match`, and fingerprint
`sudo` succeeded on this boot. The full record is
`EXPORT_RETURN_FINDINGS_2026-10-03.md`.

`/var/lib/t2-touchid/user.kb` is the macOS export (1560 bytes, mode
0600). `native-501.kb` is still the Linux-owned 1540-byte file and was
not copied onto `user.kb`. `t2-keybag-load.service` loaded `user.kb`
and bound special `-501`. Both unlock calls returned status 0. The
local Catacomb store is provisioned with one identity.
`/var/lib/t2-touchid/backups/` did not exist when this block was
written, so `t2-touchid-enroll` could not start.

| Fact | Evidence |
| --- | --- |
| Boot-policy response **3** for bridgeOS `23.16.16068.0.0,0`, epoch 1.0 | `INVENTORY_RO_501_20261003-194352` dmesg |
| Identity count **1**, free **2** / capacity **5** | same public report |
| Catacomb component present; state words **`[0xFFFFFFFF, 3, 501, 3]`** | same |
| SKS lock **520** on this boot (the 2026-10-01 cold boot was 16) | same (`sks_lock_state: 520`) |
| BridgeXPC port this boot | **49197** |
| `user.kb` load and `set-system-keybag` onto `-501` | both status 0 (`t2-keybag-load.service`) |
| Both keybag unlocks | status 0, `response_length` 16. `/run/t2-touchid/keybags-unlocked` is mode 0600 |
| `fprintd-verify -f any tim` | `verify-match`. Daemon log: `mba91-fprintd: verify verify-match` |
| PAM | `tools/install-pam.sh`. Originals in `/var/lib/t2-touchid/pam-backups`. Fingerprint `sudo` succeeded |
| Export stick, remounted 2026-10-03 | Catacomb archive still 23665 bytes, SHA-256 `3a9c6dce463e20cb4c2bc4c685cc7a24b5ea19d2f808b6443f7f4e98c31705db`. Keybag archive still 12561 bytes |

The next steps written with this block were: install that Catacomb
archive as the sole private backup, confirm a typed password at
`sudo`, run preflight, then `t2-touchid-enroll start`. Those four
steps finished later on 2026-10-03. The start returned status 0 and
froze on BiometricKit status 80 before a finger prompt. See the
standing state above and `STATUS80_HANDOFF_2026-10-03.md`.

## Prior standing state (2026-10-01, after the approved match canary)

Track A is the approval for this machine (`docs/LAB_PROTOCOL.md`,
`PARKED_2026-09-08.md`). The halts in this block are results of that
research. They do not withdraw the approval, and they are not a request
for another permission check.

The macOS one-finger enroll for uid 501 is done. It survived the warm
reboot and the 2026-10-01 cold boot into Omarchy. The durable bag on
this volume is the Linux-owned `/var/lib/t2-touchid/native-501.kb` from
2026-09-26. There is no macOS `user.kb`. `warm-bringup-mba91.sh` loads
`native-501.kb` and leaves the systemd `user.kb` loader alone
(`CORRECTION_NO_MACOS_USER_KB_2026-09-30.md`).

| Fact | Evidence |
| --- | --- |
| Per-user `0x42` count **1** (status 0, 20 B) | `…-222840`; reconfirmed `INVENTORY_RO_501_20261001-063245` |
| Catacomb UUID/hash status **0**; user component present | `…-222840`; `CATACOMB_IDENTITY_LAYOUT_20260930-222840.md` |
| Catacomb state words **`[0xFFFFFFFF, 3, 501, 3]`** | same |
| SKS lock **16 = 0x10** (warm), including after true power-off | `…-222840` and `…-063245` (`sks_lock_state: 16`) |
| Free `0x41` **2** / capacity **5** | same |
| BridgeXPC port this cold boot | **49213** (`…-063245`) |
| Private dump persisted | `/var/lib/t2-touchid/inventory-journals/inventory-ro-501-20260930-222840.private.json` |
| `native-501.kb` is still the 2026-09-26 export (1540 bytes, mode 0600) | `/var/lib/t2-touchid/native-501.kb` |
| Approved canary, 2026-10-01 | one `load-keybag` of that file, session 1 handle 1, `set-system-keybag` onto `-501` status 0. `unlock-keybag 1 1` was AKS operation `0x4`, SEP status **-5**, flags `0x0`, surfaced as `EREMOTEIO`. Special `-501` was not unlocked. The match window was not opened. |

The next step written here was the macOS export. That return completed
on 2026-10-03. See the standing state above. The sentence in this
record that says there is no macOS `user.kb` describes 2026-10-01.

Everything under this heading is a session record from the date in its
heading. It is not a live order. Where an old paragraph says the work
is parked, waiting for permission, or that endpoint 7 must stay parked,
that sentence describes that day.

## Prior standing state (2026-09-30 17:41, empty inventory)

Transport was loaded again on kernel `7.2.7-arch1-Watanare-T2-2-t2`
(`t2_sep_transport` + patched `applesmc` boot_state). Read-only inventory
for uid 501 completed public-only (private dump gated incomplete).

| Fact | Evidence |
| --- | --- |
| Per-user `0x42` status **0**, output nil → identity count **0** | `INVENTORY_RO_501_20260930-174149_*` |
| Catacomb UUID/hash (`0x38`/`0x3A`) status **22** — no user component for 501 | same |
| SKS lock (`0x27`) **21** (`0x15`, cold) | same |
| BridgeXPC port **49208**; private inventory not written (gate incomplete) | same; oneshot fix in `t2-inventory-ro-501.*` |
| Kernel upgrade had dropped modules; rebuild+install restored transport | `AGENT_STATUS_2026-09-30.md`, `ELEVATE_NEEDED_2026-09-30.txt` |

The next step written here was the macOS one-finger re-enroll, then a warm
reboot and another inventory. That step completed the same night. The
result is the standing state above.

## Prior standing state (2026-09-26, after the type-5 create)


Fresh Omarchy and a fresh macOS volume are installed. This boot published
the SMC boot record, endpoint 7 answered, and one Linux-owned bag for user
501 is bound at `-501`. User 501 still has no fingerprint. Do not create a
second bag. Do not reboot before the enroll dance: handles 1 and 2
evaporate, and the saved file is the durable copy.

| Fact | Evidence |
| --- | --- |
| `t2_sep_boot_state` is `response-received:1` for bridgeOS `23.16.16068.0.0,0`, epoch 1.0. Capabilities then returned `0x2` | this boot, after `packaging/applesmc-t2-sep-boot/` |
| Before that publication, cold boots left the SEP CPU stopped (`+0x8028=0x7f`) and one endpoint-7 read timed out | earlier 2026-09-26 boots |
| User 501 `0x42` was status 0 with nil output. Alias `-501` was absent (`-3`) before the create | same boot, pre-create |
| Operation `0x01` version 5 with a type-5 ACM secret returned status 0, live handle 1, KEK length 162. Export returned status 0, saved length 1540. Reload returned handle 2 and the bag UUID matched. `set-system-keybag` of handle 2 onto `-501` returned status 0, and the alias read back present | `src/bridge-aks-native-501.py`, then `t2-aks-tool set-system-keybag 1 2 -501` |
| Saved root-only files: `native-501.kb` (0600), `native-501.form` and `native-501.account` (0400), under `/var/lib/t2-touchid/` | same |
| `t2-keybag-load.service` still starts the SEP transport through `Requires=` even when `t2-sep-transport.service` is disabled | this boot's journal |
| A bag installed over an existing macOS `-501`, plus a Catacomb save, left enroll at 22. That was a different bag. Enroll with no credential returns `-3` | `NEW_BAG_501_VERDICT_2026-09-25.md`, `ENROLL_U1_VERDICT_2026-09-20.md` |

The publisher source hash is
`4edb24f48a39b1f56522be4dd5d6f8c2650e8b1c63d279cf9a3c2ccff6d561a6`.
The warm pins are unchanged:
`register_ool=1 register_acm=1 aks_start_cpu=0 aks_ep0_nop=0 aks_discover=0 aks_device_state_canary=0`.

## Recorded next (2026-09-26, halted)

This boot reloaded `native-501.kb` as handle 2. Alias `-501` was already
present and names that same bag. No bind and no second create.

`bridge-xpc-enroll-native-501.py --handle 2` then ran cleanly. Context
cleanup no longer disables endpoint 10.

| Check | Result |
| --- | --- |
| Session prep, including xART and enabled-unlock | status 0 |
| User 501 identity count | 0 |
| Operation `0x21` option `0x100` | status 0 |
| Zero-group enroll start | status 1 |
| Finger dance | not run |
| ACM cleanup | succeeded |

Status 1 is a refusal. It is not status `22` and it is not a timeout.
The same start returned 1 on the previous boot, before the cleanup bug
hid it. Do not repeat this dispatch until the status-1 reason is known.

1. **Find why the authorized zero-group start returns 1 for an empty
   user-501 inventory.** Do not send another start, another create, or
   another `0x21` on top of this result.

## Prior standing state (2026-09-25)

User 501's fingerprints and Catacomb entry were removed. Alias `-501` still
held the macOS keybag. A Linux-only first identity was not open. The macOS
re-enroll recovery below was the plan before the fresh install.

| Fact | Evidence |
| --- | --- |
| `0x48` for uid 501 returned 0. Identity count 2 → 0, twice. `0x3c` no longer lists 501. `0x38` returns 22 | `EMPTY_SEP_HALT_2026-09-25.md` |
| `-501` still has the macOS bag. Primary-identity read `0x51` did not return absent | same |
| No recovered command deletes that bag. Unload `0x05` removes one handle. `0x51` suboperations 1 and 2 transfer primary state; they are not a reset | `IDENTITY_RECONCILIATION.md` in the reference tree; this branch's halt notes |
| DFU Revive reinstalls bridgeOS and leaves a provisioned T2. Erase All Content and Settings and DFU Restore are macOS or second-Mac procedures. Neither has been shown to leave this Air with primary identity absent | Apple Configurator revive/restore docs; reference `BRIDGEOS_DIAGNOSTICS.md` |
| A bag we create can export and accept its creation reference. Installed as `-501`, with a user-501 Catacomb save, enroll still returns 22 | `NEW_BAG_501_VERDICT_2026-09-25.md` |
| The saved scratch bag will not reload (`-9`). After the alias swap it will not reinstall as `-501` or `-502` (`-1`) | `SCRATCH_RELOAD_HALT_2026-09-25.md`, `CATACOMB_REBIND_HALT_2026-09-25.md` |
| `t2touch`'s empty-SEP installer is real and was proven on MacBookPro16,1, same bridgeOS `23P6068`. It refuses to run until the primary identity is already absent. That result does not qualify this Air | reference `linux_native/README.md`, `CATACOMB_BOOTSTRAP.md` |

**Air right now:** biometric user 501 is empty. The macOS keybag is still
at `-501`. Do not send another removal, another `0x51` shape, or another
create on top of that bag.

## Superseded recovery (2026-09-25)

1. **Recovery, from macOS.** Enroll one finger. The Apple account and the
   keybag are still in the T2. Then warm-reboot to Linux with no power-off.
   Re-check `0x42` for uid 501 and a warm `load-keybag` before trusting the
   reader. This is the way back to the working macOS-bag path.
2. **Linux-only first identity stays closed** until a primary-identity read
   returns absent. The only documented ways to chase that absence are Erase
   All Content and Settings, or a DFU Restore from a second Mac. If that is
   tried, stop at Setup Assistant and boot Linux before any new Apple
   account. Then read whether `-501` and operation `0x51` suboperation 0 are
   actually absent. If they are not, the erase did not clear the keybag.
   Do not finish macOS setup first. That provisions the chip again.

The 2026-09-07 list below is history. Its "Air right now" count is stale.

## What we know (2026-09-07)

| Fact | Evidence |
| --- | --- |
| Bridge open works (Multiverse → 0 → client-ver 2 → 1) | warm A/B |
| Once enrolled, `0x42` survives soft reboot **and** power-off **without** Linux `0x40` | cold A/B notes |
| `0x54` accessoryInfo: **all-zero 83 B** on Linux; macOS caches builtin accessory **before** load | `ACCESSORY_*` notes |
| `0x40` → **257** with or without reset preflight; USB LTFC extract looks structurally valid | load notes |
| bent: 257 ↔ missing accessory/device-group context; same `0x54` first_byte=0 on their Linux | bent touch-id / catacomb handoff |
| `no_catacomb(0xffffffff)` cleared `0x42` here; reset alone did **not** | `RESET_THEN_LOAD40_2026-09-07.md` |

**Air on 2026-09-13:** `0x42` count **1** (re-warmed via single-boot
macOS trip → warm reboot, no sensor reset; verified SKS `0x10`).
Superseded by the standing state above: count is 0 as of 2026-09-25.

## Next (in order)

### 1. Accessory / host cache — status

**Done (Linux):** `0x54` all-zero (`ACCESSORY_0x54_NOTES.md`).

**Done (Sequoia):** `cacheAccessories` before `loadCatacomb`
(`ACCESSORY_MACOS_CONTRAST_2026-09-07.md`).

**Done (private opcodes):** unlock-path **82→84**; **84** all-zero on macOS
too; cache still succeeds from **82**
(`ACCESSORY_PRIVATE_OPCODES_2026-09-07.md`). Nonzero `0x54` is **not** an
MBA91 hard gate.

**Done (Omarchy host-parity):** ready=1, prov=5, cal_present=True, xART,
`0x52` builtin, warm `0x42`=1 (`HOST_PARITY_CANARIES_2026-09-07.md`).

**Done:** no-reset `0x40` after host-parity preflight → still **257** both
blobs; warm `0x42` preserved (`LOAD40_HOST_PARITY_2026-09-07.md`).

**Done (offline + read-only):** FDR Bridge method **11** returns **61407 B**
on Omarchy (matches macOS cal length); load path is Mesa **`0x20` value=3**
(`MSR_CAL_LOAD_MAP_2026-09-07.md`). MSRk still unknown.

**Done (Sequoia):** this boot **calBLOBSource 0** (no `setCalibration` /
no Mesa 32). Source-3 boots log 61407@3 but Db `0x20` lines were dropped —
inference only (`MSR_CAL_SEQUOIA_CONFIRM_2026-09-07.md`).

**Done:** Mesa **`0x20` value=3** status **0**; follow-up `0x40` still **257**
(`LOAD_CAL_0x20_2026-09-07.md`). Cal loops remain open.

**Done (map):** `LOAD40_ENVELOPE_MAP_2026-09-07.md` — macOS boot load is
mostly Common/unarchive (**A**); our Mesa LTFC `0x40` is path **B**. 257 may
mean wrong tool for warm SEP, wrong blob class, or empty-gate bent also lacks.

**Fork unblocked (2026-09-08):** A (warm match/`0x04`+ACM), B (Sequoia
Mesa-64 mine), and C (empty-SEP load envelope) are all back on the table.
See `PARKED_2026-09-08.md`.

### 2. Re-warm identity (ops)

macOS Touch ID → Omarchy warm handoff to restore `0x42` when you need a
non-empty list again (match UX, etc.). Proven; independent of (1).

### 2b. Next macOS trip checklist (single boot covers all) — DONE 2026-09-13

Trip completed unlock-only variant (existing uid-501 enrollment kept, no
live enroll); evidence in `MESA64_FRESHBOOT_MINE_2026-09-13.md`. SEP was
empty pre-trip; re-warm verified post-trip (`0x42`=1, SKS `0x10`).
Kit procedure: `README.md` + `CHECKLIST.md`; exports/teardown:
`BACKUP_AND_TEARDOWN.md`.

1. Install capture daemon → `chmod 755` + `a+r` on `/var/log/t2-aks-capture`
   → install `EnablePrivateLogging.mobileconfig` → confirm `PRIVATE_DATA`
   → cold reboot.
2. **B mine:** around `loadCatacombForComponent` / `loadCatacombForUser`,
   search for `performCommand … 64` (decimal). Record present/absent (+
   `inValue`/`inSize` if present). Prediction: absent (boot load is
   host-side unarchive).
3. Enroll one finger, lock-screen unlock once; confirm both succeed.
4. Export newest capture set + `/Library/Catacomb/<UUID>/` +
   `t2-keybags.tar.gz` to `~/Private/` and USB. **Skip ESP FDR** (absent/N/A).
5. `sudo ./uninstall.sh`; remove the Device Management profile.
6. Warm reboot to Omarchy (no sensor reset) to restore `0x42=1`.
7. Report back: `sw_vers`, `PRIVATE_DATA` state, enroll/unlock success,
   Mesa-64 verdict, USB contents confirmed.

### 3. Retry `0x40` / match

Live `0x40` or match/`0x04` / ACM work is open for assisted research.

### 4. Linux-native enroll / ACM

Open for assisted research.

### 5. Last resort (EP7)

EP7 AKS stays muted (separate transport dead-end); fingerprint path is BridgeXPC.

## Open items

- Mute AKS EP7 (dead-end transport; BridgeXPC path preferred)
- Live Mesa match / `0x40` / ACM canaries (unblocked 2026-09-08)
  - 2026-09-13: Fork A match opens (status 0, no 261) but yields no
    `match_result` in 6 windows incl. calibrated + confirmed touch +
    60 s continuous-contact hold —
    see `MATCH_FORKA_2026-09-13.md`. Sequoia unlock prelude comparison:
    working unlock sends zero opcode-4 (`48 → 84 → 39 → 84 → 12 → 74`).
    Warm `0x42=1` preserved throughout.
  - 2026-09-13 window 7: 74 with Fork A framing refused at dispatch
    (**258**) after clean Sequoia prelude, no module loaded, one shot
    no variants. SKS read `0x810` (stable) afterwards vs `0x10` at
    warm-verify; `0x42` intact. 4-opens/74-refuses, identical payloads.
- Sequoia Mesa decimal-64 boot mine — DONE 2026-09-13 (third independent
  confirmation): full-boot sweep **0 hits** for `performCommand … 64`;
  boot histogram without 64; unlock framing `48 → 84 → 39 → 84 → 12 → 74`
  with match traffic on 74 — see `MESA64_FRESHBOOT_MINE_2026-09-13.md`.
  Path B is a command macOS doesn't use; closed.
- Blind `0x40` / reset-load loops (open)
  - 2026-09-13: no-reset `0x40` master+user re-run on warm `0x42=1` boot:
    **257/257**, snapshots identical before/after, warm preserved.
  - 2026-09-13: full reset → `no_catacomb(0xffffffff)` → `0x40` re-run:
    reset 0, `no_catacomb` 0, **257/257**, `0x42` went **1→0**.
    Reset alone again did **not** clear (count 1 after reset).
    Air now at `0x42` count **0** — re-warm via macOS before any match work.
- Host-parity-only `0x40` (still 257)
- `0x20` then `0x40` (cal OK, load still 257)
- Assuming power-off clears enrolled `0x42` (falsified — noted)
- `0x08` as alias for `0x42` (investigation open)
- Linux-native ordinary (token-free) enroll `0x03` uid 501 (2026-09-13):
  start rejected **status -3**, no events, no state change — with and
  without same-session sensor context. Pre-enroll context probe passes
  every precondition (bridge init, readiness, provisioning, protected
  config, xART, catacomb consistency), so -3 is purely the dispatch
  gate. SEP still empty.
- ACM-token path, first live run as root (2026-09-13 late, `/dev/t2-acm`
  generation 1): context **create/delete succeeded** (tracking 21 B),
  policy-1007 preflight = unsatisfied **type-1 passcode requirement**
  (state 1, flags 1), wall at exactly **`password-binding`** with
  mandatory cleanup — no `/run/t2-touchid/keybag.env`, no installed
  `t2-aks-tool`, EP7 canary still -110. No authorized 16 B form exists,
  so no `authorized_enroll_fields` dispatch was built. Endpoint-10
  itself is alive; the block is the keybag-bound password proof.
- `0x30` getEnabledForUnlock shape recovered (2026-09-13, Linux-only):
  v1 (empty or uid501) → status 0, 1 byte; reads **enabled=True** for
  uid 501 even with empty SEP. v0 → `0xe00002c2`. `0x11` empty-in →
  status 22 (needs its ~20 B input; not sprayed).
- Re-mine of the 2026-09-06 cold-boot capture (2026-09-13 late, no boot):
  **1,731** tagged `performCommand` events across boot/enroll/unlock
  contain **zero opcode-64** — second independent confirmation Sequoia
  never sends Mesa `0x40`. Path B is not a wrong constant, it is a
  command macOS doesn't use. Unlock framing is `48 → 84 → 39 → 84 →
  12 → 74` (match traffic on **74** between 84s); opcode **65** appears
  exactly once, in enroll, unannotated.
- Bounded read-only probes, operator-authorized, 9 calls (2026-09-13
  late, empty SEP, state verified unchanged): `0x08` v1 → **status
  265** (novel), v0 → `0xe00002c2`; the 400 returned bytes are
  **all zero** — the daemon returns the preallocated out-buffer
  unfilled on error paths, so `out_len == cap` on failures is
  meaningless everywhere (status only). `0x11` zero-fill at 16/20/32 →
  **22 every time**: content-gated, not length-gated; oracle closed.
  `0x41` ver=1/val=0/empty → `0xe00002c2` (one call, not chased).
  Lesson: brute-forcing small fields cannot converge — remaining
  unknowns sit behind enrolled SEP state or the framework binary.
- APFS offline-read attempt (2026-09-13 late): built `apfs-fuse-git`,
  but open fails at **`KeyManager` init** in both `apfs-fuse` and
  `apfsutil`, before any password prompt. T2 + Sequoia + FileVault
  container keybag is SEP-wrapped — no Linux tooling unwraps it.
  Mount track dead; framework binaries stay behind a macOS boot.
- Warm-SEP insmod crashes (2026-09-13, 2/2, journal-proven): loading
  `t2_sep_transport` on a **warm** SEP kills the machine with no panic
  or oops — the journal just stops (boot -3 died mid-load at 01:18:45;
  boot -1 completed bring-up then `cdc_ncm enp116s0f1u1: NETDEV
  WATCHDOG: transmit queue timed out` 9 s later, then death). Cold-SEP
  loads are stable for hours. Warm bring-up also shows a different
  outbox (`0x29901` vs cold `0x20001`). Suspect: CPU-start poke /
  OOL-DMA registration against a session-active SEP wedges the T2
  (which owns power). Rule until disproven: **no insmod on warm SEP**
  with default params. Minimal-bring-up hypothesis (untested):
  `aks_start_cpu=0 aks_discover=0 aks_acm_canary=0
  aks_device_state_canary=0`. Decisive decoupling: Fork A / 74 match
  traffic rides **BridgeXPC/NCM in userspace and needs no module** —
  warm match work proceeds with the module unloaded; insmod returns
  only for ACM-specific steps, minimally parameterized.
- Minimal-bring-up SURVIVED warm SEP (2026-09-13): `register_ool=1
  register_acm=1 aks_start_cpu=0 aks_ep0_nop=0 aks_discover=0
  aks_device_state_canary=0` → all three nodes registered, NCM alive
  past the 9 s death mark, 20+ min uptime, no watchdog. Prime suspect
  remains the CPU-start poke (untested in isolation — one variable at
  a time if ever revisited). ACM lifecycle on warm SEP: create/delete
  + policy-1007 preflight (type-1, unsatisfied) identical to cold.
  Warm `0x42=1` intact throughout; SKS `0x810` stable.
- EP7 is SELECTIVE, not mute (2026-09-13, warm SEP, minimal module):
  `load-keybag` → status 0 handle 1; `set-system-keybag` → status 0;
  `copy-keybag-uuid` → present; `unlock-keybag-stdin` (macOS login
  password, operator-entered via ask-password, never stored) →
  status 0; `verify-password-acm` → status 0 with **policy 1007
  SATISFIED** — first authorized ACM context in program history. Only
  the `0x19` device-state canary and capabilities query time out.
  Staged: trip-exported login keybag, `/etc/t2-touchid.conf`
  (uid 501 / -501 / tim), `/usr/local/sbin/t2-aks-tool` installed,
  `/run/t2-touchid/keybag.env` (session 1, handle 1, special -501).
  Every "EP7 dead-end" note above is revised accordingly: the wall was
  never the transport, it was the missing credential. Password handling
  throughout: operator terminal only, no disk/git/log copies.
- Authorized enroll dispatch (2026-09-13, warm SEP, `bridge-xpc-
  authorized-enroll.py`): bind `status=0`, policy satisfied, then
  command-3 v2 dispatch refused — `0xe00002c2` on a 52 B payload
  (authoring bug, fixed to canonical 68 B), then **22** on the exact
  68 B shape, with and without read-only session prep (0x52/0x53/0x43/
  0x4C/0x30 all status 0 standalone). Session-state hypothesis dead;
  prime suspect is credential generation (tracking `0x24` vs legacy
  `0x01` external form) — `--legacy-context-create` staged, one
  bounded attempt pending. SKS drifts `0x10 → 0x810 → 0x239` with
  `0x42=1` intact throughout: session coloring, not a gate.
- Legacy form also refused **22** (2026-09-13, full prep green, cancel
  0, identities 1→1, context cleaned). Generation ruled out. The 22
  now points below shape entirely — likely the v2 enroll *flow*
  (`0x03` bare start + `0x0e` continue protocol + adjacent `0x65`,
  per Sequoia enroll-phase histogram) rather than inline-token `0x03`,
  a Catalina-era model never live-proven. Live enroll attempts parked
  (5 contexts spent, warm SEP intact, machine 40+ min stable on
  minimal bring-up).
- `0x0e` enrollContinue mapped (2026-09-13, warm SEP): opens **status
  0** with empty input, emits **zero events in 30 s fingerless and
  60 s held**, cancels clean, no state change (`0x42`=1 throughout).
  It arms a channel that needs structured follow-up input — whose
  shape is unmined anywhere accessible (no codec on disk; the 09-06
  raw enroll log is gone, only its histogram survives). No further
  `0x0e` windows until arg shapes are recovered.
- Enroll arg shapes recovered (2026-09-13 enroll-phase trip, boot
  `62D1A28F-…` `20260913T092455Z`, macOS 15.7.9 — new finger enrolled,
  then one lock-screen unlock verified `MATCH` uid 501): see
  `ENROLL_ARG_SHAPES_2026-09-13.md`. Sweep over the enroll minute:
  `3` ×1 (ver 2, inValue 0, **68 B token**), `14` ×**8** (ver 1,
  inValue 0, **0 B every time**), decimal `65` (= `0x41`) ×1 (ver 1,
  inValue 0, **4 B**, ~10 s pre-enroll), `4` ×1 post-enroll (ver 1,
  inValue 0, **68 B**). Notation: trip note "`0x65`" was decimal-65
  shorthand; decimal 101 (`0x65` proper) appears zero times in the
  30 k-line boot log. Linux-side: `t2_enrollment_protocol` /
  `t2_enrollment_bridge` are already shape-faithful (v2 68 B start,
  empty v1 continue), and decimal 65 matches the existing `0x41`
  free-capacity codec (uid 4 B, v1). What this closes: the `0x0e`
  input-size sequence (the missing datum — all empty, N=8, pacing
  ~1–2 s, each glued to `enrollContinue → Success`) and the
  `0x03` bare-vs-token question (token). What it does not recover:
  the 68 B token *contents* (never logged). The live 22-on-68 B
  refusal and the parked live-enroll stance are unchanged — no new
  preflight, no live attempt proposed here.
- Authorized-74 window (2026-09-13, warm SEP, minimal module,
  `bridge-xpc-match74-authorized.py` staged): fresh ACM tracking context,
  `verify-password-acm` status 0 (policy 1007 SATISFIED), warm gate true
  (`0x42` count 2, SKS `0x11` — new drift value, `0x42` intact
  throughout), Sequoia prelude all status 0
  (`48`→1 B, `84`→83 B, `39`→4 B, `84`→83 B, `12`→nil), then **74
  empty refused 258** — identical to plain empty-74 (window 9) and
  Fork-A 68 B 74 (windows 7–8). First attempt's silence was a harness
  bug (diagnostic printed on one path only, plus an over-strict SKS
  gate); fixed to record-and-raise with SKS informational, second run
  reporting fully. Conclusion: the 74 gate is **neither input-shape nor
  ambient password-context**. Remaining 74 hypotheses, if any, are
  credential-in-payload (inline token à la `0x03`'s 68 B authorized
  form) or 74-isn't-match-start on this build (label stays
  medium-confidence) — both design questions, no live attempt staged.
  Gate re-disabled in source; `0x42`=2 preserved, capacity
  repeat-equal. SKS `0x11` joins `0x10/0x810/0x239` as observed-warm
  session coloring, never a gate.
- C3 version-gate closed (2026-09-13, warm SEP, no module needed):
  74 empty at wire **ver 2** → **`0xe00002c2`** (bad argument), prelude
  all 0, warm gate true (`0x42`=2, SKS `0x11` stable). The SEP knows 74
  at ver 1 only; the version axis is dead in one shot as designed.
  Remaining payload candidates (C4/C1/C2) stay parked behind the Fork B
  mine per the design note. Gate re-disabled; `0x42`=2 preserved.
- Unlock-minute arg shapes, capture-mined 2026-09-13 (48 performCommand
  lines, ver/val/inSize only — trailing hex is buffer pointers, not
  sizes; payloads never extracted): `48` v1/0/empty, `84` v1/0/20 B,
  `39` v1/0/4 B, `12` v1/0/empty, **`74` v1/0/empty ×3**. macOS sends
  74 with NO input — our 68 B Fork A framing was a shape rejection
  (258), not necessarily a credential gate. `--empty-match-input`
  staged for one bounded window-9 attempt. Save cluster after: 60/80
  empty, 61/62/63 v2/24 B context. No 03/04/65/14 anywhere
  (unlock-only trip; enroll choreography still unmined — the 09-06
  raw log is gone, only its histogram survives).

## Doc index

| Note | Topic |
| --- | --- |
| `STATUS80_SELECTOR_2026-10-03.md` | Status 80 calls `operationEndsWithReason:` 2, state 4 |
| `STATUS80_HANDOFF_2026-10-03.md` | Linux enroll froze on BKOperation status 80 |
| `EXPORT_RETURN_FINDINGS_2026-10-03.md` | macOS `user.kb` and Catacomb return |
| `WARM_IDENTITY_AB_2026-09-07.md` | smoke + warm |
| `WARM_CATACOMB_PROBES_2026-09-07.md` | store API split |
| `COLD_*_AB_2026-09-07.md` | preserve ladder |
| `LOAD_CATACOMB_0x40_2026-09-07.md` | no-reset 257 |
| `RESET_THEN_LOAD40_2026-09-07.md` | reset + still 257 |
| `MESA_BENT_OPCODE_CROSSWALK.md` | opcodes |
| `ACCESSORY_0x54_NOTES.md` | accessoryInfo / all-zero reply |
| `ACCESSORY_MACOS_CONTRAST_2026-09-07.md` | Sequoia cacheAccessories → loadCatacomb |
| `ACCESSORY_PRIVATE_OPCODES_2026-09-07.md` | private 82→84; 84 all-zero on macOS |
| `HOST_PARITY_CANARIES_2026-09-07.md` | Omarchy ready/prov5/cal-present |
| `LOAD40_HOST_PARITY_2026-09-07.md` | preflight OK, 0x40 still 257 |
| `MSR_CAL_LOAD_MAP_2026-09-07.md` | FDR method 11 + Mesa 0x20 map |
| `MSR_CAL_SEQUOIA_CONFIRM_2026-09-07.md` | calBLOBSource 0 vs 3; no captured 32 |
| `LOAD_CAL_0x20_2026-09-07.md` | 0x20 OK; 0x40 still 257 |
| `LOAD40_ENVELOPE_MAP_2026-09-07.md` | Common load A vs Mesa 0x40 B |
| `PARKED_2026-09-08.md` | authorization record; forks unblocked |
