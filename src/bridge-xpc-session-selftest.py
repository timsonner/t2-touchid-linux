#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Fingerless read-only session self-test (no 4, no 74, no confirm needed).

Replays the session-binding cluster minus the token stand-in plus the
capture-exact verdict framing, asserting status 0 everywhere and 0x42
byte-identical afterwards. Every command here has returned status 0 with
zero service events standalone and ordered (2026-09-16, 0x42=2 preserved):

  early: 48-empty, 39-uid, 46-uid x3 (cap 33 -> 32B)
  verdict: 48-empty, 84-20B, 39-uid, 84-20B, 12-empty

Exit 0 PASS, exit 1 FAIL. Never sends opcode 4 or 74, never waits on the
sensor, never touches EP7/ACM/enroll/load/reset. Safe to run any time to
check the warm baseline can carry a full session.
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

from t2_bridge_wire import (  # noqa: E402
    biometric_command,
    describe,
    receive_frame,
    request,
    send_helo,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--interface", required=True)
    parser.add_argument("--macos-user-id", required=True, type=int)
    args = parser.parse_args()
    uid = args.macos_user_id
    steps = [
        (0x30, b"", 1, "early-48-empty"),
        (0x27, struct.pack("<I", uid), 4, "early-39"),
        (0x2E, struct.pack("<I", uid), 33, "early-46-a"),
        (0x2E, struct.pack("<I", uid), 33, "early-46-b"),
        (0x2E, struct.pack("<I", uid), 33, "early-46-c"),
        (0x30, b"", 1, "verdict-48-empty"),
        (0x54, struct.pack("<I", 2) + bytes(16), 83, "verdict-84-a"),
        (0x27, struct.pack("<I", uid), 4, "verdict-39"),
        (0x54, struct.pack("<I", 2) + bytes(16), 83, "verdict-84-b"),
        (0x0C, b"", 0, "verdict-12"),
    ]
    result: dict[str, object] = {"steps": [], "pass": False}
    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
        sock.settimeout(5.0)
        sock.connect((args.host, args.port, 0,
                      socket.if_nametoindex(args.interface)))
        frame_type, body = receive_frame(sock)
        helo = describe(frame_type, body)
        send_helo(sock, int(helo.get("BridgeXPCVersion", 39)))
        request(sock, [0])
        request(sock, [10, 2])
        request(sock, [1])
        pre, _ = biometric_command(
            sock, 0x42, data=struct.pack("<I", uid),
            output_capacity=20 * 10)
        pre_ids = pre[1] if isinstance(pre, list) and len(pre) == 2 else None
        ok = True
        for opcode, data, cap, label in steps:
            reply, events = biometric_command(
                sock, opcode, data=data, output_capacity=cap)
            status = reply[0] if isinstance(reply, list) and reply else None
            out = (reply[1] if isinstance(reply, list) and len(reply) == 2
                   and isinstance(reply[1], bytes) else None)
            result["steps"].append({
                "label": label, "opcode": opcode, "status": status,
                "out_len": None if out is None else len(out),
                "events": len(events)})
            if status != 0 or events:
                ok = False
                result["fail_at"] = label
                break
        post, _ = biometric_command(
            sock, 0x42, data=struct.pack("<I", uid),
            output_capacity=20 * 10)
        post_ids = post[1] if isinstance(post, list) and len(post) == 2 else None
        result["identities_preserved"] = post_ids == pre_ids
        result["identity_count"] = (
            len(post_ids) // 20 if isinstance(post_ids, bytes)
            and len(post_ids) % 20 == 0 else None)
        result["pass"] = bool(ok and result["identities_preserved"])
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
