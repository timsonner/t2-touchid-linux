# Status-1 diagnosis: authorized zero-group enroll start (2026-09-30)

Branch: `research/mba91-aks-ep7`. Phase 1 only — docs/code analysis.
No enroll start, create, `0x21`, reboot, or second bag was sent.
Shapes/statuses/counts only.

**Placement:** written under `tools/` because
`tools/mba91-aks-macos-capture/` is root-owned on this host. Operator
move when convenient:

`sudo mv tools/STATUS1_DIAG_2026-09-30.md tools/mba91-aks-macos-capture/`

## Standing fact (from NEXT_STEPS 2026-09-26)

| Check | Result |
| --- | --- |
| Session prep (incl. xART, enabled-unlock) | status 0 |
| User 501 identity count | 0 |
| Operation `0x21` option `0x100` | status 0 |
| Zero-group enroll start (`0x03` v2 68 B) | **status 1** |
| Finger dance | not run |

Status 1 is a refusal. It is not `22`, not `-3`, not `257`, not a
timeout. Same start returned 1 on the prior boot (cleanup bug had
hidden it). Do not repeat the dispatch until this note's Phase 2
read-only check is done.

## (1) Concrete hypothesis

**Leading hypothesis — wrong enroll credential class on an empty
never-enrolled uid-501 namespace.**

`bridge-xpc-enroll-native-501.py` authorizes with AKS operation
`0x21` option `0x100` (type-5 creation reference on an input ACM
context + a second target context whose external form is the enroll
token). That path is **not** the password-bound policy-1007
`TouchIdEnrollment` ceremony that opened enroll on this Air (E1/E4).

The zero-group 68 B framing is already proven good under the password
path. Status 1 is therefore attributed to **what the start token
represents** (creation-reference / `0x100` target form) interacting
with **empty user-501 inventory on a Linux-owned `-501` bag**, not to
group bytes or prep.

Secondary (inventory) clause: after a fresh volume with no finger
ever enrolled, uid 501 may also lack a loadable user Catacomb
component. Missing-component enroll on this Air has previously
surfaced as **22** (C5 / CATACOMB_PRESENCE), so component absence alone
does not explain **1** — but it must be classified before any further
start, because empty-first-enroll and add-finger are different SEP
baselines.

## (2) Evidence

### Refusal vocabulary (extended)

| Form / situation | Dispatch | Source |
| --- | ---: | --- |
| Token-free | -3 | ENROLL_U1, early NEXT_STEPS |
| Dead ACM reference | 257 | ENROLL_U1 |
| Live form, wrong shape / gated UID (group-1, C5-502) | 22 | ENROLL_U1, ENROLL_C5 |
| Live form, password-bound policy-1007, provisioned 501, count≥1 | 0 | ENROLL_E1 / E4 |
| `0x100`/`0x200` creation-ref form, uid 502 | -3 | SCRATCH_ENROLL_HALT, SCRATCH_ENROLL_200_HALT |
| `0x100` + zero-group, uid 501 empty, Linux `-501` | **1** | NEXT_STEPS 2026-09-26 |

Status 1 is a new cell. Stopping rule in ENROLL_E_DESIGN already
says any start status outside `{0,22,-3}` → halt and analyze.

### Credential-class evidence (strong)

- SCRATCH_ENROLL_HALT / SCRATCH_ENROLL_200_HALT: option `0x100` and
  `0x200` both SEP-accept (status 0), then enroll dispatch **-3** —
  "not the mark enroll reads." Password-bound context on the same
  uid is seen (then 22 for 502).
- SCRATCH_VERIFY: `0x100` "proves the credential matches. It does
  **not** satisfy policy 1007 for enrollment."
- POLICY_COMPARE: policy satisfied/type/state/flags can match a real
  password bind and still fail enroll; **which bag** performed the
  verification matters.
- E1: identical zero-group packing
  `(0, uid, 0, 16) + form + 36×0` opened **0** only with a live
  password-bound ACM form (ENROLL_E1, `SensitiveEnrollmentRequest`).
- Native script (`bridge-xpc-enroll-native-501.py`): after `0x21`
  option `0x100` status 0, packs **target_form** into that same
  zero-group layout — never calls `with_authorized_context` /
  policy-1007 / `verify-password-acm`.

