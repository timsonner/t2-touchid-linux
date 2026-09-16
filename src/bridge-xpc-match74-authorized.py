#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""DRAFT (staged, not yet run): one authorized-context Mesa-74 match window.

Status: design only. LIVE_74AUTH_ENABLED defaults False; even enabled,
this refuses unless ALL of the following hold:

- warm SEP: BridgeXPC 0x42 holds >=1 identity for the configured UID;
- a fresh ACM tracking context creates, shows the type-1 passcode
  requirement, binds the operator password via t2-aks-tool, and reaches
  policy-1007 SATISFIED — all inside with_authorized_context, with
  mandatory context cleanup before return;
- the Sequoia prelude (48 -> 84 -> 39 -> 84 -> 12, all status 0)
  completes without deviation.

Rationale: plain empty-74 (window 9, 2026-09-13) and Fork-A 68 B 74
(windows 7-8) all refuse at dispatch with 258 after a clean prelude
(MATCH_FORKA_2026-09-13.md, NEXT_STEPS.md). The 74 gate is therefore not
input-shape. The one proven credential upgrade on this Air is the
password-bound authorized ACM context (policy 1007 SATISFIED, first
reached 2026-09-13 via EP7 selective path). This probe asks whether 74
opens with that ambient authorization live, using capture-exact empty
input (ver 1, val 0, 0 B), exactly once. A nonzero start status ends the
run: no payload variants, no sprays, no enroll/load/reset/delete/EP7
traffic of any kind.

S4 update (UNLOCK_VERDICTS_2026-09-16, S3): the default prelude below is
the as-run 2026-09-13 shape (48+uid deviation, proven benign by S1).
Pass --exact-session for the 00:00-style no-4 session instead —
46 -> 48-empty -> 46, 3 s zero-Mesa gap, corrected verdict order
48 -> 84 -> 39 -> 12 -> 84 — with the authorized context live. That is
the last untested authorized x session combination. Honest odds: low
(ambient auth already 258 against the old prelude; S3 already 258
without auth). One window; any non-258/22 halts everything.

Deliberate limits: single attempt, 60 s event cap, cancel always,
post-0x42 preserved check. match_result contents are never decoded:
only (event_kind, ordinal, data_length, boolean matched) is recorded.
Per-window raw JSON is opt-in and restricted to operator-private paths.
Password handling: operator terminal only via t2-aks-tool, never stored,
never logged, no disk/git/log copies.

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

LIVE_74AUTH_ENABLED = False
CONFIRM = "I_UNDERSTAND_THIS_STARTS_ONE_AUTHORIZED_MATCH74_WINDOW"
CONFIG = Path("/etc/t2-touchid.conf")
KEYBAG_STATE = Path("/run/t2-touchid/keybag.env")
AKS_TOOL = Path("/usr/local/sbin/t2-aks-tool")
MATCH74_OPCODE = 74
PRIVATE_ROOT = Path("/home/tim/Private")

WARM_SKS_STATES = (0x10, 0x810, 0x239)


def _load_helpers():
    path = LOCAL_SOURCE / "bridge-xpc-authorized-enroll.py"
    spec = _importlib_util.spec_from_file_location(
        "bridge_xpc_match74_authorized_enroll", path)
    assert spec and spec.loader
    module = _importlib_util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fail(message: str) -> int:
    print(f"match74-authorized: {message}", file=sys.stderr)
    return 1


def open_bridge(host: str, port: int, interface: str):
    scope_id = socket.if_nametoindex(interface)
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    sock.connect((host, port, 0, scope_id))
    frame_type, body = receive_frame(sock)
    if frame_type != TYPE_HELO:
        sock.close()
        raise RuntimeError(f"expected HELO frame, got type {frame_type}")
    helo = describe(frame_type, body)
    send_helo(sock, int(helo.get("BridgeXPCVersion", 39)))
    version_reply = request(sock, [0])
    if (not isinstance(version_reply, list) or len(version_reply) != 2
            or version_reply[0] != 0):
        sock.close()
        raise RuntimeError(f"getBridgeVersion failed: {version_reply!r}")
    if request(sock, [10, min(version_reply[1], 2)]) != [0]:
        sock.close()
        raise RuntimeError("bridge client-version negotiation failed")
    if request(sock, [1]) != [0, True]:
        sock.close()
        raise RuntimeError("biometric service did not report opened")
    return sock


