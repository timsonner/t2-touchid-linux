#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""DRAFT (staged, not yet run): C4b ACM-verify against the native bag.

Status: design only. LIVE_C4B_ENABLED defaults False; even enabled,
this refuses unless --confirm-live matches. Single question: does
fresh-bag handle (default: resolve live, never macOS handle 1)
participate in ACM password verification at all?

Body: fresh ACM tracking context for uid 501 -> externalize ->
verify-password-acm <session> <handle> with the 16 B form on stdin
and the operator-typed creation password at the tool prompt ->
report policy-1007 satisfied/unsatisfied + requirement shape.
Mandatory context cleanup. No bind/unlock/enroll traffic, no state
change of any kind (read-only decision procedure).

SATISFIED means the native bag is functionally usable for
enroll-auth (C5 viable) and the unlock-keybag / verify-only
refusals are side-gates. Anything else keeps C4 parked with a
precise vocabulary word.
"""

from __future__ import annotations

import argparse
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

LIVE_C4B_ENABLED = False
CONFIRM = "I_UNDERSTAND_THIS_TESTS_ACM_VERIFY_ON_A_TEST_BAG"
AKS_TOOL = Path("/usr/local/sbin/t2-aks-tool")


def fail(message: str) -> int:
    print(f"verify-c4b: {message}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=int, default=1)
    parser.add_argument("--handle", required=True, type=int)
    parser.add_argument("--macos-user-id", type=int, default=501)
    parser.add_argument("--confirm-live", default="")
    args = parser.parse_args()

    if not LIVE_C4B_ENABLED or args.confirm_live != CONFIRM:
        return fail("live C4b probe is disabled in source; refusing")
    if args.handle == 1:
        return fail("handle 1 is the macOS bag; refusing")

    def bind_password(context: bytes) -> None:
        print("Type the creation password at the prompt.", flush=True)
        completed = subprocess.run(
            [str(AKS_TOOL), "verify-password-acm",
             str(args.session), str(args.handle)],
            input=context, check=False)
        if completed.returncode:
            raise ACMDeviceError("AKS password binding failed")

    try:
        with ACMDevice() as device:
            initial, final, _ = with_authorized_context(
                device, args.macos_user_id, bind_password,
                lambda _form: "c4b-check", tracking=True)
    except (OSError, ValueError, ACMDeviceError, RuntimeError) as error:
        return fail(f"{error}")
    print(f"c4b: preflight_type={initial.requirement_type} "
          f"satisfied={final.satisfied}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
