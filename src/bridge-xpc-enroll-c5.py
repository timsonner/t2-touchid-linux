#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""DRAFT (staged, not yet run): C5 scratch-UID enroll dance.

Status: design only. LIVE_C5_ENABLED defaults False; even enabled,
this refuses unless ALL of the following hold:

- EMPTY target namespace: BridgeXPC 0x42 holds EXACTLY 0 identities
  for the scratch UID (C5 expects the 0->1 transition; this is the
  UID-native middle ground, NOT macOS-free — the ACM ceremony runs
  against the configured macOS-bag session);
- full-inventory repeat_equal true on this boot before the window;
- full-inventory repeat_equal true on this boot before the window
  (operator verifies separately; script re-checks 0x42 count
  in-session);
- a fresh ACM tracking context creates, shows the type-1 passcode
  requirement, binds the operator password via t2-aks-tool, and reaches
  policy-1007 SATISFIED — all inside with_authorized_context, with
  mandatory context cleanup before return;
- explicit --confirm-live AND --acknowledge-new-identity (the new
  SEP identity is the operator's own ring finger — Track A covers
  operator-owned biometric material; the flag records the ack);
- the operator performs the lift/place dance on prompt (~2 min).

Choreography (capture-faithful, ENROLL_ARG_SHAPES_2026-09-13): full
session prep (5 read-only steps, abort on deviation) -> single 0x03
v2 zero-group 68B dispatch (E1 proved start opens 0; any non-0 start
aborts with cancel and no dance) -> 8x empty 0x0e v1 continues at
~1-2 s pacing with lift/place finger dance -> cancel (UI-teardown
shape) -> post-0x42 read, expecting exactly 3. The post-enroll 0x04
from capture is OMITTED by default (contents never logged; sending
an invented 68B risks confusing fresh state) with opt-in
--with-post-4-standin for a follow-up window only.

Outcome is journaled: full summary (counts/statuses only, no UUIDs,
no payloads) goes to stdout AND, when --private-json points under
operator-private storage, to that file. A 2->3 transition requires
the post-reboot proof (fresh boot, stable 0x42==3, ring matches,
index still matches) before any further mutation. Any deviation —
non-0 start/continue, any service event violating the
status-authoritative assumption, post count other than 2 (refused)
or 3 (enrolled) — halts everything with cancel attempted.

Deliberate limits: one dance per verified-stable baseline, fresh ACM
context + mandatory cleanup, no 0x40/load/reset/delete/EP7 traffic
beyond keybag-session prerequisites. Password handling: operator
terminal only via t2-aks-tool, never stored, never logged.

Prerequisites (operator, in order): minimal-bring-up module load on warm
SEP (pinned set only), re-established EP7 keybag session
(/run/t2-touchid/keybag.env), operator password at the bind prompt,
then the ring-finger dance on prompt.
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

LIVE_C5_ENABLED = False
CONFIRM = "I_UNDERSTAND_THIS_ENROLLS_ONE_SCRATCH_UID_FINGERPRINT"
ACK = "ENROLL_SCRATCH_UID_RING_FINGER"
AKS_TOOL = Path("/usr/local/sbin/t2-aks-tool")
ENROLL_OPCODE = 0x03
ENROLL_VERSION = 2
CONTINUE_OPCODE = 0x0E
EXPECTED_CONTINUES = 8
PRIVATE_ROOT = Path("/home/tim/Private")


def _load_helpers():
    path = LOCAL_SOURCE / "bridge-xpc-authorized-enroll.py"
    spec = _importlib_util.spec_from_file_location(
        "bridge_xpc_enroll_e4_helpers", path)
    assert spec and spec.loader
    module = _importlib_util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fail(message: str) -> int:
    print(f"enroll-c5: {message}", file=sys.stderr)
    return 1


