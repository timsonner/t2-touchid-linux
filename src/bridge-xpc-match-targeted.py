#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""DRAFT (staged, not yet run): targeted 1-record token-free match.

Status: design only. LIVE_T_ENABLED defaults False; even enabled,
this refuses unless ALL of the following hold:

- warm SEP: BridgeXPC 0x42 holds EXACTLY 3 identities for the
  configured UID (the delete-ladder inventory);
- full-inventory repeat_equal true on this boot before the window
  (operator verifies separately; script re-checks 0x42 count
  in-session);
- keybags unlocked (token-free verifies only with unlocked bags
  per K1/K2; no ACM context, no password involved);
- explicit --record-index 0/1/2 selecting which 0x42 record rides
  alone in the counted blob, plus --confirm-live;
- finger present for the window, cancel always, post-0x42==3
  required with byte-identical records.

Rationale: the delete ladder must aim the 0x0d at the ring's exact
20 B record, and insertion order is not evidence. One window per
record with the ring held: the record returning matched:true is
ring's. Stop at the first true; two trues or any identity change
halts the ladder.

Framing (single shot): Sequoia prelude (48 -> 84 -> 39 -> 84 -> 12,
all v1/val0, status-0-gated) -> opcode 4 v1/val0, 68 B token-free
options (flags 0x4000 selected-identities, uid, 60 zero) + counted
blob (count 1 + the selected 20 B record) -> match window -> cancel
-> post-0x42 check.
match_result contents never decoded: only (event_kind, ordinal,
data_length, boolean matched) recorded.

