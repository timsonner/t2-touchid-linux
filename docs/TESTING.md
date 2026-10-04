# Testing

## Unit tests (no hardware)

CI runs this on Python 3.12 and 3.14 for every pull request:

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
T2_TOUCHID_USER=test .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m py_compile src/*.py tests/*.py
tools/privacy-check.sh
enrollment_research/scripts/check-public-tree.sh
shellcheck install.sh uninstall.sh src/*.sh tools/*.sh tools/macos/*.sh
make -C src t2-aks-tool t2-pam-fingerprint-prompt
```

`tests/` is hardware-free. It covers protocol state machines, journals,
Catacomb codecs, fprintd claim/runtime, PAM assets, and fail-closed
malformed events. Enrollment protocol tests include status 80
(`operation-finished`), 60/61 (`operation-state-changed`), and the
other recovered generic ordinals.

Workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

## Live hardware (MBA91)

These talk to SEP. One numbered mutation at a time. Do not unload
`t2_sep_transport` or `applesmc`. Do not run `warm-bringup-mba91.sh`
while `user.kb` is the loaded bag.

**Match (no enroll)**

1. `t2-keybag-load.service` loaded `user.kb`.
2. Unlock both handles (`t2-keybag-unlock` or the PAM first-sudo path).
3. From the desktop session, not a root shell without a seat:

```sh
fprintd-verify -f any "$USER"
```

Expect `verify-match` for either enrolled finger. `fprintd-list` may
show only `right-index-finger`; that is a compatibility alias.

**Enroll**

Requires a hashed Catacomb backup, password-fallback acknowledgement,
and a visible terminal. After start, reboot and run
`t2-touchid-enroll verify-post-reboot` before another mutation.

If start freezes with `ENROLL_OUTCOME_UNKNOWN`, run
`t2-touchid-enroll recover-outcome`. If host and SEP identity counts
diverge, `recover-observed` persists the SEP identity into the local
store. Do not start a second enroll on an unfinished journal.

**Do not run as a test**

- `bridge-xpc-enroll-native-501.py`
- `0x40`, sensor reset, `no_catacomb`, `0x48`
- Copying `native-501.kb` onto `user.kb`
- `t2-inventory-ro-501.sh` into the git tree (it writes DMA into logs)

## Privacy checks

```sh
tools/privacy-check.sh
enrollment_research/scripts/check-public-tree.sh
```

These must pass before a pull request. They reject tracked keybags,
Catacomb files, pcaps, and some identifier patterns.