def c5_consumer_factory(host, port, interface, user_id, post_4_standin):
    def consume(external_form: bytes) -> dict[str, object]:
        try:
            return _consume(external_form)
        except RuntimeError as error:
            print(f"enroll-c5: consumer failed: {error}", file=sys.stderr)
            raise

    def _consume(external_form: bytes) -> dict[str, object]:
        if not isinstance(external_form, bytes) or len(external_form) != 16:
            raise RuntimeError("authorized external form is invalid")
        payload = (struct.pack("<IIII", 0, user_id, 0, 16)
                   + external_form + bytes(36))
        assert len(payload) == 68
        helpers = _load_helpers()
        summary: dict[str, object] = {
            "opcode": ENROLL_OPCODE,
            "stage": "c5",
            "framing": "zero-group-68B-plus-8-empty-continues",
            "warm_gate": False,
            "session_prep": [],
            "dispatch_status": None,
            "continues": [],
            "post_4_standin": post_4_standin,
            "post_4_status": None,
            "cancel_status": None,
            "identities_before": 0,
            "identities_after": None,
            "outcome": "unknown",
        }
        sock = helpers.open_bridge(host, port, interface)
        try:
            list_reply, _ = biometric_command(
                sock, 0x42, data=struct.pack("<I", user_id),
                output_capacity=20 * 10)
            if not (isinstance(list_reply, list) and list_reply
                    and list_reply[0] == 0):
                raise RuntimeError("identity enumeration failed")
            identities = (list_reply[1] if len(list_reply) == 2
                          and isinstance(list_reply[1], bytes) else b"")
            if len(identities) != 0:
                raise RuntimeError(
                    "C5 expects an empty namespace (0->1); refusing")
            summary["warm_gate_detail"] = {"identity_count": 0}
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
            if start_status != 0:
                raise RuntimeError(
                    f"enroll did not start: status={start_status}; "
                    "no dance attempted")
            print("ENROLL OPEN. Place the RING finger flat on Touch ID.",
                  flush=True)
            for i in range(1, EXPECTED_CONTINUES + 1):
                if i > 1:
                    print(f"Lift, then place the RING finger again "
                          f"({i}/{EXPECTED_CONTINUES}).", flush=True)
                    time.sleep(1.5)
                cont_reply, cont_events = biometric_command(
                    sock, CONTINUE_OPCODE, version=1, value=0, data=b"",
                    output_capacity=0)
                cont_status = (cont_reply[0] if (
                    isinstance(cont_reply, list) and cont_reply) else None)
                summary["continues"].append({
                    "n": i, "status": cont_status,
                    "events": len(cont_events)})
                # Events are EXPECTED here: capture shows each continue
                # glued to enrollContinue progress. Record, never halt on
                # them; only a non-0 dispatch status halts the dance.
                if cont_status != 0:
                    raise RuntimeError(
                        f"continue {i} refused: status={cont_status}; "
                        "halting dance")
            print("Dance complete. Lift the finger.", flush=True)
            if post_4_standin:
                standin = struct.pack("<II60x", 0, user_id)
                post_reply, _ = biometric_command(
                    sock, 0x04, version=1, value=0, data=standin,
                    output_capacity=0)
                summary["post_4_status"] = (post_reply[0] if isinstance(
                    post_reply, list) and post_reply else None)
            post_reply, _ = biometric_command(
                sock, 0x42, data=struct.pack("<I", user_id),
                output_capacity=20 * 10)
            post = (post_reply[1] if isinstance(post_reply, list)
                    and len(post_reply) == 2
                    and isinstance(post_reply[1], bytes) else None)
            after = None if post is None else len(post) // 20
            summary["identities_after"] = after
            if after == 1:
                summary["outcome"] = "enrolled-pending-proof"
            elif after == 0:
                summary["outcome"] = "refused-clean"
            else:
                summary["outcome"] = "ambiguous-halt-everything"
        finally:
            try:
                cancel_reply, _ = biometric_command(sock, 0x0C)
                summary["cancel_status"] = (cancel_reply[0] if isinstance(
                    cancel_reply, list) and cancel_reply else None)
            except Exception:
                summary["cancel_status"] = -1
            sock.close()
        return summary
    return consume


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--interface", required=True)
    parser.add_argument("--macos-user-id", required=True, type=int)
    parser.add_argument("--scratch-uid", required=True, type=int)
    parser.add_argument("--confirm-live", default="")
    parser.add_argument("--acknowledge-new-identity", default="")
    parser.add_argument("--with-post-4-standin", action="store_true")
    parser.add_argument("--private-json", default="")
    args = parser.parse_args()

    if not LIVE_C5_ENABLED or args.confirm_live != CONFIRM:
        return fail("live C5 probe is disabled in source; refusing")
    if args.acknowledge_new_identity != ACK:
        return fail("new-identity acknowledgement missing; refusing")
    if not 0 <= args.macos_user_id <= 0xFFFFFFFF:
        return fail("macOS user ID is outside uint32 range")
    if not 10 <= args.scratch_uid <= 0xFFFFFFFF:
        return fail("scratch UID is outside the usable range")
    if args.scratch_uid == args.macos_user_id:
        return fail("scratch UID must differ from the configured UID")
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

    def bind_password(context: bytes) -> None:
        completed = subprocess.run(
            [str(AKS_TOOL), "verify-password-acm",
             str(session), str(handle)],
            input=context, check=False)
        if completed.returncode:
            raise ACMDeviceError("AKS password binding failed")

    try:
        with ACMDevice() as device:
            initial, final, c5_summary = with_authorized_context(
                device, args.scratch_uid, bind_password,
                c5_consumer_factory(
                    args.host, args.port, args.interface,
                    args.scratch_uid, args.with_post_4_standin),
                tracking=True)
    except (OSError, ValueError, ACMDeviceError, RuntimeError) as error:
        return fail(f"{error}")
    result = {
        "policy_preflight_type": initial.requirement_type,
        "policy_satisfied": final.satisfied,
        "scratch_uid": args.scratch_uid,
        "c5": c5_summary,
    }
    if private_path is not None:
        private_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2, sort_keys=True))
    if c5_summary.get("outcome") == "ambiguous-halt-everything":
        return fail("C5 ambiguous state; halt all live work and reconcile")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