def reply_bytes(reply: object) -> bytes | None:
    if (isinstance(reply, list) and len(reply) == 2
            and isinstance(reply[1], bytes)):
        return reply[1]
    return None


def match74_consumer_factory(host, port, interface, user_id,
                             fork_a, match_seconds, exact_session=False):
    def consume(external_form: bytes) -> dict[str, object]:
        if not isinstance(external_form, bytes) or len(external_form) != 16:
            raise RuntimeError("authorized external form is invalid")
        # The form is ambient-only by Fork-B verdict (74 carries no
        # credential payload): validated, never placed on the wire.
        summary: dict[str, object] = {
            "opcode": MATCH74_OPCODE,
            "match_input": "empty-authorized",
            "warm_gate": False,
            "prelude": [],
            "match_start_status": None,
            "match_result_seen": False,
            "observed_events": [],
            "cancel_status": None,
            "identities_preserved": False,
        }
        sock = open_bridge(host, port, interface)

        class _ConsumerAbort(RuntimeError):
            """Expected halt (gate/deviation/refusal): already diagnosed."""

        def abort(message: str) -> None:
            summary["consumer_error"] = message
            print("consumer diagnostic: "
                  + json.dumps(summary, sort_keys=True), file=sys.stderr)
            raise _ConsumerAbort(message)

        try:
            list_reply, _ = biometric_command(
                sock, 0x42, data=struct.pack("<I", user_id),
                output_capacity=20 * 10)
            identities = reply_bytes(list_reply) or b""
            count = (len(identities) // 20
                     if len(identities) % 20 == 0 else -1)
            uids = ([struct.unpack_from("<I", identities, i * 20)[0]
                     for i in range(count)] if count > 0 else [])
            sks_reply, _ = biometric_command(
                sock, 0x27, data=struct.pack("<I", user_id),
                output_capacity=4)
            sks = reply_bytes(sks_reply)
            sks_value = (struct.unpack("<I", sks)[0]
                         if isinstance(sks, bytes) and len(sks) == 4
                         else None)
            summary["warm_gate_detail"] = {
                "identity_count": count, "sks": sks.hex() if sks else None}
            if count < 1 or any(u != user_id for u in uids):
                abort("warm gate failed: no trusted identity for this UID")
            # SKS is recorded, never decisive: 0x10, 0x810 and 0x239 have
            # all been observed with 0x42 intact on one warm SEP, so an
            # unknown value must not abort the run — it is reported
            # alongside the dispatch verdict instead.
            summary["warm_gate"] = True

            if exact_session:
                # S4: 00:00-style no-4 session. Nothing match-type opens
                # here, so no cancel — the zero-Mesa gap macOS shows.
                for opcode, version, value, data, cap, label in [
                    (0x2E, 1, 0, struct.pack("<I", user_id), 33,
                     "early-46-a"),
                    (0x30, 1, 0, b"", 1, "early-48-empty"),
                    (0x2E, 1, 0, struct.pack("<I", user_id), 33,
                     "early-46-b"),
                ]:
                    reply, _ = biometric_command(
                        sock, opcode, version=version, value=value,
                        data=data, output_capacity=cap)
                    status = reply[0] if (
                        isinstance(reply, list) and reply) else None
                    out = reply_bytes(reply)
                    summary["prelude"].append({
                        "label": label, "opcode": opcode, "status": status,
                        "out_len": None if out is None else len(out)})
                    if status != 0:
                        abort(f"early cluster deviated at {label}: "
                              f"status={status}")
                time.sleep(3.0)
                summary["session"] = "s3-exact-no4"
            else:
                summary["session"] = "legacy-48-uid"

            prelude_steps = [
                (0x30, 1, 0, b"" if exact_session else struct.pack(
                    "<I", user_id), 1, "getEnabledForUnlock"),
                (0x54, 1, 0, struct.pack("<I", 2) + bytes(16), 83,
                 "accessory-B"),
                (0x27, 1, 0, struct.pack("<I", user_id), 4, "sks-lock"),
            ]
            if exact_session:
                # 00:07 canonical: 12 before the second 84.
                prelude_steps.append(
                    (0x0C, 1, 0, b"", 0, "cancel-idle"))
            prelude_steps.append(
                (0x54, 1, 0, struct.pack("<I", 2) + bytes(16), 83,
                 "accessory-B"))
            if not exact_session:
                prelude_steps.append(
                    (0x0C, 1, 0, b"", 0, "cancel-idle"))
            for opcode, version, value, data, cap, label in prelude_steps:
                reply, _ = biometric_command(
                    sock, opcode, version=version, value=value,
                    data=data, output_capacity=cap)
                status = reply[0] if (
                    isinstance(reply, list) and reply) else None
                out = reply_bytes(reply)
                summary["prelude"].append({
                    "label": label, "opcode": opcode, "status": status,
                    "out_len": None if out is None else len(out)})
                if status != 0:
                    abort(f"prelude deviated at {label}: status={status}")

            match_reply, _ = biometric_command(
                sock, MATCH74_OPCODE, data=b"")
            start_status = match_reply[0] if (
                isinstance(match_reply, list) and match_reply) else None
            summary["match_start_status"] = start_status
            if start_status != 0:
                abort(f"74 did not start: status={start_status}; "
                      "no variants attempted")
            print("TOUCH NOW: place the enrolled finger flat on Touch ID.",
                  flush=True)
            enrolled_records = tuple(
                identities[i * 20:(i + 1) * 20] for i in range(count))
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
                        envelope[3], enrolled_records,
                        expected_user_id=user_id)
                    observed.append({
                        "event_kind": kind.get("event_kind"),
                        "ordinal": kind.get("ordinal"),
                        "data_length": kind.get("data_length"),
                        "matched": kind.get("matched"),
                    })
                    send_message(sock, [1, True, envelope[2], [0]])
                    if kind.get("event_kind") == "match_result":
                        summary["match_result_seen"] = True
                        break
            summary["observed_events"] = observed
        except _ConsumerAbort:
            raise
        except BaseException as error:
            # Unexpected transport/codec failure (e.g. peer closed on 74):
            # dump the partial summary so the window is never a blank.
            summary["consumer_exception"] = type(error).__name__
            print("consumer diagnostic: "
                  + json.dumps(summary, sort_keys=True), file=sys.stderr)
            raise
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
                    output_capacity=20 * 10)[0])
                summary["identities_preserved"] = post == identities
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
    parser.add_argument("--match-seconds", type=float, default=30.0)
    parser.add_argument(
        "--exact-session", action="store_true",
        help="S4: 00:00-style no-4 session (46/48/46 + gap, 12 before "
        "second 84) with the authorized context live. Default re-runs "
        "the as-run 2026-09-13 shape.")
    parser.add_argument("--confirm-live", default="")
    parser.add_argument("--private-json", default="")
    args = parser.parse_args()

    if not LIVE_74AUTH_ENABLED or args.confirm_live != CONFIRM:
        return fail("live authorized-74 probe is disabled in source; refusing")
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
    fork_a = helpers.fork_a
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
                match74_consumer_factory(
                    args.host, args.port, args.interface, user_id,
                    fork_a, args.match_seconds,
                    exact_session=args.exact_session),
                tracking=True)
    except (OSError, ValueError, ACMDeviceError, RuntimeError) as error:
        return fail(f"{error}")
    result = {
        "policy_preflight_type": initial.requirement_type,
        "policy_satisfied": final.satisfied,
        "authorized_74": match_summary,
    }
    if private_path is not None:
        private_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
