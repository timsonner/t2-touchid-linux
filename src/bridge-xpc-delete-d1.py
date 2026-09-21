#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""DRAFT (staged, not yet run): D1 single-identity delete, T-proven record.

Status: design only. LIVE_D1_ENABLED defaults False; even enabled,
this refuses unless ALL of the following hold:

- warm SEP: BridgeXPC 0x42 holds EXACTLY 3 identities for the
  configured UID (the delete-ladder inventory; never the last);
- T-proof recorded: record index 2 returned matched:true against the
  ring with records 0/1 terminal false (T0/T1/T2, valid 0x4000
  framing), identities preserved throughout;
- full-inventory repeat_equal true on this boot before the window
  (operator verifies separately; script re-checks in-session);
- explicit --confirm-live AND --acknowledge-single-deletion (SEP
  deletion is irreversible; the target is the operator's own
  Linux-enrolled ring — Track A covers it; macOS prints are never
  in the blast radius by construction below).

Body: open bridge -> warm gate (==3) -> resolve records fresh and
select index 2 ONLY (any other index refused; the target is never
accepted as bytes on the command line, never logged, never written
outside the in-memory dispatch) -> journal intent (record index +
pre-count + wire version, operator-private path, REQUIRED) ->
single 0x0d dispatch (version from --mesa-version, default 0; D2
runs 1) with the exact 20 B record -> best-effort cancel ->
post-0x42 must be exactly 2 AND byte-equal to records[0:2] (the
survivors). Outcome (counts/indexes only, no UUIDs) appended to the
journal and printed. Trust the stable inventory, never the command
status, for the verdict.

A 3->2 with the exact survivor set closes D1 (then E4r re-enrolls
the ring via the proven dance). Anything else — transport error,
non-empty events on dispatch, post state other than exactly the two
survivors — halts all live work with no replay.

Deliberate limits: single dispatch, credential-free (no ACM, no
password), no enroll/load/reset/no_catacomb traffic. Keybags must
simply be unlocked (K-series). Per-window raw JSON stays
operator-private.
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
    TYPE_HELO,
    biometric_command,
    describe,
    receive_frame,
    request,
    send_helo,
)

LIVE_D1_ENABLED = False
CONFIRM = "I_UNDERSTAND_THIS_DELETES_ONE_FINGERPRINT"
ACK = "DELETE_MY_OWN_RING_IDENTITY"
TARGET_INDEX = 2
PRIVATE_ROOT = Path("/home/tim/Private")


