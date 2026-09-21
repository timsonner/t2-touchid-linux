#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""DRAFT (staged, not yet run): C4 native-bag password/bind probe.

Status: design only. LIVE_C4_ENABLED defaults False; even enabled,
this refuses unless ALL of the following hold:

- warm SEP with lab + ACM nodes live and an EP7 keybag session;
- the C3 test file present at its exact path (reloaded fresh —
  never a hardcoded live handle);
- explicit --confirm-live, with intent journaled pre-dispatch to a
  REQUIRED operator-private path.

Body: reload the C3 test file (additive new handle H) -> bag-UUID
present (non-zero 16 B; values never logged) -> set-system-keybag
bind H to scratch alias -502 FIRST (fresh bags need activation
before unlock; NEVER -501 — macOS binding untouched by
construction) -> operator types the creation password at the
unlock prompt -> fresh ACM tracking context + verify-password-acm
bind with the same password (second prompt) -> policy-1007
SATISFIED required -> outcome journal.

The two password prompts take a NEW Linux-chosen test password the
operator invents on the spot; it is never stored, never logged, and
lives only in terminal memory plus SEP-side state. Nothing
macOS-derived is read or written anywhere in this window.

Outcome closes one of: password-establishes-and-verifies (C5
unblocked), unlock-refuses (new vocabulary to mine), bind-refuses
(alias layer question). Any transport error halts with no replay.
Live handles evaporate on reboot; the test file persists until the
operator deletes it.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

LOCAL_SOURCE = Path(__file__).resolve().parent
if str(LOCAL_SOURCE) not in sys.path:
    sys.path.insert(0, str(LOCAL_SOURCE))

from t2_acm_device import (  # noqa: E402
    ACMDevice,
    ACMDeviceError,
    with_authorized_context,
)

LIVE_C4_ENABLED = False
CONFIRM = "I_UNDERSTAND_THIS_BINDS_ONE_TEST_KEYBAG"
AKS_TOOL = Path("/usr/local/sbin/t2-aks-tool")
LAB_DEVICE = Path("/dev/t2-sep-lab")
ACM_DEVICE_NODE = Path("/dev/t2-acm")
SCRATCH_ALIAS = -502
TEST_KEYBAG = Path("/var/lib/t2-touchid/native-c3-test.kb")
PRIVATE_ROOT = Path("/home/tim/Private")


def fail(message: str) -> int:
    print(f"bind-c4: {message}", file=sys.stderr)
    return 1


def run_tool(*argv: str) -> tuple[int, str]:
    completed = subprocess.run(
        [str(AKS_TOOL), *argv], capture_output=True, text=True, check=False)
    return completed.returncode, completed.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=int, default=1)
    parser.add_argument("--confirm-live", default="")
    parser.add_argument("--private-json", required=True)
    args = parser.parse_args()

    if not LIVE_C4_ENABLED or args.confirm_live != CONFIRM:
        return fail("live C4 probe is disabled in source; refusing")
    private_path = Path(args.private_json)
    if PRIVATE_ROOT not in private_path.resolve().parents:
        return fail("journal must stay under operator-private storage")
    if not LAB_DEVICE.exists() or not ACM_DEVICE_NODE.exists():
        return fail("lab/ACM devices absent; load the module first")
    if not TEST_KEYBAG.exists():
        return fail("C3 test keybag file absent; run C3 first")

    journal: dict[str, object] = {
        "stage": "c4",
        "scratch_alias": SCRATCH_ALIAS,
        "reload_handle": None,
        "pre_uuid_observed": False,
        "unlock_status": None,
        "policy_satisfied": False,
        "bind_status": None,
        "outcome": "unknown",
    }
    try:
        code, out = run_tool("load-keybag", str(TEST_KEYBAG),
                             str(args.session))
        if code != 0 or "status=0" not in out:
            raise RuntimeError(f"reload failed: {out[:120]}")
        handle = int(out.split("handle=")[1].split()[0])
        journal["reload_handle"] = handle
        tmp = private_path.parent / (private_path.stem + ".uuid-pre.bin")
        code, _ = run_tool("copy-keybag-uuid", str(args.session),
                           str(handle), str(tmp))
        try:
            raw = tmp.read_bytes() if code == 0 else b""
            journal["pre_uuid_observed"] = len(raw) == 16 and any(raw)
        finally:
            tmp.unlink(missing_ok=True)
        if not journal["pre_uuid_observed"]:
            raise RuntimeError("reloaded bag has no UUID; refusing")
        journal["intent"] = {"reload_handle": handle}
        private_path.write_text(json.dumps(journal, indent=2))

        code, out = run_tool("set-system-keybag", str(args.session),
                             str(handle), str(SCRATCH_ALIAS))
        journal["bind_status"] = out.split()[0] if out else f"rc={code}"
        if code != 0 or "status=0" not in out:
            journal["outcome"] = "bind-refused-clean"
            private_path.write_text(json.dumps(journal, indent=2))
            print(json.dumps(journal, indent=2, sort_keys=True))
            return 0
        print("Type the creation password at each prompt.",
              flush=True)
        code, out = run_tool("unlock-keybag", str(args.session),
                             str(handle))
        journal["unlock_status"] = out.split()[0] if out else f"rc={code}"
        if code != 0 or "status=0" not in out:
            journal["outcome"] = "unlock-refused-clean"
            private_path.write_text(json.dumps(journal, indent=2))
            print(json.dumps(journal, indent=2, sort_keys=True))
            return 0

        def bind_password(context: bytes) -> None:
            # Proven F1/S4 pattern: the tool prompts on the terminal
            # and reads the password itself; only the 16 B context
            # crosses this process boundary. The operator types the
            # SAME new password established at unlock above.
            print("Type the SAME new password for the ACM bind.",
                  flush=True)
            completed = subprocess.run(
                [str(AKS_TOOL), "verify-password-acm",
                 str(args.session), str(handle)],
                input=context, check=False)
            if completed.returncode:
                raise ACMDeviceError("AKS password binding failed")

        with ACMDevice() as device:
            initial, final, _ = with_authorized_context(
                device, 501, bind_password, lambda _form: "bound",
                tracking=True)
            journal["policy_preflight_type"] = initial.requirement_type
            journal["policy_satisfied"] = final.satisfied
        if not journal["policy_satisfied"]:
            raise RuntimeError("policy-1007 unsatisfied on native bag")
        journal["outcome"] = "bound-unlocked-verified"
    except (OSError, ValueError, ACMDeviceError, RuntimeError) as error:
        journal["outcome"] = f"halt: {type(error).__name__}"
        try:
            private_path.write_text(json.dumps(journal, indent=2))
        except OSError:
            pass
        print(json.dumps(journal, indent=2, sort_keys=True))
        return fail(f"{error}")
    private_path.write_text(json.dumps(journal, indent=2))
    print(json.dumps(journal, indent=2, sort_keys=True))
    if journal["outcome"] not in ("bound-unlocked-verified",
                                  "unlock-refused-clean",
                                  "bind-refused-clean"):
        return fail("C4 ambiguous; halt and review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
