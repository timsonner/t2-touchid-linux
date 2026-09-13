#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""DRAFT (not yet run): bounded Mesa-74 match framing probe, Sequoia order.

Status: design only. LIVE_74_ENABLED defaults False; even enabled, the warm
gate aborts before any match traffic unless the SEP holds an identity
(0x42 count>=1 for the configured UID) and reports warm SKS (0x10).

Rationale: Sequoia working-unlock captures send zero opcode-4 and frame
match traffic as 48 -> 84 -> 39 -> 84 -> 12 -> 74
(MESA64_FRESHBOOT_MINE_2026-09-13.md, MATCH_FORKA_2026-09-13.md). Fork A
proved opcode-4 opens-but-mute; this probe asks whether 74 opens at all,
using the identical 68-byte-options + counted-blob framing, exactly once.
A nonzero start status ends the run: no payload variants, no sprays.

Deliberate limits:
- No enroll / load / reset / delete / EP7 traffic of any kind.
- match_result contents are never decoded here: on the result ordinal the
  probe records the privacy-safe summary (kind/ordinal/boolean verdict
  only, via the shared Fork A summarizer — no UUIDs, no image metrics)
  and stops. Verdict attribution beyond that boolean belongs to a later
  gated analysis pass, not this script.
- Per-window raw JSON is opt-in and restricted to operator-private paths.
"""

from __future__ import annotations

import argparse
import json
import socket
import struct
import sys
import time
from pathlib import Path

LOCAL_SOURCE = Path(__file__).resolve().parent
if str(LOCAL_SOURCE) not in sys.path:
    sys.path.insert(0, str(LOCAL_SOURCE))

import importlib.util as _importlib_util

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


def _load_fork_a():  # noqa: E402
    path = LOCAL_SOURCE / "bridge-xpc-probe.py"
    spec = _importlib_util.spec_from_file_location(
        "bridge_xpc_match74_fork_a", path)
    assert spec and spec.loader
    module = _importlib_util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


fork_a = _load_fork_a()

LIVE_74_ENABLED = False
CONFIRM = "I_UNDERSTAND_THIS_STARTS_ONE_BOUNDED_MATCH74_WINDOW"
WARM_SKS_STATE = 0x10
MATCH74_OPCODE = 74
MATCH_RESULT_ORDINAL = 0xE3FF8002
PRIVATE_ROOT = Path("/home/tim/Private")


def fail(message: str) -> int:
    print(f"match74-probe: {message}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--interface", required=True)
    parser.add_argument("--macos-user-id", required=True, type=int)
    parser.add_argument("--match-seconds", type=float, default=30.0)
    parser.add_argument("--match-processed-flags", type=int, default=0)
    parser.add_argument("--confirm-live", default="")
    parser.add_argument("--private-json", default="")
    args = parser.parse_args()

    if not LIVE_74_ENABLED or args.confirm_live != CONFIRM:
        return fail("live 74 probe is disabled in source; refusing")
    if not 1.0 <= args.match_seconds <= 60.0:
        return fail("match window must be within 1..60 seconds")
    if not 0 <= args.macos_user_id <= 0xFFFFFFFF:
        return fail("macOS user ID is outside uint32 range")
    private_path = None
    if args.private_json:
        private_path = Path(args.private_json)
        if PRIVATE_ROOT not in private_path.resolve().parents:
            return fail("raw JSON must stay under operator-private storage")

    scope_id = socket.if_nametoindex(args.interface)
    summary: dict[str, object] = {
        "opcode": MATCH74_OPCODE,
        "warm_gate": False,
        "prelude": [],
        "match_start_status": None,
        "match_result_seen": False,
        "cancel_status": None,
        "identities_preserved": False,
    }
    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
        sock.settimeout(5.0)
        sock.connect((args.host, args.port, 0, scope_id))
        frame_type, body = receive_frame(sock)
        if frame_type != TYPE_HELO:
            return fail(f"expected HELO frame, got type {frame_type}")
        helo = describe(frame_type, body)
        send_helo(sock, int(helo.get("BridgeXPCVersion", 39)))
        version_reply = request(sock, [0])
        if (not isinstance(version_reply, list)
                or len(version_reply) != 2 or version_reply[0] != 0):
            return fail(f"getBridgeVersion failed: {version_reply!r}")
        client_version = min(version_reply[1], 2)
        if request(sock, [10, client_version]) != [0]:
            return fail("bridge client-version negotiation failed")
        if request(sock, [1]) != [0, True]:
            return fail("biometric service did not report opened")

        # Warm gate: identity list + SKS state. Abort cold, before match.
        list_reply, _ = biometric_command(
            sock, 0x42, data=struct.pack("<I", args.macos_user_id),
            output_capacity=20 * 10,
        )
        identities = (
            list_reply[1] if isinstance(list_reply, list) and
            len(list_reply) == 2 and isinstance(list_reply[1], bytes)
            else b""
        )
        count = len(identities) // 20 if len(identities) % 20 == 0 else -1
        uids = (
            [struct.unpack_from("<I", identities, i * 20)[0]
             for i in range(count)] if count > 0 else []
        )
        sks_reply, _ = biometric_command(
            sock, 0x27, data=struct.pack("<I", args.macos_user_id),
            output_capacity=4,
        )
        # NOTE: the direct BiometricKit framing returns a 4-byte SKS payload
        # whose layout differs from the coupled path (observed warm:
        # 10080000). Only the first byte carries the known state across
        # all readings (0x10 warm, 0x15 cold on the coupled path); gate on
        # it and let the 0x42 count carry the hard fail-closed decision.
        sks = (
            sks_reply[1][0]
            if isinstance(sks_reply, list) and len(sks_reply) == 2
            and isinstance(sks_reply[1], bytes) and len(sks_reply[1]) == 4
            else None
        )
        summary["warm_gate_detail"] = {"identity_count": count, "sks": sks}
        if count < 1 or any(u != args.macos_user_id for u in uids):
            return fail("warm gate failed: no trusted identity for this UID")
        if sks != WARM_SKS_STATE:
            return fail(f"warm gate failed: SKS state {sks} is not warm")
        summary["warm_gate"] = True

        # Sequoia prelude, in order. Any deviation aborts the run.
        prelude_steps = [
            (0x30, 1, 0, struct.pack("<I", args.macos_user_id), 1, "getEnabledForUnlock"),
            (0x54, 1, 0, struct.pack("<I", 2) + bytes(16), 83, "accessory-B"),
            (0x27, 1, 0, struct.pack("<I", args.macos_user_id), 4, "sks-lock"),
            (0x54, 1, 0, struct.pack("<I", 2) + bytes(16), 83, "accessory-B"),
            (0x0C, 1, 0, b"", 0, "cancel-idle"),
        ]
        for opcode, version, value, data, cap, label in prelude_steps:
            reply, _ = biometric_command(
                sock, opcode, version=version, value=value,
                data=data, output_capacity=cap,
            )
            status = reply[0] if isinstance(reply, list) and reply else None
            out_len = len(reply[1]) if (
                isinstance(reply, list) and len(reply) == 2
                and isinstance(reply[1], bytes)) else None
            summary["prelude"].append(
                {"label": label, "opcode": opcode, "status": status,
                 "out_len": out_len})
            if status != 0:
                print(json.dumps(summary, indent=2, sort_keys=True))
                return fail(f"prelude deviated at {label}: status={status}")

        # Match-start on 74: Fork A framing, one shot, no variants.
        counted = struct.pack("<I", count) + identities
        match_data = struct.pack(
            "<II60x", args.match_processed_flags, args.macos_user_id,
        ) + counted
        match_reply, events = biometric_command(sock, MATCH74_OPCODE,
                                                data=match_data)
        start_status = match_reply[0] if (
            isinstance(match_reply, list) and match_reply) else None
        summary["match_start_status"] = start_status
        if start_status != 0:
            print(json.dumps(summary, indent=2, sort_keys=True))
            return fail(f"74 did not start: status={start_status}; "
                        "no variants attempted")
        print("TOUCH NOW: place the enrolled finger flat on Touch ID.",
              flush=True)
        enrolled_records = tuple(
            identities[i * 20:(i + 1) * 20] for i in range(count))
        observed: list[dict[str, object]] = []
        deadline = time.monotonic() + args.match_seconds
        while time.monotonic() < deadline:
            sock.settimeout(max(0.1, deadline - time.monotonic()))
            try:
                envelope = receive_envelope(sock)
            except TimeoutError:
                break
            if envelope[1] is False:
                message = envelope[3]
                # Privacy-safe summary only: kinds, ordinals, lengths.
                # match_result UUID verdicts stay boolean inside the summary.
                kind = fork_a.summarize_event(
                    message, enrolled_records,
                    expected_user_id=args.macos_user_id)
                observed.append({
                    "event_kind": kind.get("event_kind"),
                    "ordinal": kind.get("ordinal"),
                    "data_length": kind.get("data_length"),
                    "status_code": kind.get("status_code"),
                    "matched": kind.get("matched"),
                })
                events.append(message)
                send_message(sock, [1, True, envelope[2], [0]])
                if kind.get("event_kind") == "match_result":
                    summary["match_result_seen"] = True
                    break
        sock.settimeout(5.0)
        cancel_reply, cancel_events = biometric_command(sock, 0x0C)
        summary["cancel_status"] = cancel_reply[0] if (
            isinstance(cancel_reply, list) and cancel_reply) else None
        summary["observed_events"] = observed
        events.extend(cancel_events)

        # Warm-preserved proof.
        post_reply, _ = biometric_command(
            sock, 0x42, data=struct.pack("<I", args.macos_user_id),
            output_capacity=20 * 10,
        )
        post = post_reply[1] if (
            isinstance(post_reply, list) and len(post_reply) == 2
            and isinstance(post_reply[1], bytes)) else None
        summary["identities_preserved"] = post == identities

    if private_path is not None:
        private_path.write_text(json.dumps(
            {"summary": summary,
             "event_count": len(events)}, indent=2))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
