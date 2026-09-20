#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""DRAFT (staged, not yet run): one credential-set-bearing opcode-4 window.

Status: design only. LIVE_F1_ENABLED defaults False; even enabled,
this refuses unless ALL of the following hold:

- warm SEP: BridgeXPC 0x42 holds >=2 identities for the configured UID
  (post-S5 count; SKS informational only);
- full-inventory repeat_equal true on this boot before the window
  (operator verifies separately; script re-checks 0x42 count in-session);
- a fresh ACM tracking context creates, shows the type-1 passcode
  requirement, binds the operator password via t2-aks-tool, and reaches
  policy-1007 SATISFIED — all inside with_authorized_context, with
  mandatory context cleanup before return;
- the Sequoia prelude (48 -> 84 -> 39 -> 84 -> 12, all status 0)
  completes without deviation;
- explicit --confirm-live.

Rationale: our Fork-A opcode-4 windows (2026-09-13, windows 1-6 plain /
7-8 framing) all used token-free options (flags 0, uid, 60 zero bytes)
and stayed mute — open (status 0) but zero match_result events even
with 60 s continuous contact. The sibling t2touch project (MBP16,1,
same bridgeOS 23P6068 string) verifies through an authorization-bearing
match request: 68-byte options with MATCH_FLAG_FOR_CREDENTIAL_SET
(0x08) plus the 16-byte ACM external form at offset 12, combined with
the unlock flag (0x01) and the counted identity blob
(build_match_request in their bridge-xpc-probe.py). Window 8 already
proved unlock-flag-1 without the form still refuses/mutes, so F1
isolates exactly one new variable: the 16-byte form + 0x08.

Framing (single shot, finger present):
  68B header = flags (0x01|0x08|0x4000) | uid | credlen (16) | 16B form
  + counted blob (count + N x 20B records from 0x42), opcode 4,
  ver 1 val 0, then the match window, cancel always.

Predictions: match_result with matched=true reopens the track (the
mute was missing authorization, no session-proxy needed); status 258
at dispatch or a mute window closes the Fork-A credential lens and the
H2 proxy track stands. Any start status other than 0/258, any
post-0x42 != 2, or any service event violating the status-authoritative
assumption halts all live work.

Deliberate limits: single attempt, 60 s event cap, cancel always,
post-0x42 preserved check. match_result contents are never decoded:
only (event_kind, ordinal, data_length, boolean matched) is recorded.
Per-window raw JSON is opt-in and restricted to operator-private paths.
Password handling: operator terminal only via t2-aks-tool, never stored,
never logged, no disk/git/log copies. No enroll / load / reset / delete /
EP7 traffic beyond the keybag-session prerequisites below.

Prerequisites (operator, in order): minimal-bring-up module load on warm
SEP (register_ool=1 register_acm=1 aks_start_cpu=0 aks_ep0_nop=0
aks_discover=0 aks_device_state_canary=0 — the ONLY warm-surviving set;
default params kill the machine, journal-proven 2/2), re-established
EP7 keybag session (/run/t2-touchid/keybag.env), enrolled finger ready.
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
    TYPE_HELO,
    biometric_command,
    describe,
    receive_envelope,
    receive_frame,
    request,
    send_helo,
    send_message,
)
from t2_acm_device import (  # noqa: E402
    ACMDevice,
    ACMDeviceError,
    with_authorized_context,
)

LIVE_F1_ENABLED = False
CONFIRM = "I_UNDERSTAND_THIS_STARTS_ONE_AUTHORIZED_F1_MATCH_WINDOW"
CONFIG = Path("/etc/t2-touchid.conf")
KEYBAG_STATE = Path("/run/t2-touchid/keybag.env")
AKS_TOOL = Path("/usr/local/sbin/t2-aks-tool")
MATCH_OPCODE = 4
MATCH_FLAG_FOR_UNLOCK = 0x0001
MATCH_FLAG_FOR_CREDENTIAL_SET = 0x0008
MATCH_FLAG_SELECTED_IDENTITIES = 0x4000
PRIVATE_ROOT = Path("/home/tim/Private")


