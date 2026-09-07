# Mesa / BridgeXPC sequence mining (MBA91)

Derived from private cold-boot capture `2489129E-…` (2026-09-06 MT).
No templates, key material, or raw log bodies — opcode/ordering only.

## How we figure out the sequences

1. **Mine os_log** — `biometrickitd` `Daemon-Mesa` + `BridgeTransport` + `BridgeXPC` from the LaunchDaemon capture.
2. **Tag `performCommand` opcodes** — first numeric arg is the Mesa command id; pair with TX/RX byte sizes.
3. **Phase-split** — cold boot / enroll UI / unlock+catacomb save.
4. **Compare to Linux** — mailbox EP7 AKS was mute; macOS biometric path is BridgeXPC↔Mesa. Ask whether any opcode/ordering maps to AKS EP7 or only to a different endpoint/service.
5. **Next instruments** (if logs insufficient) — userspace BridgeXPC dump, `log show` for dropped lines, dual-boot A/B after exporting catacomb/keybags.

## Opcode histogram (full session)

| opcode | count |
| --- | ---: |
| `84` | 38 |
| `82` | 21 |
| `12` | 15 |
| `39` | 13 |
| `14` | 12 |
| `44` | 8 |
| `61` | 8 |
| `62` | 8 |
| `63` | 8 |
| `74` | 8 |
| `8` | 7 |
| `48` | 5 |
| `58` | 5 |
| `46` | 5 |
| `76` | 4 |
| `56` | 4 |
| `60` | 3 |
| `80` | 3 |
| `26` | 1 |
| `65` | 1 |
| `3` | 1 |
| `17` | 1 |
| `15` | 1 |
| `38` | 1 |
| `4` | 1 |
| `40` | 1 |

## Phase snapshots

### boot_pre (109 tagged events)

| opcode | count |
| --- | ---: |
| `44` | 8 |
| `39` | 5 |
| `82` | 5 |
| `84` | 4 |
| `76` | 2 |
| `26` | 1 |
| `12` | 1 |

```
2026-09-06 21:00:58.246  MESA_CMD opcode=26 ver=1 inValue=0
2026-09-06 21:00:59.948  MESA_CMD opcode=39 ver=1 inValue=0
2026-09-06 21:01:02.560  MESA_CMD opcode=44 ver=1 inValue=0
2026-09-06 21:01:03.998  MESA_CMD opcode=82 ver=1 inValue=0
2026-09-06 21:01:04.004  MESA_CMD opcode=84 ver=1 inValue=0
2026-09-06 21:01:18.044  MESA_CMD opcode=44 ver=1 inValue=0
2026-09-06 21:01:18.059  MESA_CMD opcode=44 ver=1 inValue=0
2026-09-06 21:01:18.089  MESA_CMD opcode=44 ver=1 inValue=0
2026-09-06 21:01:18.281  MESA_CMD opcode=44 ver=1 inValue=0
2026-09-06 21:01:44.651  MESA_CMD opcode=76 ver=1 inValue=0
2026-09-06 21:01:44.658  MESA_CMD opcode=82 ver=1 inValue=0
2026-09-06 21:01:44.664  MESA_CMD opcode=84 ver=1 inValue=0
2026-09-06 21:03:03.153  MESA_CMD opcode=39 ver=1 inValue=0
2026-09-06 21:03:31.699  MESA_CMD opcode=39 ver=1 inValue=0
2026-09-06 21:04:18.150  MESA_CMD opcode=44 ver=1 inValue=0
```

Notable tags:
```
2026-09-06 21:01:03.998  GET_BIO_DEVICE_LIST
2026-09-06 21:01:44.658  GET_BIO_DEVICE_LIST
2026-09-06 21:08:35.882  GET_BIO_DEVICE_LIST
2026-09-06 21:08:36.087  GET_BIO_DEVICE_LIST
2026-09-06 21:08:36.306  GET_BIO_DEVICE_LIST
```

### enroll (1622 tagged events)

| opcode | count |
| --- | ---: |
| `84` | 32 |
| `82` | 16 |
| `12` | 13 |
| `14` | 12 |
| `8` | 7 |
| `74` | 7 |
| `39` | 7 |
| `61` | 6 |
| `62` | 6 |
| `63` | 6 |
| `58` | 4 |
| `48` | 3 |
| `56` | 3 |
| `46` | 3 |
| `60` | 2 |
| `80` | 2 |
| `76` | 2 |
| `65` | 1 |
| `3` | 1 |
| `17` | 1 |
| `15` | 1 |
| `38` | 1 |
| `4` | 1 |
| `40` | 1 |

```
2026-09-06 21:10:07.810  MESA_CMD opcode=82 ver=1 inValue=0
2026-09-06 21:10:07.817  MESA_CMD opcode=84 ver=1 inValue=0
2026-09-06 21:10:08.037  MESA_CMD opcode=82 ver=1 inValue=0
2026-09-06 21:10:08.044  MESA_CMD opcode=84 ver=1 inValue=0
2026-09-06 21:10:08.056  MESA_CMD opcode=65 ver=1 inValue=0
2026-09-06 21:10:17.322  MESA_CMD opcode=82 ver=1 inValue=0
2026-09-06 21:10:17.328  MESA_CMD opcode=84 ver=1 inValue=0
2026-09-06 21:10:17.335  MESA_CMD opcode=12 ver=1 inValue=0
2026-09-06 21:10:17.347  MESA_CMD opcode=12 ver=1 inValue=0
2026-09-06 21:10:17.400  MESA_CMD opcode=82 ver=1 inValue=0
2026-09-06 21:10:17.405  MESA_CMD opcode=84 ver=1 inValue=0
2026-09-06 21:10:17.409  MESA_CMD opcode=12 ver=1 inValue=0
2026-09-06 21:10:17.446  MESA_CMD opcode=82 ver=1 inValue=0
2026-09-06 21:10:17.451  MESA_CMD opcode=84 ver=1 inValue=0
2026-09-06 21:10:17.457  MESA_CMD opcode=12 ver=1 inValue=0
```

