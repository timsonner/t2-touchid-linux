#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""DRAFT (staged, not yet run): E1 enroll-start probe, zero-group 68B.

Status: design only. LIVE_E1_ENABLED defaults False; even enabled,
this refuses unless ALL of the following hold:

- warm SEP: BridgeXPC 0x42 holds 1..4 identities for the configured
  UID (room for exactly one more; SKS informational only);
- full-inventory repeat_equal true on this boot before the window
  (operator verifies separately; script re-checks 0x42 count
  in-session);
- a fresh ACM tracking context creates, shows the type-1 passcode
  requirement, binds the operator password via t2-aks-tool, and reaches
  policy-1007 SATISFIED — all inside with_authorized_context, with
  mandatory context cleanup before return;
- explicit --confirm-live.

Rationale: the authorized 0x03 v2 68B dispatch refused 22 with our
group-u32=1 bytes at [48:52]; the sibling t2touch project's working
v2 construction (`SensitiveEnrollmentRequest`) packs those 4 bytes
zero. Header, form placement, version, session prep are otherwise
identical. E1 isolates exactly those 4 bytes.

Body (start-only, NO finger dance): full session prep (5 read-only
steps, abort on deviation) -> single 0x03 v2 dispatch with the
zero-group 68B -> whatever the start status, cancel immediately ->
post-0x42 must still equal the pre count. A 0 that opens means the
track reopens (E4 dance staged separately, never combined here); 22
or -3 closes the group theory (graduate E2). Any other start status,
any service event, or any identity-count change halts all live work.

Deliberate limits: single dispatch, cancel always, no 0x0e traffic,
no finger contact needed (refusal happens at dispatch; a 0-open is
cancelled before any enroll continues). No enroll completion, no
load / reset / delete / EP7 traffic beyond the keybag-session
prerequisites. Password handling: operator terminal only via
t2-aks-tool, never stored, never logged.