### Empty-inventory / Catacomb evidence (supporting, incomplete)

- Standing: `0x42` for 501 is nil / count 0; never enrolled on this
  fresh volume (NEXT_STEPS).
- CATACOMB_PRESENCE: uid without component → `0x38` status **22**;
  "same word enroll returns" for C5-502.
- EMPTY_SEP_HALT: after `0x48`, `0x3c` drops 501 and `0x38` → 22.
- CATACOMB_BRIDGE_SEQUENCE (macOS first enroll): boot can
  `loadCatacombForUser:501` with empty UUID `0000***` **before**
  first finger — host file load, not Linux's current path.
- This boot's post-create standing table never recorded `0x38` /
  `0x3c` / `0x41` for 501. That gap is the Phase 2 read-only target.

### Framing ruled out

- E1 falsified group-u32=1 vs zero; zero opens under password ACM.
- Native-501 uses the E1/E4 zero-group layout, not the old group-1
  authorized-enroll packing.

## (3) Phase 2 one-variable canary

**An enroll-start canary is not justified yet.** NEXT_STEPS forbids
another start until the status-1 reason is known; we still lack the
Catacomb/component baseline for this empty 501.

**Justified Phase 2 = one read-only inventory canary** (no start, no
create, no `0x21`, no reboot, no second bag):

After Tim restores a working SEP transport (see below), on a warm
bridge with handle 2 / `-501` already as standing state:

```bash
# Read-only. Record statuses/lengths only — no payloads to git.
cd /home/tim/Projects/t2-touchid-linux
sudo python3 src/bridge-xpc-probe.py \
  --initialize --full-inventory --macos-user-id 501 \
  --private-inventory-output /home/tim/Private/t2-touchid/status1-inv-501.json
```

Minimum targeted reads if full inventory is inconvenient: `0x42`
(uid 501), `0x38`, `0x3a`, `0x3c`, `0x41` (free capacity), plus
confirm alias `-501` still names the Linux bag. Compare to
CATACOMB_PRESENCE table.

Interpretation:

| `0x38` / `0x3c` for 501 | Implication |
| --- | --- |
| 22 / absent (like 502) | Empty-namespace + no component; status **1** is still not the usual **22** map → credential-class hypothesis stays leading; do **not** enroll-start; next human choice is macOS first-finger recovery or a separate Catacomb-bootstrap design (out of Phase 2) |
| 0 / present (empty UUID ok) | Component gate is not the blocker; strengthens pure credential-class hypothesis; still **no** repeat of `0x100`+start until a different auth producer exists |

**Not justified as Phase 2:** re-running
`bridge-xpc-enroll-native-501.py`, swapping only target vs input form
(SCRATCH already -3'd both on 502), or `verify-password-acm` against
the Linux bag (NATIVE_C4 → SEP `-5`). Those either repeat the forbidden
start or are already answered / blocked.

## (4) What needs Tim (human)

1. **sudo / operator presence** for any live BridgeXPC inventory
   (root-only conf, `/var/lib/t2-touchid`, private inventory path).
2. **Restore `t2_sep_transport`** for this kernel
   (`7.2.7-arch1-Watanare-T2-2-t2`): current boot's
   `t2-sep-transport.service` failed with
   `Module t2_sep_transport not found`. No read-only probe until that
   loads. Bag files under `/var/lib/t2-touchid/` are root-only; do not
   reboot casually — standing note: handles evaporate; saved
   `native-501.kb` is the durable copy (reload, no second create).
3. **No enroll start / create / `0x21` / second bag** until Phase 2
   inventory is journaled and this hypothesis is confirmed or
   replaced.
4. **Strategic call after inventory:** if Linux-only first finger
   remains closed, the documented recovery is still macOS enroll one
   finger → warm reboot to Linux (NEXT_STEPS superseded-recovery /
   EMPTY_SEP path). That is operator time on the macOS volume, not a
   script canary.
5. **Move this note** into `tools/mba91-aks-macos-capture/` with sudo
   when ready (dir is root-owned).

## Do-nots (carry forward)

- No second `bridge-xpc-enroll-native-501.py` start.
- No second keybag create / alias rewrite / `0x21` on top of status 1.
- No `0x40` / reset / `no_catacomb` / `0x48` near this window.
- No commit of raw inventory payloads, forms, or keybags.