Deliberate limits: single attempt, 60 s event cap, cancel always. No
ACM/password, no enroll/load/reset/delete/EP7 traffic. Per-window raw
JSON opt-in under operator-private paths only.
"""

from __future__ import annotations

import argparse
import importlib.util as _importlib_util
import json
import socket
import struct
import sys
import time
from pathlib import Path

LOCAL_SOURCE = Path(__file__).resolve().parent
if str(LOCAL_SOURCE) not in sys.path:
    sys.path.insert(0, str(LOCAL_SOURCE))

from t2_bridge_wire import (  # noqa: E402
    TYPE_HELO,
    biometric_command,
    describe,
    receive_envelope,
    receive_frame,
    request,
    send_helo,
    send_message,
)

LIVE_T_ENABLED = False
CONFIRM = "I_UNDERSTAND_THIS_STARTS_ONE_TARGETED_MATCH_WINDOW"
MATCH_OPCODE = 4
# The counted blob is only honored as a selection with this flag (the
# reference construction always pairs them). Flags-0 plus a lone blob
# evaluates against nothing and rejects: proven by the T0/T1/T2
# all-false run against a finger that verifies tonight.
MATCH_FLAG_SELECTED_IDENTITIES = 0x4000
PRIVATE_ROOT = Path("/home/tim/Private")


def _load_fork_a():
    path = LOCAL_SOURCE / "bridge-xpc-probe.py"
    spec = _importlib_util.spec_from_file_location(
        "bridge_xpc_match_targeted_fork_a", path)
    assert spec and spec.loader
    module = _importlib_util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


fork_a = _load_fork_a()


def fail(message: str) -> int:
    print(f"match-targeted: {message}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--interface", required=True)
    parser.add_argument("--macos-user-id", required=True, type=int)
    parser.add_argument("--record-index", required=True, type=int,
                        choices=(0, 1, 2))
    parser.add_argument("--match-seconds", type=float, default=30.0)
    parser.add_argument("--confirm-live", default="")
    parser.add_argument("--private-json", default="")
    args = parser.parse_args()

    if not LIVE_T_ENABLED or args.confirm_live != CONFIRM:
        return fail("live targeted-match probe is disabled in source; refusing")
    if not 1.0 <= args.match_seconds <= 60.0:
        return fail("match window must be within 1..60 seconds")
    if not 0 <= args.macos_user_id <= 0xFFFFFFFF:
        return fail("macOS user ID is outside uint32 range")
    private_path = None
    if args.private_json:
        private_path = Path(args.private_json)
        if PRIVATE_ROOT not in private_path.resolve().parents:
            return fail("raw JSON must stay under operator-private storage")

    uid = args.macos_user_id
    summary: dict[str, object] = {
        "opcode": MATCH_OPCODE,
        "stage": f"t{args.record_index}",
        "framing": "token-free-68B-plus-1-record-blob",
        "record_index": args.record_index,
        "warm_gate": False,
        "prelude": [],
        "match_start_status": None,
        "match_result_seen": False,
        "matched": False,
        "cancel_status": None,
        "identities_preserved": False,
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
        summary["warm_gate_detail"] = {"identity_count": count}
        if count != 3 or any(u != uid for u in uids):
            return fail("warm gate failed: need exactly 3 identities")
        summary["warm_gate"] = True
        records = tuple(identities[i * 20:(i + 1) * 20]
                        for i in range(count))
        target = records[args.record_index]

        def run_step(opcode, version, value, data, cap, label, log):
            reply, _ = biometric_command(
                sock, opcode, version=version, value=value,
                data=data, output_capacity=cap)
            status = reply[0] if isinstance(reply, list) and reply else None
            out = reply[1] if (isinstance(reply, list) and len(reply) == 2
                               and isinstance(reply[1], bytes)) else None
            log.append({"label": label, "opcode": opcode, "status": status,
                        "out_len": None if out is None else len(out)})
            return status

        prelude = [
            (0x30, 1, 0, b"", 1, "getEnabledForUnlock-empty"),
            (0x54, 1, 0, struct.pack("<I", 2) + bytes(16), 83,
             "accessory-B"),
            (0x27, 1, 0, struct.pack("<I", uid), 4, "sks-lock"),
            (0x54, 1, 0, struct.pack("<I", 2) + bytes(16), 83,
             "accessory-B"),
            (0x0C, 1, 0, b"", 0, "cancel-idle"),
        ]
        for op, ver, val, data, cap, label in prelude:
            if run_step(op, ver, val, data, cap, label,
                        summary["prelude"]) != 0:
                return fail(f"prelude deviated at {label}; no match attempted")

        options = struct.pack("<II60x", MATCH_FLAG_SELECTED_IDENTITIES,
                                uid)
        match_data = options + struct.pack("<I", 1) + target
        summary["match_request"] = {
            "data_length": len(match_data),
            "selected_identity_count": 1,
        }
        try:
            match_reply, events = biometric_command(
                sock, MATCH_OPCODE, data=match_data)
        except Exception as error:
            return fail(f"match halt-state: transport {type(error).__name__}")
        start_status = (match_reply[0] if isinstance(match_reply, list)
                        and match_reply else None)
        summary["match_start_status"] = start_status
        if start_status != 0:
            print(json.dumps(summary, indent=2, sort_keys=True))
            return fail(f"match did not start: status={start_status}")
        print("TOUCH NOW: place the RING finger flat on Touch ID.",
              flush=True)
        observed: list[dict[str, object]] = []
        deadline = time.monotonic() + args.match_seconds
        while time.monotonic() < deadline:
            sock.settimeout(max(0.1, deadline - time.monotonic()))
            try:
                envelope = receive_envelope(sock)
            except TimeoutError:
                break
            if envelope[1] is False:
                kind = fork_a.summarize_event(
                    envelope[3], (target,), expected_user_id=uid)
                observed.append({
                    "event_kind": kind.get("event_kind"),
                    "ordinal": kind.get("ordinal"),
                    "data_length": kind.get("data_length"),
                    "matched": kind.get("matched"),
                })
                send_message(sock, [1, True, envelope[2], [0]])
                if kind.get("event_kind") == "match_result":
                    summary["match_result_seen"] = True
                    summary["matched"] = bool(kind.get("matched"))
                    break
        sock.settimeout(5.0)
        cancel_reply, cancel_events = biometric_command(sock, 0x0C)
        summary["cancel_status"] = (cancel_reply[0] if isinstance(
            cancel_reply, list) and cancel_reply else None)
        summary["observed_events"] = observed
        events.extend(cancel_events)

        post_reply, _ = biometric_command(
            sock, 0x42, data=struct.pack("<I", uid),
            output_capacity=20 * 10)
        post = (post_reply[1] if isinstance(post_reply, list)
                and len(post_reply) == 2
                and isinstance(post_reply[1], bytes) else None)
        summary["identities_preserved"] = post == identities

    if private_path is not None:
        private_path.write_text(json.dumps(
            {"summary": summary, "event_count": len(events)}, indent=2))
    print(json.dumps(summary, indent=2, sort_keys=True))
    if not summary["identities_preserved"]:
        return fail("identity state changed; halt all live work")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