Notable tags:
```
2026-09-06 21:10:07.809  GET_BIO_DEVICE_LIST
2026-09-06 21:10:08.036  GET_BIO_DEVICE_LIST
2026-09-06 21:10:17.320  ENROLL_UI
2026-09-06 21:10:17.321  GET_BIO_DEVICE_LIST
2026-09-06 21:10:17.346  ENROLL_UI
2026-09-06 21:10:17.400  GET_BIO_DEVICE_LIST
2026-09-06 21:10:17.441  ENROLL_UI
2026-09-06 21:10:17.441  ENROLL_UI
2026-09-06 21:10:17.441  ENROLL_UI
2026-09-06 21:10:17.443  ENROLL_UI
2026-09-06 21:10:17.445  ENROLL_UI
2026-09-06 21:10:17.445  ENROLL_UI
2026-09-06 21:10:17.445  ENROLL_UI
2026-09-06 21:10:17.445  ENROLL_UI
2026-09-06 21:10:17.445  ENROLL_UI
2026-09-06 21:10:17.446  GET_BIO_DEVICE_LIST
2026-09-06 21:10:17.462  ENROLL_UI
2026-09-06 21:10:17.462  ENROLL_UI
2026-09-06 21:10:17.462  ENROLL_UI
2026-09-06 21:10:17.469  ENROLL_UI
```

### idle (0 tagged events)

_No performCommand opcodes in this slice._
### unlock (292 tagged events)

| opcode | count |
| --- | ---: |
| `46` | 2 |
| `48` | 2 |
| `84` | 2 |
| `61` | 2 |
| `62` | 2 |
| `63` | 2 |
| `39` | 1 |
| `12` | 1 |
| `74` | 1 |
| `60` | 1 |
| `80` | 1 |
| `56` | 1 |
| `58` | 1 |

```
2026-09-06 21:14:11.596  MESA_CMD opcode=46 ver=1 inValue=0
2026-09-06 21:14:11.608  MESA_CMD opcode=46 ver=1 inValue=0
2026-09-06 21:14:14.303  MESA_CMD opcode=48 ver=1 inValue=0
2026-09-06 21:14:14.342  MESA_CMD opcode=48 ver=1 inValue=0
2026-09-06 21:14:14.360  MESA_CMD opcode=84 ver=1 inValue=0
2026-09-06 21:14:14.373  MESA_CMD opcode=39 ver=1 inValue=0
2026-09-06 21:14:14.390  MESA_CMD opcode=84 ver=1 inValue=0
2026-09-06 21:14:14.410  MESA_CMD opcode=12 ver=1 inValue=0
2026-09-06 21:14:14.411  MESA_CMD opcode=74 ver=1 inValue=0
2026-09-06 21:14:29.940  MESA_CMD opcode=60 ver=1 inValue=0
2026-09-06 21:14:29.948  MESA_CMD opcode=80 ver=1 inValue=0
2026-09-06 21:14:29.954  MESA_CMD opcode=61 ver=2 inValue=0
2026-09-06 21:14:29.965  MESA_CMD opcode=62 ver=2 inValue=0
2026-09-06 21:14:30.010  MESA_CMD opcode=63 ver=2 inValue=0
2026-09-06 21:14:30.015  MESA_CMD opcode=56 ver=1 inValue=0
```

Notable tags:
```
2026-09-06 21:14:11.238  ENABLED_FOR_UNLOCK 1 ([0: Success])
2026-09-06 21:14:14.317  ENABLED_FOR_UNLOCK 1 ([0: Success])
2026-09-06 21:14:14.353  ENABLED_FOR_UNLOCK 1 ([0: Success])
2026-09-06 21:14:29.940  SAVE_CATACOMB
2026-09-06 21:14:30.010  CONFIRM_SAVE_CATACOMB
2026-09-06 21:14:30.015  CONFIRM_SAVE_CATACOMB_DONE
2026-09-06 21:14:30.035  CATACOMB_FILE master.cat
2026-09-06 21:14:30.096  CONFIRM_SAVE_CATACOMB
2026-09-06 21:14:30.519  CONFIRM_SAVE_CATACOMB_DONE
2026-09-06 21:14:30.519  SAVE_CATACOMB
2026-09-06 21:14:30.519  SAVE_CATACOMB
```

## Working hypothesis

- Enroll/unlock are **BridgeXPC sessions** driven by `biometrickitd`, not the Linux `t2_sep` mailbox AKS capability frame.
- Catacomb save (`master.cat`, confirm opcode path) is the durable biometric store we already knew Linux needs exports for.
- Linux EP7 mute may mean: wrong service endpoint, missing Bridge/xART bring-up before AKS, or AKS never exposed the same way on this bridgeOS — Mesa opcodes are clues for *what* the SEP biometric stack does, not a drop-in EP7 replay.

## Immediate next steps

1. Keep this opcode table; annotate unknown opcodes against any public BiometricKit/Mesa RE notes / bent docs.
2. On Linux, check whether BridgeXPC/IPv6 interface to bridgeOS can observe similar messages (userspace) vs mailbox-only.
3. Export keybags/catacomb when returning to Omarchy; retest match stack separately from EP7 capability.
4. Optional: `log show --last boot` offline to recover lines dropped by live `log stream`.
