# MATCH canary plan — password-bound path vs surviving macOS finger (2026-09-30)

Branch: `research/mba91-aks-ep7`. Track A already approves this research
(`docs/LAB_PROTOCOL.md`). The canary below was approved and run on
2026-10-01. It stopped at unlock: session 1 handle 1, AKS operation
`0x4`, SEP status **-5**, flags `0x0` (`EREMOTEIO`). Special `-501` was
not unlocked. Sections B and C were not run. Do not treat this file as
a second permission check.

Standing baseline (RO inventory `…-222840`, interpretation
`CATACOMB_IDENTITY_LAYOUT_20260930-222840.md`):

| Fact | Value |
| --- | --- |
| `0x42` uid 501 | count **1** (20 B) |
| Catacomb | present; `0x3C` = `[0xFFFFFFFF, 3, 501, 3]` |
| SKS `0x27` | **16 = 0x10** (warm) |
| Port / host / iface | **49183** on 2026-09-30; **49213** on the 2026-10-01 cold boot. Host `fe80::aede:48ff:fe33:4455`, iface `enp116s0f1u1` |
| Private inventory | written; UUID/hash **presence** already recorded in public summary (no raw material in git) |
| Transport this boot | `t2_sep_transport` loaded; `/dev/t2-{aks,acm,sep-lab}` present |
| Keybag session | Durable bag = **`native-501.kb`** (no macOS `user.kb` on this track). systemd `t2-keybag-load` still gates on `user.kb` → skipped; use MBA91 `warm-bringup` override. Session file may be absent until `--bring-up` / manual load |

Context: K1/K2 (2026-09-20) proved **token-free** opcode-4 verifies with
**unlocked** keybags (password not structurally required at match time). This
plan still stages the **password-bound F1** path against the new **one-finger**
baseline, because standing NEXT_STEPS asks for that research step and F1 is the
proven ACM+`verify-password-acm` harness.

**Bag correction:** do not stage macOS `user.kb` on this volume. Use
`native-501.kb` via MBA91 warm-bringup
(`CORRECTION_NO_MACOS_USER_KB_2026-09-30.md`).

## Specimen halts

Track A approval is unchanged. These are answered shots for this finger
and this bag, collected in the standing block of `NEXT_STEPS.md`.

- No Linux enroll start (`0x03` / enroll workers).
- No bag **create**, no **second** bag, no alias rewrite.
- No creation-reference `0x21` option `0x100`/`0x200` (native-enroll path).
- No `0x40` / reset / `no_catacomb` / `0x48` near this window.
- No 74 traffic (closed matrix).
- No default-param warm `insmod` (loader pins only).
- No commit of raw inventory, forms, keybags, or passwords.

**Clarify:** F1’s `verify-password-acm` also uses AKS op `0x21` in
`t2-aks-tool`, but that is the **password-bind-into-ACM** request shape from the
proven F1/R1 path, and it is distinct from the creation-reference options
`0x100`/`0x200`. The 2026-10-01 canary was approved and stopped at
unlock `-5`, so this `0x21` was not sent.

## Prerequisites

1. **Transport / BridgeXPC** — already green this boot (nodes + port 49183).
2. **SKS warm** — inventory showed `0x10`; re-check after keybag unlock if desired
   (informational only; F1 does not gate on SKS).
3. **Keybag file + session** — corrected bag path (see
   `CORRECTION_NO_MACOS_USER_KB_2026-09-30.md`):
   - There is **no** macOS `user.kb` export on this track. Do **not** restore or
     copy/rename a bag to `user.kb` to satisfy systemd.
   - Durable bag = **`/var/lib/t2-touchid/native-501.kb`** (Linux-owned `-501`).
     MBA91 `warm-bringup-mba91.sh` defaults to that path; leave installed
     `t2-keybag-load.sh` on `user.kb` for macOS-export flows elsewhere.
   - Need `/run/t2-touchid/keybag.env` with `T2_KEYBAG_SESSION=1`, a live handle
     from load, `T2_KEYBAG_SPECIAL=-501` — staged by warm-bringup `--bring-up`
     (or manual load) after Tim approves. `--check` only until then.
4. **Password source** — **Tim types on the local tty**, never via remote broker,
   never stored. `t2-aks-tool` prompts `macOS login password:` on `/dev/tty`.
