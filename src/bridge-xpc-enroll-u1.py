#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""DRAFT (staged): U1 unbound-form enroll-start probe.

Status: design only. LIVE_U1_ENABLED defaults False; even enabled,
this refuses unless --confirm-live matches. No password, no finger,
no ACM policy involved: mint a tracking context, externalize it,
DELETE it immediately, then dispatch 0x03 v2 zero-group 68B carrying
the dead 16 B reference. Cancel whatever happens; post-0x42 must
equal pre-count.

Question: does the token need an AUTHORIZED form (policy-1007 live,
E1-proven) or merely form-shaped bytes? 22 preserves the status quo
(authorization required); 0 means structure suffices and the native
story gets much simpler (contexts without ceremonies).
"""

from __future__ import annotations

import argparse
import json
import socket
import struct
import sys
from pathlib import Path

LOCAL_SOURCE = Path(__file__).resolve().parent
if str(LOCAL_SOURCE) not in sys.path:
    sys.path.insert(0, str(LOCAL_SOURCE))

from t2_bridge_wire import biometric_command  # noqa: E402
from t2_acm_device import (  # noqa: E402
    ACMDevice, ACMDeviceError, externalize_context,
)
import t2_acm_protocol as protocol  # noqa: E402

LIVE_U1_ENABLED = False
CONFIRM = "I_UNDERSTAND_THIS_TESTS_UNBOUND_FORM_STRUCTURE"


def fail(message: str) -> int:
    print(f"enroll-u1: {message}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--interface", required=True)
    parser.add_argument("--macos-user-id", required=True, type=int)
    parser.add_argument("--confirm-live", default="")
    args = parser.parse_args()

    if not LIVE_U1_ENABLED or args.confirm_live != CONFIRM:
        return fail("live U1 probe is disabled in source; refusing")
    uid = args.macos_user_id
    summary: dict[str, object] = {
        "opcode": 3, "stage": "u1",
        "framing": "zero-group-68B-unbound-form",
        "dispatch_status": None, "cancel_status": None,
        "identities_before": None, "identities_after": None,
        "identities_preserved": False,
    }
    try:
        with ACMDevice() as device:
            resp = device.exchange(
                protocol.build_create(user_id=uid, tracking=True), 21)
            handle = protocol.parse_create_response(resp, tracking=True)
            try:
                form = bytes(externalize_context(device, handle))
            finally:
                cleanup = protocol.ContextHandle(
                    resp[:protocol.CONTEXT_SIZE], 0, True, False)
                device.exchange(protocol.build_delete(cleanup), 0)
    except (OSError, ValueError, ACMDeviceError) as error:
        return fail(f"ACM mint failed: {error}")
    if len(form) != 16:
        return fail("form is not 16 bytes")
    payload = struct.pack("<IIII", 0, uid, 0, 16) + form + bytes(36)
    assert len(payload) == 68
    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
        sock.settimeout(5.0)
        sock.connect((args.host, args.port, 0,
                      socket.if_nametoindex(args.interface)))
        from t2_bridge_wire import (  # noqa: E402
            describe, receive_frame, request, send_helo,
        )
        frame_type, body = receive_frame(sock)
        if frame_type != 1:
            return fail("expected HELO frame")
        helo = describe(frame_type, body)
        send_helo(sock, int(helo.get("BridgeXPCVersion", 39)))
        version_reply = request(sock, [0])
        if (not isinstance(version_reply, list)
                or len(version_reply) != 2 or version_reply[0] != 0):
            return fail("getBridgeVersion failed")
        if request(sock, [10, min(version_reply[1], 2)]) != [0]:
            return fail("client-version negotiation failed")
        if request(sock, [1]) != [0, True]:
            return fail("service did not report opened")
        list_reply, _ = biometric_command(
            sock, 0x42, data=struct.pack("<I", uid),
            output_capacity=20 * 10)
        identities = (list_reply[1] if isinstance(list_reply, list)
                      and len(list_reply) == 2
                      and isinstance(list_reply[1], bytes) else None)
        before = None if identities is None else len(identities) // 20
        summary["identities_before"] = before
        if before != 3:
            return fail(f"warm gate: want 3, have {before}")
        try:
            start_reply, _ = biometric_command(
                sock, 3, version=2, value=0, data=payload,
                output_capacity=0)
            start_status = (start_reply[0] if isinstance(
                start_reply, list) and start_reply else None)
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
                    sock, 0x42, data=struct.pack("<I", uid),
                    output_capacity=20 * 10)
                post = (post_reply[1] if isinstance(post_reply, list)
                        and len(post_reply) == 2
                        and isinstance(post_reply[1], bytes) else None)
                summary["identities_after"] = (
                    None if post is None else len(post) // 20)
                summary["identities_preserved"] = (
                    summary["identities_after"] == 3)
            except Exception:
                summary["identities_preserved"] = False
    print(json.dumps(summary, indent=2, sort_keys=True))
    if not summary["identities_preserved"]:
        return fail("identity state changed; halt all live work")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