def _load_helpers():
    path = LOCAL_SOURCE / "bridge-xpc-authorized-enroll.py"
    spec = _importlib_util.spec_from_file_location(
        "bridge_xpc_match_f1_authorized_enroll", path)
    assert spec and spec.loader
    module = _importlib_util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_fork_a():
    path = LOCAL_SOURCE / "bridge-xpc-probe.py"
    spec = _importlib_util.spec_from_file_location(
        "bridge_xpc_match_f1_fork_a", path)
    assert spec and spec.loader
    module = _importlib_util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fail(message: str) -> int:
    print(f"match-f1-authorized: {message}", file=sys.stderr)
    return 1


def build_f1_match_request(
    apple_user_id: int,
    credential_form: bytes,
    selected_records: tuple[bytes, ...],
) -> tuple[bytes, int]:
    """Authorization-bearing opcode-4 framing (t2touch construction).

    68-byte options: flags (unlock | credential-set | selected) |
    uid | credential length (16) | 16-byte ACM external form, then the
    counted blob (record count + N x 20-byte 0x42 records).
    """
    if not 0 <= apple_user_id <= 0xFFFFFFFF:
        raise ValueError("macOS user ID is outside uint32 range")
    if len(credential_form) != 16:
        raise ValueError("credential form is not exactly 16 bytes")
    if (not selected_records or any(
            type(record) is not bytes or len(record) != 20
            for record in selected_records)):
        raise ValueError("selected identity records are invalid")
    flags = (MATCH_FLAG_FOR_UNLOCK | MATCH_FLAG_FOR_CREDENTIAL_SET
             | MATCH_FLAG_SELECTED_IDENTITIES)
    header = bytearray(68)
    struct.pack_into("<III", header, 0, flags, apple_user_id,
                     len(credential_form))
    header[12:12 + len(credential_form)] = credential_form
    payload = (bytes(header) + struct.pack("<I", len(selected_records))
               + b"".join(selected_records))
    return payload, flags