5. **ACM helper** — `/dev/t2-acm` + `/usr/local/sbin/t2-aks-tool` (present) +
   `src/bridge-xpc-match-f1-authorized.py` + `t2_acm_device.with_authorized_context`.
6. **Harness gaps for count=1** (must fix before live F1):
   - `LIVE_F1_ENABLED = False` (must flip True for one window, restore False after).
   - Warm gate `count < 2` → refuse (lines ~209–211). For one surviving finger,
     change to **`count < 1`** (and docstring) for this canary only.
7. **Build** — no package install needed. Binaries already at
   `/usr/local/sbin/t2-aks-tool` and `src/t2-aks-tool`. Module already loaded;
   do **not** re-`insmod` while loaded (`warm-bringup --bring-up` refuses).
   If vermagic ever mismatches: rebuild `t2_sep_transport.ko` for
   `7.2.7-arch1-Watanare-T2-2-t2` only — long sudo → beep + `NEED SUDO` line.

## Safe dry-runs (cannot mutate bags)

These are OK before Tim approves a live match:

```bash
# 0) Beep + list bags / session (READ-ONLY). ONE recommended next command.
printf '\a'
echo 'NEED SUDO: read-only bag/session discovery for match canary prep'
sudo bash -lc 'ls -la /var/lib/t2-touchid/*.kb /var/lib/t2-touchid/biometric-port /run/t2-touchid/ 2>&1; /home/tim/Projects/t2-touchid-linux/tools/mba91-aks-macos-capture/warm-bringup-mba91.sh --check'

# 1) Harness refuse path (no ACM open — LIVE_F1_ENABLED False)
cd /home/tim/Projects/t2-touchid-linux
python3 src/bridge-xpc-match-f1-authorized.py \
  --host fe80::aede:48ff:fe33:4455 --port 49183 \
  --interface enp116s0f1u1 --macos-user-id 501
# expect: "live F1 probe is disabled in source; refusing"
```

Optional presence re-peek (already done in public summary; shapes only):

```bash
printf '\a'
echo 'NEED SUDO: private inventory key presence only'
sudo python3 -c 'import json; d=json.load(open("/var/lib/t2-touchid/inventory-journals/inventory-ro-501-20260930-222840.private.json")); print(sorted(d.keys())); c=d.get("catacomb",{}); print("catacomb.present", c.get("present"), "uuid_len", len(c.get("uuid") or ""), "hash_len", len(c.get("hash") or "")); print("per_user_n", len(d.get("per_user_identity_records") or []))'
```

**No safe dry-run of a live match exists** that still exercises opcode-4 without
opening a match window. Token-free and F1 both start match; both need unlocked
bags for a meaningful verdict. Do not invent a “dry match.”

## Staged live sequence (AFTER Tim approves — not this prep task)

### A. Stage + unlock keybags (local tty; mutates unlock state only)

Once `native-501.kb` is confirmed present (`warm-bringup --check`):

```bash
printf '\a'
echo 'NEED SUDO: load native-501.kb + stage keybag.env (no create, no user.kb)'
# MBA91 override (preferred on this track):
#   sudo .../warm-bringup-mba91.sh --bring-up
#   (only after reboot with module unloaded; refuses if already loaded)
# OR manual (session/handle must match what load printed — do not guess):
#   sudo t2-aks-tool load-keybag /var/lib/t2-touchid/native-501.kb 1
#   sudo t2-aks-tool set-system-keybag 1 <HANDLE> -501
#   then write /run/t2-touchid/keybag.env as warm-bringup does
# Do NOT: systemctl start t2-keybag-load.service (expects user.kb)
# Do NOT: copy/rename native-501.kb → user.kb

# Unlock both bags — Tim at the MBA91 keyboard/terminal:
sudo t2-aks-tool unlock-keybag 1 <NORMAL_HANDLE>   # from keybag.env
sudo t2-aks-tool unlock-keybag 1 -501
# Success: each prints status=0. Fail: non-zero / SEP status → STOP.
```

Password: **local tty only** (`macOS login password:`). Do not pipe passwords
over chat/SSH agent scripts unless Tim deliberately uses `*-stdin` on console.

### B. Optional positive control — token-free (K2 shape, no ACM)

Confirms one-finger sensor path before spending an ACM context:

```bash
printf '\a'
echo 'NEED SUDO: token-free match canary (unlocked bags; no ACM)'
cd /home/tim/Projects/t2-touchid-linux/src
sudo python3 bridge-xpc-probe.py \
  --host fe80::aede:48ff:fe33:4455 --port 49183 \
  --interface enp116s0f1u1 --macos-user-id 501 \
  --initialize --identity-list \
  --match-seconds 30 --stop-on-match-result
```

| Outcome | Meaning |
| --- | --- |
| `match_start` 0 → terminal `match_result` `matched: true` | one-finger + unlocked bags OK (K2 on count=1) |
| start 0, mute / no verdict | bags still locked or sensor/path issue — fix before F1 |
| start ≠ 0 | halt; journal status only |

Touch the **enrolled** finger when prompted / during the window. Cancel is
built into the probe path after stop-on-result.

### C. Password-bound F1 (one window) — needs source gates

1. Edit `src/bridge-xpc-match-f1-authorized.py` **temporarily**:
   - `LIVE_F1_ENABLED = True`
   - warm gate: `count < 1` (not `< 2`)
2. Run (Tim present for **two** password prompts: unlock already done; ACM bind
   prompts again via `verify-password-acm` on tty when the harness feeds the
   16 B form):

```bash
printf '\a'
echo 'NEED SUDO: ONE password-bound F1 match window (operator-approved)'
cd /home/tim/Projects/t2-touchid-linux/src
sudo python3 bridge-xpc-match-f1-authorized.py \
  --host fe80::aede:48ff:fe33:4455 --port 49183 \
  --interface enp116s0f1u1 --macos-user-id 501 \
  --match-seconds 30 \
  --confirm-live I_UNDERSTAND_THIS_STARTS_ONE_AUTHORIZED_F1_MATCH_WINDOW
# optional: --private-json /home/tim/Private/t2-touchid/f1-onefinger-YYYYMMDD.json
```

3. Immediately restore `LIVE_F1_ENABLED = False` and the count gate (or leave
   count≥1 if Tim wants one-finger F1 reusable — still keep LIVE False).

#### Success / fail (F1)

| Signal | Success | Fail / halt |
| --- | --- | --- |
| Policy | type-1 → after bind **SATISFIED** | bind fail / unsatisfied |
| Prelude | all status **0** | any prelude ≠ 0 → no match |
| `match_start_status` | **0** | ≠0/258 analysis; stop sprays |
| Events | terminal `match_result` (~3268 B) | mute after start 0 |
| `matched` | **true** (enrolled finger held) | false → placement/finger; one retry max with care |
| Cancel / post-`0x42` | cancel 0; identities **preserved** (still count 1) | identity change → **halt all live** |

## Blast radius / what NOT to do

- Match does **not** enroll and should not change `0x42` count; still cancel and
  re-check count=1 after.
- ACM create/externalize/bind/cleanup is **session-local**; mandatory cleanup is
  inside `with_authorized_context`.
- Unlock changes bag lock state until reboot/re-lock — expected.
- Never run enroll scripts, `bridge-xpc-enroll-native-501.py`, bag create,
  creation-ref `0x21`, or a second `load-keybag` that invents a new bag.
- Do not enable F1 and leave LIVE True in tree.

## Password: local vs broker

| Step | Who types password | Mechanism |
| --- | --- | --- |
| Keybag unlock | **Tim, local tty on MBA91** | `t2-aks-tool unlock-keybag` → `/dev/tty` |
| ACM bind (F1) | **Tim, local tty on MBA91** | harness pipes 16 B form to stdin of `verify-password-acm`; tool then prompts on tty |
| Remote agent / chat | **never** | no broker password capture in this canary |

K2 already says a production broker can be password-free at match time if bags
stay unlocked; this canary still exercises the ACM path for regression against
the one-finger macOS baseline.

## Outcome (2026-10-01)

The prep check, the one load of `native-501.kb`, the bind onto `-501`,
and `unlock-keybag 1 1` are done. Unlock returned SEP `-5`. The plan's
own rule was non-zero unlock means stop, so the token-free control and
F1 were not started. The open approved work is the activation-sequence
paper named in `NEXT_STEPS.md`. Another password attempt, another load,
and a copy to `user.kb` are repeats of answered shots.