Prerequisites (operator, in order): minimal-bring-up module load on warm
SEP (pinned set only), re-established EP7 keybag session
(/run/t2-touchid/keybag.env), operator password at the bind prompt.
"""

from __future__ import annotations

import argparse
import importlib.util as _importlib_util
import json
import socket
import struct
import subprocess
import sys
import time
from pathlib import Path

LOCAL_SOURCE = Path(__file__).resolve().parent
if str(LOCAL_SOURCE) not in sys.path:
    sys.path.insert(0, str(LOCAL_SOURCE))

from t2_bridge_wire import (  # noqa: E402
    biometric_command,
)
from t2_acm_device import (  # noqa: E402
    ACMDevice,
    ACMDeviceError,
    with_authorized_context,
)

LIVE_E1_ENABLED = False
CONFIRM = "I_UNDERSTAND_THIS_STARTS_ONE_E1_ENROLL_START_WINDOW"
AKS_TOOL = Path("/usr/local/sbin/t2-aks-tool")
ENROLL_OPCODE = 0x03
ENROLL_VERSION = 2
PRIVATE_ROOT = Path("/home/tim/Private")


def _load_helpers():
    path = LOCAL_SOURCE / "bridge-xpc-authorized-enroll.py"
    spec = _importlib_util.spec_from_file_location(
        "bridge_xpc_enroll_e1_helpers", path)
    assert spec and spec.loader
    module = _importlib_util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fail(message: str) -> int:
    print(f"enroll-e1: {message}", file=sys.stderr)
    return 1


def e1_consumer_factory(host, port, interface, user_id, before_count):
    def consume(external_form: bytes) -> dict[str, object]:
        if not isinstance(external_form, bytes) or len(external_form) != 16:
            raise RuntimeError("authorized external form is invalid")
        # t2touch-exact v2 layout: IIII flags/uid/0/16 + 16-byte ACM
        # external form + 36 zero bytes (all-zero device group).
        # The ONLY difference from our refused construction is bytes
        # [48:52] (zero here, u32=1 there).
        payload = (struct.pack("<IIII", 0, user_id, 0, 16)
                   + external_form + bytes(36))
        assert len(payload) == 68
        helpers = _load_helpers()
        summary: dict[str, object] = {
            "opcode": ENROLL_OPCODE,
            "stage": "e1",
            "framing": "zero-group-68B",
            "warm_gate": False,
            "session_prep": [],
            "dispatch_status": None,
            "cancel_status": None,
            "identities_before": before_count,
            "identities_after": None,
            "identities_preserved": False,
        }
        sock = helpers.open_bridge(host, port, interface)
        try:
            identities, sks = helpers.warm_gate(sock, user_id)
            count = len(identities) // 20
            summary["warm_gate_detail"] = {
                "identity_count": count, "sks": sks}
            if count != before_count:
                raise RuntimeError(
                    "warm gate drifted since pre-verification; refusing")
            summary["warm_gate"] = True
            for opcode, version, value, data, cap, label in [
                (0x52, 1, 0, b"", 264, "device-list"),
                (0x53, 1, 0, b"", 1, "sensor-readiness"),
                (0x43, 2, 0, b"", 64, "system-protected-config"),
                (0x4C, 1, 0, b"", 1, "xart-available"),
                (0x30, 1, 0, struct.pack("<I", user_id), 1,
                 "enabled-unlock"),
            ]:
                reply, _ = biometric_command(
                    sock, opcode, version=version, value=value,
                    data=data, output_capacity=cap)
                status = reply[0] if (
                    isinstance(reply, list) and reply) else None
                summary["session_prep"].append(
                    {"label": label, "status": status})
                if status != 0:
                    raise RuntimeError(
                        f"session prep deviated at {label}; "
                        "no enroll attempted")
            start_reply, _ = biometric_command(
                sock, ENROLL_OPCODE, version=ENROLL_VERSION, value=0,
                data=payload, output_capacity=0)
            start_status = (start_reply[0] if (
                isinstance(start_reply, list) and start_reply) else None)
            summary["dispatch_status"] = start_status
        finally:
            try:
                cancel_reply, _ = biometric_command(sock, 0x0C)
                summary["cancel_status"] = (cancel_reply[0] if isinstance(
                    cancel_reply, list) and cancel_reply else None)
            except Exception:
                summary["cancel_status"] = -1
            try:
                post_reply, _ = biometric_command(
                    sock, 0x42, data=struct.pack("<I", user_id),
                    output_capacity=20 * 10)
                post = (post_reply[1] if isinstance(post_reply, list)
                        and len(post_reply) == 2
                        and isinstance(post_reply[1], bytes) else None)
                summary["identities_after"] = (
                    None if post is None else len(post) // 20)
                summary["identities_preserved"] = (
                    summary["identities_after"] == before_count)
            except Exception:
                summary["identities_preserved"] = False
            sock.close()
        return summary
    return consume


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--interface", required=True)
    parser.add_argument("--macos-user-id", required=True, type=int)
    parser.add_argument("--confirm-live", default="")
    parser.add_argument("--private-json", default="")
    args = parser.parse_args()

    if not LIVE_E1_ENABLED or args.confirm_live != CONFIRM:
        return fail("live E1 probe is disabled in source; refusing")
    if not 0 <= args.macos_user_id <= 0xFFFFFFFF:
        return fail("macOS user ID is outside uint32 range")
    private_path = None
    if args.private_json:
        private_path = Path(args.private_json)
        if PRIVATE_ROOT not in private_path.resolve().parents:
            return fail("raw JSON must stay under operator-private storage")

    helpers = _load_helpers()
    try:
        user_id, special, mapped_uid = helpers.configuration()
        if args.macos_user_id != user_id:
            return fail("requested UID does not match /etc/t2-touchid.conf")
        if not helpers.caller_is_mapped(mapped_uid):
            return fail(
                "caller is not the mapped Linux user via sudo/pkexec")
        session, handle = helpers.keybag_runtime(special)
    except helpers.EnrollRunnerError as error:
        return fail(f"precondition: {error}")

    before_count = 2

    def bind_password(context: bytes) -> None:
        completed = subprocess.run(
            [str(AKS_TOOL), "verify-password-acm",
             str(session), str(handle)],
            input=context, check=False)
        if completed.returncode:
            raise ACMDeviceError("AKS password binding failed")

    try:
        with ACMDevice() as device:
            initial, final, e1_summary = with_authorized_context(
                device, user_id, bind_password,
                e1_consumer_factory(
                    args.host, args.port, args.interface, user_id,
                    before_count),
                tracking=True)
    except (OSError, ValueError, ACMDeviceError, RuntimeError) as error:
        return fail(f"{error}")
    result = {
        "policy_preflight_type": initial.requirement_type,
        "policy_satisfied": final.satisfied,
        "e1": e1_summary,
    }
    if private_path is not None:
        private_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2, sort_keys=True))
    if e1_summary.get("dispatch_status") not in (0, 22, -3):
        return fail("E1 halt-state: analyze, no further shots")
    if not e1_summary.get("identities_preserved"):
        return fail("E1 identity state changed; halt all live work")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