def f1_consumer_factory(host, port, interface, user_id, fork_a,
                        match_seconds):
    def consume(external_form: bytes) -> dict[str, object]:
        summary: dict[str, object] = {
            "opcode": MATCH_OPCODE,
            "stage": "f1",
            "framing": "credential-set-bearing-68B-plus-counted-blob",
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
            sock.connect((host, port, 0,
                          socket.if_nametoindex(interface)))
            frame_type, body = receive_frame(sock)
            if frame_type != TYPE_HELO:
                raise RuntimeError(
                    f"expected HELO frame, got type {frame_type}")
            helo = describe(frame_type, body)
            send_helo(sock, int(helo.get("BridgeXPCVersion", 39)))
            version_reply = request(sock, [0])
            if (not isinstance(version_reply, list)
                    or len(version_reply) != 2
                    or version_reply[0] != 0):
                raise RuntimeError(
                    f"getBridgeVersion failed: {version_reply!r}")
            if request(sock, [10, min(version_reply[1], 2)]) != [0]:
                raise RuntimeError(
                    "bridge client-version negotiation failed")
            if request(sock, [1]) != [0, True]:
                raise RuntimeError(
                    "biometric service did not report opened")

            list_reply, _ = biometric_command(
                sock, 0x42, data=struct.pack("<I", user_id),
                output_capacity=20 * 10)
            identities = (list_reply[1] if isinstance(list_reply, list)
                          and len(list_reply) == 2
                          and isinstance(list_reply[1], bytes) else b"")
            count = (len(identities) // 20
                     if len(identities) % 20 == 0 else -1)
            uids = ([struct.unpack_from("<I", identities, i * 20)[0]
                     for i in range(count)] if count > 0 else [])
            summary["warm_gate_detail"] = {"identity_count": count}
            if count < 2 or any(u != user_id for u in uids):
                raise RuntimeError(
                    "warm gate failed: need >=2 identities for this UID")
            summary["warm_gate"] = True
            records = tuple(identities[i * 20:(i + 1) * 20]
                            for i in range(count))

            def run_step(opcode, version, value, data, cap, label):
                reply, _ = biometric_command(
                    sock, opcode, version=version, value=value,
                    data=data, output_capacity=cap)
                status = reply[0] if isinstance(reply, list) and reply else None
                out = (reply[1] if isinstance(reply, list)
                       and len(reply) == 2
                       and isinstance(reply[1], bytes) else None)
                summary["prelude"].append(
                    {"label": label, "opcode": opcode, "status": status,
                     "out_len": None if out is None else len(out)})
                return status

            prelude = [
                (0x30, 1, 0, b"", 1, "getEnabledForUnlock-empty"),
                (0x54, 1, 0, struct.pack("<I", 2) + bytes(16), 83,
                 "accessory-B"),
                (0x27, 1, 0, struct.pack("<I", user_id), 4, "sks-lock"),
                (0x54, 1, 0, struct.pack("<I", 2) + bytes(16), 83,
                 "accessory-B"),
                (0x0C, 1, 0, b"", 0, "cancel-idle"),
            ]
            for op, ver, val, data, cap, label in prelude:
                if run_step(op, ver, val, data, cap, label) != 0:
                    raise RuntimeError(
                        f"prelude deviated at {label}; no match attempted")

            match_data, flags = build_f1_match_request(
                user_id, external_form, records)
            summary["match_request"] = {
                "data_length": len(match_data),
                "processed_flags": flags,
                "selected_identity_count": len(records),
                "credential_set_authorized": True,
                "credential_set_length": len(external_form),
            }
            match_reply, events = biometric_command(
                sock, MATCH_OPCODE, data=match_data)
            start_status = (match_reply[0] if isinstance(match_reply, list)
                            and match_reply else None)
            summary["match_start_status"] = start_status
            if start_status != 0:
                return summary
            print("TOUCH NOW: place the enrolled finger flat on Touch ID.",
                  flush=True)
            observed: list[dict[str, object]] = []
            deadline = time.monotonic() + match_seconds
            while time.monotonic() < deadline:
                sock.settimeout(max(0.1, deadline - time.monotonic()))
                try:
                    envelope = receive_envelope(sock)
                except TimeoutError:
                    break
                if envelope[1] is False:
                    kind = fork_a.summarize_event(
                        envelope[3], records, expected_user_id=user_id)
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
                sock, 0x42, data=struct.pack("<I", user_id),
                output_capacity=20 * 10)
            post = (post_reply[1] if isinstance(post_reply, list)
                    and len(post_reply) == 2
                    and isinstance(post_reply[1], bytes) else None)
            summary["identities_preserved"] = post == identities
        return summary
    return consume


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--interface", required=True)
    parser.add_argument("--macos-user-id", required=True, type=int)
    parser.add_argument("--match-seconds", type=float, default=30.0)
    parser.add_argument("--confirm-live", default="")
    parser.add_argument("--private-json", default="")
    args = parser.parse_args()

    if not LIVE_F1_ENABLED or args.confirm_live != CONFIRM:
        return fail("live F1 probe is disabled in source; refusing")
    if not 1.0 <= args.match_seconds <= 60.0:
        return fail("match window must be within 1..60 seconds")
    if not 0 <= args.macos_user_id <= 0xFFFFFFFF:
        return fail("macOS user ID is outside uint32 range")
    private_path = None
    if args.private_json:
        private_path = Path(args.private_json)
        if PRIVATE_ROOT not in private_path.resolve().parents:
            return fail("raw JSON must stay under operator-private storage")

    helpers = _load_helpers()
    fork_a = _load_fork_a()
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
            initial, final, match_summary = with_authorized_context(
                device, user_id, bind_password,
                f1_consumer_factory(
                    args.host, args.port, args.interface, user_id,
                    fork_a, args.match_seconds),
                tracking=True)
    except (OSError, ValueError, ACMDeviceError, RuntimeError) as error:
        return fail(f"{error}")
    result = {
        "policy_preflight_type": initial.requirement_type,
        "policy_satisfied": final.satisfied,
        "authorized_f1": match_summary,
    }
    if private_path is not None:
        private_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