def fail(message: str) -> int:
    print(f"delete-d1: {message}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--interface", required=True)
    parser.add_argument("--macos-user-id", required=True, type=int)
    parser.add_argument("--confirm-live", default="")
    parser.add_argument("--acknowledge-single-deletion", default="")
    parser.add_argument("--mesa-version", type=int, default=0,
                        choices=(0, 1))
    parser.add_argument("--private-json", required=True)
    args = parser.parse_args()

    if not LIVE_D1_ENABLED or args.confirm_live != CONFIRM:
        return fail("live D1 probe is disabled in source; refusing")
    if args.acknowledge_single_deletion != ACK:
        return fail("single-deletion acknowledgement missing; refusing")
    if not 0 <= args.macos_user_id <= 0xFFFFFFFF:
        return fail("macOS user ID is outside uint32 range")
    private_path = Path(args.private_json)
    if PRIVATE_ROOT not in private_path.resolve().parents:
        return fail("journal must stay under operator-private storage")

    uid = args.macos_user_id
    journal: dict[str, object] = {
        "opcode": 13,
        "stage": "d1" if args.mesa_version == 0 else "d2",
        "wire_version": args.mesa_version,
        "target_record_index": TARGET_INDEX,
        "warm_gate": False,
        "dispatch_status": None,
        "cancel_status": None,
        "identities_before": None,
        "identities_after": None,
        "survivors_match_expected": False,
        "outcome": "unknown",
    }
    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
        sock.settimeout(5.0)
        sock.connect((args.host, args.port, 0,
                      socket.if_nametoindex(args.interface)))
        frame_type, body = receive_frame(sock)
        if frame_type != TYPE_HELO:
            return fail(f"expected HELO frame, got type {frame_type}")
        helo = describe(frame_type, body)
        send_helo(sock, int(helo.get("BridgeXPCVersion", 39)))
        version_reply = request(sock, [0])
        if (not isinstance(version_reply, list)
                or len(version_reply) != 2 or version_reply[0] != 0):
            return fail(f"getBridgeVersion failed: {version_reply!r}")
        if request(sock, [10, min(version_reply[1], 2)]) != [0]:
            return fail("bridge client-version negotiation failed")
        if request(sock, [1]) != [0, True]:
            return fail("biometric service did not report opened")

        list_reply, _ = biometric_command(
            sock, 0x42, data=struct.pack("<I", uid),
            output_capacity=20 * 10)
        identities = (list_reply[1] if isinstance(list_reply, list)
                      and len(list_reply) == 2
                      and isinstance(list_reply[1], bytes) else b"")
        count = len(identities) // 20 if len(identities) % 20 == 0 else -1
        uids = ([struct.unpack_from("<I", identities, i * 20)[0]
                 for i in range(count)] if count > 0 else [])
        journal["identities_before"] = count
        if count != 3 or any(u != uid for u in uids):
            return fail("warm gate failed: need exactly 3 identities")
        journal["warm_gate"] = True
        records = tuple(identities[i * 20:(i + 1) * 20]
                        for i in range(count))
        target = records[TARGET_INDEX]
        expected_survivors = records[:TARGET_INDEX]

        journal["intent"] = {
            "target_record_index": TARGET_INDEX,
            "pre_count": count,
        }
        try:
            private_path.write_text(json.dumps(journal, indent=2))
        except OSError as error:
            return fail(f"intent journal unwritable: {error}; refusing")

        try:
            del_reply, del_events = biometric_command(
                sock, 0x0D, version=args.mesa_version, value=0,
                data=target, output_capacity=0)
        except Exception as error:
            journal["outcome"] = "transport-ambiguous-halt-everything"
            private_path.write_text(json.dumps(journal, indent=2))
            print(json.dumps(journal, indent=2, sort_keys=True))
            return fail(
                f"delete transport {type(error).__name__}; "
                "reconcile, never replay")
        journal["dispatch_status"] = (del_reply[0] if isinstance(
            del_reply, list) and del_reply else None)
        journal["dispatch_events"] = len(del_events)
        if del_events:
            journal["outcome"] = "events-on-dispatch-halt-everything"
            private_path.write_text(json.dumps(journal, indent=2))
            print(json.dumps(journal, indent=2, sort_keys=True))
            return fail("service events on delete dispatch; reconcile")
        try:
            cancel_reply, _ = biometric_command(sock, 0x0C)
            journal["cancel_status"] = (cancel_reply[0] if isinstance(
                cancel_reply, list) and cancel_reply else None)
        except Exception:
            journal["cancel_status"] = -1
        post_reply, _ = biometric_command(
            sock, 0x42, data=struct.pack("<I", uid),
            output_capacity=20 * 10)
        post = (post_reply[1] if isinstance(post_reply, list)
                and len(post_reply) == 2
                and isinstance(post_reply[1], bytes) else None)
        post_count = None if post is None else len(post) // 20
        journal["identities_after"] = post_count
        journal["survivors_match_expected"] = (
            post is not None
            and bytes(post) == b"".join(expected_survivors))
        if post_count == 2 and journal["survivors_match_expected"]:
            journal["outcome"] = "deleted-confirmed"
        else:
            journal["outcome"] = "ambiguous-halt-everything"
        private_path.write_text(json.dumps(journal, indent=2))

    print(json.dumps(journal, indent=2, sort_keys=True))
    if journal["outcome"] != "deleted-confirmed":
        return fail("D1 did not confirm cleanly; halt all live work")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
