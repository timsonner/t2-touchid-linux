#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""DRAFT (live-gated): one authorized ACM-token enrollment, uid 501.

Status: LIVE_ENROLL_ENABLED defaults False. This is the program's first
SEP-mutating act: on success it mints one new fingerprint identity next
to the macOS enrollment (capacity max 5). Operator's own finger, own
machine, Track A only. Requires explicit --confirm-live AND warm gate.

Flow: config + keybag-runtime checks -> bridge warm gate (0x42 count in
1..4, SKS first byte 0x10) -> fresh ACM context -> policy preflight ->
password bind (AKS verify over operator terminal) -> policy final ->
command-3 dispatch with the 16-byte authorized form -> bounded
progress-guided event window -> cancel always -> post-0x42 delta check.

Deliberate limits: single attempt, 60 s event cap, no payload variants
(nonzero start status ends the run), no enroll-continue (0x0e), no
save/reset/delete traffic. The terminal enroll result is NEVER decoded
to identity bytes here: only (ordinal, version, length) is recorded and
success is proven by the post-0x42 count delta with matching UIDs.
"""

from __future__ import annotations

import argparse
import importlib.util as _importlib_util
import json
import os
import pwd
import re
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

LIVE_ENROLL_ENABLED = False
CONFIRM = "I_UNDERSTAND_THIS_CREATES_ONE_FINGERPRINT_IDENTITY"
CONFIG = Path("/etc/t2-touchid.conf")
KEYBAG_STATE = Path("/run/t2-touchid/keybag.env")
AKS_TOOL = Path("/usr/local/sbin/t2-aks-tool")
ENROLL_OPCODE = 0x03
ENROLL_VERSION = 2
READY_ORDINAL = 0xE3FF8001
RESULT_ORDINAL = 0xE3FF8003
PROGRESS_MINIMUMS = {
    0xE3FF8004: 12,
    0xE3FF8005: 17,
    0xE3FF8006: 0,
    0xE3FF8007: 0,
    0xE3FF8008: 0,
    0xE3FF8009: 0,
    0xE3FF800A: 6,
}
PRIVATE_ROOT = Path("/home/tim/Private")


def _load_fork_a():
    path = LOCAL_SOURCE / "bridge-xpc-probe.py"
    spec = _importlib_util.spec_from_file_location(
        "bridge_xpc_authorized_enroll_fork_a", path)
    assert spec and spec.loader
    module = _importlib_util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


fork_a = _load_fork_a()


class EnrollRunnerError(RuntimeError):
    pass


def fail(message: str) -> int:
    print(f"authorized-enroll: {message}", file=sys.stderr)
    return 1


def configuration() -> tuple[int, int, int]:
    info = CONFIG.stat()
    if info.st_uid != 0 or info.st_mode & 0o077:
        raise EnrollRunnerError("configuration ownership or mode is unsafe")
    values: dict[str, list[str]] = {
        "T2_TOUCHID_MACOS_USER_ID": [],
        "T2_TOUCHID_SPECIAL_BAG": [],
        "T2_TOUCHID_USER": [],
    }
    for line in CONFIG.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([A-Z0-9_]+)=(.*)", line)
        if match and match.group(1) in values:
            values[match.group(1)].append(match.group(2))
    user_ids = values["T2_TOUCHID_MACOS_USER_ID"]
    handles = values["T2_TOUCHID_SPECIAL_BAG"]
    linux_users = values["T2_TOUCHID_USER"]
    if (len(user_ids) != 1 or not user_ids[0].isdecimal()
            or not 0 <= int(user_ids[0]) <= 0xFFFFFFFF):
        raise EnrollRunnerError("configuration has no unique valid macOS user ID")
    if (len(handles) != 1 or not re.fullmatch(r"-?[0-9]+", handles[0])
            or int(handles[0]) != -int(user_ids[0])):
        raise EnrollRunnerError("special bag does not match the macOS user ID")
    if len(linux_users) != 1 or not linux_users[0]:
        raise EnrollRunnerError("configuration has no unique mapped Linux user")
    try:
        linux_uid = pwd.getpwnam(linux_users[0]).pw_uid
    except KeyError as error:
        raise EnrollRunnerError("configured Linux user does not exist") from error
    if linux_uid <= 0:
        raise EnrollRunnerError("configured Linux user cannot be root")
    return int(user_ids[0]), int(handles[0]), linux_uid


def caller_is_mapped(mapped_uid: int) -> bool:
    callers = {
        int(value) for key in ("SUDO_UID", "PKEXEC_UID")
        if (value := os.environ.get(key)) and value.isdecimal()
    }
    return callers == {mapped_uid}


def keybag_runtime(expected_special: int) -> tuple[int, int]:
    info = KEYBAG_STATE.stat()
    if info.st_uid != 0 or info.st_mode & 0o077:
        raise EnrollRunnerError("runtime keybag state ownership or mode is unsafe")
    values: dict[str, list[int]] = {
        "T2_KEYBAG_SESSION": [],
        "T2_KEYBAG_HANDLE": [],
        "T2_KEYBAG_SPECIAL": [],
    }
    for line in KEYBAG_STATE.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([A-Z0-9_]+)=(-?[0-9]+)", line)
        if match and match.group(1) in values:
            values[match.group(1)].append(int(match.group(2)))
    sessions = values["T2_KEYBAG_SESSION"]
    handles = values["T2_KEYBAG_HANDLE"]
    specials = values["T2_KEYBAG_SPECIAL"]
    if (sessions != [1] or len(handles) != 1 or handles[0] <= 0
            or specials != [expected_special]):
        raise EnrollRunnerError("runtime keybag session does not match configuration")
    return sessions[0], handles[0]


def open_bridge(host: str, port: int, interface: str):
    scope_id = socket.if_nametoindex(interface)
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    sock.connect((host, port, 0, scope_id))
    frame_type, body = receive_frame(sock)
    if frame_type != TYPE_HELO:
        sock.close()
        raise EnrollRunnerError(f"expected HELO frame, got type {frame_type}")
    helo = describe(frame_type, body)
    send_helo(sock, int(helo.get("BridgeXPCVersion", 39)))
    version_reply = request(sock, [0])
    if (not isinstance(version_reply, list) or len(version_reply) != 2
            or version_reply[0] != 0):
        sock.close()
        raise EnrollRunnerError(f"getBridgeVersion failed: {version_reply!r}")
    if request(sock, [10, min(version_reply[1], 2)]) != [0]:
        sock.close()
        raise EnrollRunnerError("bridge client-version negotiation failed")
    if request(sock, [1]) != [0, True]:
        sock.close()
        raise EnrollRunnerError("biometric service did not report opened")
    return sock


def reply_bytes(reply: object) -> bytes | None:
    if (isinstance(reply, list) and len(reply) == 2
            and isinstance(reply[1], bytes)):
        return reply[1]
    return None


def warm_gate(sock, user_id: int) -> bytes:
    list_reply, _ = biometric_command(
        sock, 0x42, data=struct.pack("<I", user_id),
        output_capacity=20 * 10)
    if not (isinstance(list_reply, list) and list_reply
            and list_reply[0] == 0):
        raise EnrollRunnerError("identity enumeration failed")
    identities = reply_bytes(list_reply) or b""
    if len(identities) % 20 != 0:
        raise EnrollRunnerError("identity list is not 20-byte records")
    count = len(identities) // 20
    uids = [struct.unpack_from("<I", identities, i * 20)[0]
            for i in range(count)]
    if not 1 <= count <= 4 or any(u != user_id for u in uids):
        raise EnrollRunnerError(
            f"warm gate failed: count={count} leaves no room or wrong UID")
    sks_reply, _ = biometric_command(
        sock, 0x27, data=struct.pack("<I", user_id), output_capacity=4)
    # NOTE: SKS lock-state drifts across sessions (0x10, 0x810, 0x239 all
    # observed with 0x42=1 intact on one warm SEP), so it cannot gate.
    # The 0x42 count is the only stable truth: cold aborts on count 0,
    # full aborts on count 5. SKS is recorded, never decisive.
    sks = reply_bytes(sks_reply)
    summary_sks = sks.hex() if isinstance(sks, bytes) else None
    return identities, summary_sks


def enroll_consumer_factory(host, port, interface, user_id, before_count,
                            event_seconds):
    def consume(external_form: bytes) -> dict[str, object]:
        if not isinstance(external_form, bytes) or len(external_form) != 16:
            raise EnrollRunnerError("authorized external form is invalid")
        # Current-format authorized enroll payload, byte-exact with the
        # proven layout: IIII flags/uid/using_token/token_length (16) +
        # 16-byte ACM external form (16) + 16 reserved-zero bytes +
        # builtin device group u32 (4) + 16 zero bytes = 68 total.
        payload = (struct.pack("<IIII", 0, user_id, 0, 16)
                   + external_form + bytes(16) + struct.pack("<I", 1)
                   + bytes(16))
        summary: dict[str, object] = {
            "dispatch_status": None, "result_seen": False,
            "result_version": None, "result_length": None,
            "observed_kinds": [], "cancel_status": None,
            "identities_before": before_count, "identities_after": None,
        }
        sock = open_bridge(host, port, interface)
        try:
            # Daemon-style session preparation: state reads only, all
            # shapes previously observed status-0 on warm SEP except the
            # last three (recorded, non-gating). No catacomb/save/reset
            # traffic, and never no_catacomb (state-killer on warm SEP).
            prep = []
            for opcode, version, value, data, cap, label in [
                (0x52, 1, 0, b"", 264, "device-list"),
                (0x53, 1, 0, b"", 1, "sensor-readiness"),
                (0x43, 2, 0, b"", 64, "system-protected-config"),
                (0x4C, 1, 0, b"", 1, "xart-available"),
                (0x30, 1, 0, struct.pack("<I", user_id), 1, "enabled-unlock"),
            ]:
                reply, _ = biometric_command(
                    sock, opcode, version=version, value=value,
                    data=data, output_capacity=cap)
                status = reply[0] if (
                    isinstance(reply, list) and reply) else None
                out = reply_bytes(reply)
                prep.append({"label": label, "status": status,
                             "out_len": None if out is None else len(out)})
            summary["session_prep"] = prep
            start_reply, _ = biometric_command(
                sock, ENROLL_OPCODE, version=ENROLL_VERSION, value=0,
                data=payload, output_capacity=0)
            start_status = start_reply[0] if (
                isinstance(start_reply, list) and start_reply) else None
            summary["dispatch_status"] = start_status
            if (start_status != 0 or reply_bytes(start_reply) is not None):
                raise EnrollRunnerError(
                    f"enrollment dispatch refused: status={start_status}; "
                    "no variants attempted")
            print("TOUCH NOW: place the new finger flat on Touch ID.",
                  flush=True)
            kinds: list[str] = []
            deadline = time.monotonic() + event_seconds
            terminal = None
            while time.monotonic() < deadline:
                sock.settimeout(max(0.1, deadline - time.monotonic()))
                try:
                    envelope = receive_envelope(sock)
                except TimeoutError:
                    break
                if envelope[1] is not False:
                    continue
                kind = fork_a.summarize_event(envelope[3])
                event_kind = kind.get("event_kind")
                embedded = kind.get("embedded_type")
                kinds.append(str(event_kind))
                if embedded == "0xe3ff8001":
                    code = kind.get("status_code")
                    if code == READY_ORDINAL:
                        print("TOUCH NOW: place the new finger flat on Touch ID.",
                              flush=True)
                    elif code in PROGRESS_MINIMUMS:
                        print("LIFT, reposition slightly, then touch again.",
                              flush=True)
                elif embedded == "0xe3ff8004":
                    print("LIFT, reposition slightly, then touch again.",
                          flush=True)
                elif event_kind == "match_result":
                    raise EnrollRunnerError(
                        "unexpected match_result during enrollment")
                send_message(sock, [1, True, envelope[2], [0]])
                if embedded == f"0x{RESULT_ORDINAL:08x}":
                    terminal = {
                        "version": kind.get("version"),
                        "data_length": kind.get("data_length"),
                    }
                    summary["result_seen"] = True
                    summary["result_version"] = terminal["version"]
                    summary["result_length"] = terminal["data_length"]
                    break
            summary["observed_kinds"] = kinds
            if terminal is None:
                raise EnrollRunnerError(
                    f"no terminal enroll result in window; kinds={kinds}")
        finally:
            try:
                cancel_reply, _ = biometric_command(sock, 0x0C)
                summary["cancel_status"] = cancel_reply[0] if (
                    isinstance(cancel_reply, list) and cancel_reply) else None
            except Exception:
                summary["cancel_status"] = -1
            try:
                post = reply_bytes(biometric_command(
                    sock, 0x42, data=struct.pack("<I", user_id),
                    output_capacity=20 * 10)[0]) or b""
                after = len(post) // 20 if len(post) % 20 == 0 else -1
                after_uids = [struct.unpack_from("<I", post, i * 20)[0]
                              for i in range(after)] if after > 0 else []
                summary["identities_after"] = after
                summary["delta_ok"] = (
                    after == before_count + 1
                    and all(u == user_id for u in after_uids))
            except Exception:
                summary["identities_after"] = None
                summary["delta_ok"] = False
            sock.close()
            if summary.get("dispatch_status") != 0 or not summary.get("delta_ok", True):
                print("consumer diagnostic: "
                      + json.dumps(summary, sort_keys=True), file=sys.stderr)
        return summary
    return consume


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--interface", required=True)
    parser.add_argument("--event-seconds", type=float, default=60.0)
    parser.add_argument("--confirm-live", default="")
    parser.add_argument("--private-json", default="")
    parser.add_argument(
        "--legacy-context-create", action="store_true",
        help="use ACM context-create 0x01 instead of tracking 0x24: "
        "the external form generation differs and the SEP may only honor "
        "one generation in enroll dispatch (single bounded attempt each)")
    args = parser.parse_args()

    if not LIVE_ENROLL_ENABLED or args.confirm_live != CONFIRM:
        return fail("live enrollment is disabled in source; refusing")
    if not 1.0 <= args.event_seconds <= 60.0:
        return fail("event window must be within 1..60 seconds")
    if os.geteuid() != 0:
        return fail("must run as root")
    private_path = None
    if args.private_json:
        private_path = Path(args.private_json)
        if PRIVATE_ROOT not in private_path.resolve().parents:
            return fail("raw JSON must stay under operator-private storage")
    try:
        user_id, special, mapped_uid = configuration()
        if not caller_is_mapped(mapped_uid):
            raise EnrollRunnerError(
                "caller is not the mapped Linux user via sudo/pkexec")
        session, handle = keybag_runtime(special)
        gate_sock = open_bridge(args.host, args.port, args.interface)
        try:
            gate_identities, gate_sks = warm_gate(gate_sock, user_id)
            before = len(gate_identities) // 20
        finally:
            gate_sock.close()

        def bind_password(context: bytes) -> None:
            completed = subprocess.run(
                [str(AKS_TOOL), "verify-password-acm",
                 str(session), str(handle)],
                input=context, check=False)
            if completed.returncode:
                raise ACMDeviceError("AKS password binding failed")

        with ACMDevice() as device:
            initial, final, enroll_summary = with_authorized_context(
                device, user_id, bind_password,
                enroll_consumer_factory(
                    args.host, args.port, args.interface, user_id,
                    before, args.event_seconds),
                tracking=not args.legacy_context_create)
    except (OSError, ValueError, EnrollRunnerError, ACMDeviceError) as error:
        detail = f"{error}"
        cause = error.__cause__
        while cause is not None:
            detail += f" <= {cause}"
            cause = cause.__cause__
        return fail(detail)
    result = {
        "policy_preflight_type": initial.requirement_type,
        "policy_satisfied": final.satisfied,
        "warm_gate_sks": gate_sks,
        "enrollment": enroll_summary,
    }
    if private_path is not None:
        private_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
