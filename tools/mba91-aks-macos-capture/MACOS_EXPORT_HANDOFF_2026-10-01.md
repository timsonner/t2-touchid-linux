# macOS export handoff — MBA91 (2026-10-01)

Give this file to the agent after the reboot into macOS. The Linux
side is `research/mba91-aks-ep7` at or after `25a2a6b` on
`https://github.com/timsonner/t2-touchid-linux`. Track A applies: this
is Tim's own MacBookAir9,1, and the only fingerprint is his.

## Goal

Produce two private archives and stop:

- `t2-keybags.tar.gz`
- `t2-touchid-catacomb.tar.gz`

Omarchy already has the transport, `fprintd`, and one enrolled finger
(macOS uid 501, right index). `t2-keybag-load.service` skipped this
boot because `/var/lib/t2-touchid/user.kb` is absent. The only bag
file on Linux is `/var/lib/t2-touchid/native-501.kb`. Password unlock
of that file returned SEP `-5` on 2026-10-01. A locked bag makes the
matcher mute, so that file cannot become `user.kb`.

The archives stay on the macOS volume. Do not mount the Linux volume.
Do not commit the archives. Do not paste passwords, keybag bytes,
Catacomb bytes, or UUIDs into chat.

## Already true — do not redo

- One finger is already enrolled. Do not open Touch ID settings. Do
  not add, remove, or rename a finger.
- Do not create a keybag, run an AKS tool, or copy any Linux `.kb`.
- Do not run `uninstall.sh` from the old capture kit.
- Do not follow the destination-path example in `CHECKLIST.md` or
  `BACKUP_AND_TEARDOWN.md`. Those copies look for
  `/private/tmp/t2-keybags.tar.gz`. The current scripts do not write
  there, and they do not take an output-path argument.

## Where the scripts write

Each script writes its archive into the directory that contains the
script. Copy the scripts into the output directory, then run them
from there.

```bash
mkdir -p "$HOME/Private/t2-touchid-export-20261001"
chmod 700 "$HOME/Private/t2-touchid-export-20261001"
cd "$HOME/Private/t2-touchid-export-20261001"
curl -fsSL -o macos-export-keybags.sh \
  https://raw.githubusercontent.com/timsonner/t2-touchid-linux/research/mba91-aks-ep7/tools/macos/macos-export-keybags.sh
curl -fsSL -o macos-export-touchid-catacomb.sh \
  https://raw.githubusercontent.com/timsonner/t2-touchid-linux/research/mba91-aks-ep7/tools/macos/macos-export-touchid-catacomb.sh
chmod 700 macos-export-keybags.sh macos-export-touchid-catacomb.sh
```

A local checkout of that branch is fine too. Run the copies that sit
in the private directory, so the archives land there.

## 1. Keybags

```bash
./macos-export-keybags.sh
```

macOS will ask for the administrator password in the normal macOS
prompt. Type it there. Success is a line `Created:` followed by
`t2-keybags.tar.gz`, mode `600`, and a non-zero size.

If the script prints `no keybag candidates were copied`, stop. Do not
invent a bag.

The script does not print the candidate count. Read it from the
archive and report only the count plus the original paths whose
basename is `user.kb`:

```bash
ls -l t2-keybags.tar.gz
tar -xOf t2-keybags.tar.gz state/path-map.txt \
  | awk -F'\t' 'NF { n++; base=$2; sub(/.*\//, "", base); if (base=="user.kb") print } END { print "candidates=" n+0 }'
```

That awk prints the matching `path-map` lines and a count. Do not
print keybag contents. `tar -tzf t2-keybags.tar.gz` listing member
names is enough besides the command above.

## 2. Catacomb

Pass `--no-reboot`. The default freezes `biometrickitd` and runs
`shutdown -r now`. Tim chooses the reboot back to Omarchy himself.

```bash
./macos-export-touchid-catacomb.sh --no-reboot
```

Success is `Created: .../t2-touchid-catacomb.tar.gz`, mode `600`.
Then confirm the archive actually holds an enrolled-user store:

```bash
tar -tzf t2-touchid-catacomb.tar.gz | awk -F/ '{print $NF}' | sort -u
```

Report the basename list and `ls -l` of the archive. An enrolled
store contains `TemplateList.cat` or a `user_*.cat` member. If neither
name is present, stop. The script's "enroll a fingerprint" message is
not a task. The finger is already enrolled; a missing store is a
result to bring back, not a reason to enroll again.

## Done

Leave both archives in `$HOME/Private/t2-touchid-export-20261001`,
mode `600`, owned by the console user. Tell Tim the two paths, the
two sizes, the candidate count, and whether `user.kb` and
`user_*.cat` or `TemplateList.cat` were present.

Then stop. Tim reboots and selects Omarchy. The Linux agent continues
from the return section below.

## Return section (Linux, after Tim is back)

Do not start this section on macOS.

1. Confirm both archives are still the files named above. Do not copy
   `native-501.kb` onto `user.kb`.
2. From the keybag archive, the macOS `user.kb` candidate is the file
   whose basename is `user.kb`. If several match, stop and show only
   their archived pathnames and sizes. Install the chosen file as
   `/var/lib/t2-touchid/user.kb`, root:root, mode `0600`.
3. Provision the local Catacomb:

   ```bash
   sudo t2-touchid-provision-catacomb /path/to/t2-touchid-catacomb.tar.gz
   ```

4. `t2-keybag-load.service` loads that `user.kb` on the next start.
   The module is already loaded; do not unload `t2_sep_transport` or
   `applesmc`.
5. Unlock both handles with the macOS login password, on the Mac's
   own keyboard (`t2-keybag-unlock` or the two `unlock-keybag` calls
   recorded in `keybag.env`). Both results must be `status=0`. SEP
   `-5` or any other status means stop. Do not retry, do not swap in
   `native-501.kb`, and do not enroll.
6. Only after both unlocks are `status=0`: `fprintd-verify -f any tim`
   must return `verify-match` for the enrolled finger. PAM
   (`tools/install-pam.sh`) comes after that control passes. Nothing
   in `/etc/pam.d` currently calls the fingerprint stack.
