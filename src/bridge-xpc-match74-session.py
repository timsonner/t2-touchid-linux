#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""DRAFT (staged, not yet run): session-binding Mesa-74 replication probe.

Status: design only. LIVE_74SESSION_ENABLED defaults False; even enabled,
this refuses unless ALL hold:

- warm SEP: BridgeXPC 0x42 holds >=2 identities for the configured UID
  (post-Fork-B count; SKS informational only: 0x10/0x11/0x810/0x239 observed);
- full-inventory repeat_equal true on this boot before the window
  (operator verifies separately; script re-checks 0x42 count in-session);
- explicit --stage s1|s2 and --confirm-live.

Rationale: Fork B mine (MATCH74_SESSION_BINDING_2026-09-13.md) kills
credential-in-payload (zero non-empty 74 in 8964 lines). Working unlock is
always empty-74 after session:

  verdict framing: 48(0) -> 84(20) -> 39(4) -> 84(20) -> 12(0) -> 74(0),
    all ver=1 val=0;
  prelude ~3s earlier, both unlocks:
    48(0), 39(4), 46(4), 4(68), 46(4), 46(4);
  unlock #1 only: doubled verdict-48 + extra prelude 58(4B).

Linux gap (2026-09-16, verified read-only, 0x42=2 preserved):
- our prelude sent 48+uid(4B); macOS sends 48-empty. Empty-48 standalone
  also returns status 0 + 1B 0x01 here, so the deviation is benign for
  status but fixed to capture-exact in both stages;
- 39-uid -> 0 + 4B (0x10); 58-uid -> 0 + 33B (catacomb_hash shape);
  46-uid needs cap>=32 (-> 0 + 32B; cap4 -> 265, cap0 -> 258);
- 4-bare68 stand-in (Fork-A 68B options: flags0/uid/60-zero, ver1 val0,
  cap0) in cluster position returns status 0 with no start-events, and
  the trailing 46s still return 0. Full early cluster replays status-0
  with 0x42=2 preserved (no 74 attempted in that check).

Stages (one shot each, separate verified-stable baselines, never combined):
- s1: capture-exact verdict framing only (48-empty fix) + 74 empty.
  RUN 2026-09-16: prelude all 0, 74 -> 258. 48 shape is not the gate. CLOSED.
- s2: full session: early cluster (48e,39,46,4-standin,46,46) then
  verdict framing then 74 empty.
  RUN 2026-09-16: clusters all 0, 74 -> nil halt-state (not 258/22).
  Read: the 4-standin opened a session still live at 74 dispatch.
  parked the open-session hypothesis; do not repeat s2.
- s2b: like s2 but with explicit 12-cancel + drain + 3 s gap after the
  early cluster (mirrors the macOS ~3 s prelude/verdict gap) before the
  verdict framing + 74 empty.
  RUN 2026-09-16: sep-cancel 0, 3 drained events, prelude all 0,
  74 -> clean 258. Full session-shape closed as the gate; the 4-standin
  is now suspect for S2's nil (open session breaks 74 dispatch).
- s3: 00:00-style no-4 session (UNLOCK_VERDICTS_2026-09-16: prelude
  varies, 4 not mandatory): 46 -> 48-empty -> 46, then a 3 s zero-Mesa
  gap (sleep in-session, no cancel — nothing opened), then corrected
  verdict order 48 -> 84 -> 39 -> 12 -> 84 -> 74 (12 before the second
  84 per the 00:07 canonical), empty 74. STAGED, not yet run.
  258 rules the prelude out entirely; 0 opens the first real touch
  window; 22 reopens shape, targeted.
- s5: HELO-identity probe (SESSION_IDENTITY_AUDIT_2026-09-20): swapped
  HELO values only (ProcessName -> biometrickitd, OSBuild -> 24G830,
  keys preserved) -> standard init -> S1 capture-exact framing
  48 -> 84 -> 39 -> 84 -> 12 -> 74 (all v1/val0, empty 74). Isolates
  the HELO variable against S1 (which refused 258 with stock HELO).
  258 closes H1 and promotes H2; non-258 reopens the track.

Deliberate limits: single 74 dispatch per run, 60 s event cap, cancel
always, post-0x42==2 required (halt all live work otherwise). Any 74
start status other than 258/22 halts with no further shots. No enroll /
load / reset / delete / EP7 traffic. match_result contents never decoded:
only (event_kind, ordinal, data_length, matched) recorded. Per-window raw
JSON opt-in under operator-private paths only. No module load needed
(BridgeXPC/NCM userspace); NEVER insmod on warm SEP with default params.
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


def _load_fork_a():
    path = LOCAL_SOURCE / "bridge-xpc-probe.py"
    spec = _importlib_util.spec_from_file_location(
        "bridge_xpc_match74_session_fork_a", path)
    assert spec and spec.loader
    module = _importlib_util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


fork_a = _load_fork_a()

LIVE_74SESSION_ENABLED = False
CONFIRM = "I_UNDERSTAND_THIS_STARTS_ONE_SESSION74_WINDOW"
MATCH74_OPCODE = 74
PRIVATE_ROOT = Path("/home/tim/Private")


def fail(message: str) -> int:
    print(f"match74-session: {message}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--interface", required=True)
    parser.add_argument("--macos-user-id", required=True, type=int)
    parser.add_argument("--stage", required=True, choices=("s1", "s2", "s2b", "s3", "s5"))
    parser.add_argument("--match-seconds", type=float, default=30.0)
    parser.add_argument("--confirm-live", default="")
    parser.add_argument("--private-json", default="")
    args = parser.parse_args()

    if not LIVE_74SESSION_ENABLED or args.confirm_live != CONFIRM:
        return fail("live session-74 probe is disabled in source; refusing")
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
        "opcode": MATCH74_OPCODE,
        "stage": args.stage,
        "warm_gate": False,
        "early_cluster": [],
        "prelude": [],
        "match_start_status": None,
        "match_result_seen": False,
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
        if args.stage == "s5":
            send_helo(sock, int(helo.get("BridgeXPCVersion", 39)),
                      process_name="biometrickitd", os_build="24G830")
            summary["helo_sent"] = {"ProcessName": "biometrickitd",
                                    "OSBuild": "24G830"}
        else:
            send_helo(sock, int(helo.get("BridgeXPCVersion", 39)))
            summary["helo_sent"] = {"ProcessName": "t2-touchid-probe",
                                    "OSBuild": "Linux"}
        version_reply = request(sock, [0])
        if (not isinstance(version_reply, list)
                or len(version_reply) != 2 or version_reply[0] != 0):
            return fail(f"getBridgeVersion failed: {version_reply!r}")
        if request(sock, [10, min(version_reply[1], 2)]) != [0]:
            return fail("bridge client-version negotiation failed")
        if request(sock, [1]) != [0, True]:
            return fail("biometric service did not report opened")

        # Warm gate: 0x42 count>=2 for this UID (post-Fork-B). SKS recorded,
        # never decisive (0x10/0x11/0x810/0x239 all seen warm with 0x42 intact).
        list_reply, _ = biometric_command(
            sock, 0x42, data=struct.pack("<I", uid),
            output_capacity=20 * 10)
        identities = (list_reply[1] if isinstance(list_reply, list)
                      and len(list_reply) == 2
                      and isinstance(list_reply[1], bytes) else b"")
        count = len(identities) // 20 if len(identities) % 20 == 0 else -1
        uids = ([struct.unpack_from("<I", identities, i * 20)[0]
                 for i in range(count)] if count > 0 else [])
        sks_reply, _ = biometric_command(
            sock, 0x27, data=struct.pack("<I", uid), output_capacity=4)
        sks = (sks_reply[1].hex()
               if isinstance(sks_reply, list) and len(sks_reply) == 2
               and isinstance(sks_reply[1], bytes)
               and len(sks_reply[1]) == 4 else None)
        summary["warm_gate_detail"] = {"identity_count": count, "sks": sks}
        if count < 2 or any(u != uid for u in uids):
            return fail("warm gate failed: need >=2 identities for this UID")
        summary["warm_gate"] = True

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

        def close_session() -> None:
            """Best-effort cancel + warm-preserve check for abort paths."""
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
                summary["identities_preserved"] = post == identities
            except Exception:
                summary["identities_preserved"] = False

        # S2/S2b: early prelude cluster, capture order. The 4-standin is
        # Fork-A bare 68B options (flags 0, uid, 60 zero) — our construction
        # since token contents are never logged by design.
        if args.stage in ("s2", "s2b"):
            token_standin = struct.pack("<II60x", 0, uid)
            early = [
                (0x30, 1, 0, b"", 1, "early-48-empty"),
                (0x27, 1, 0, struct.pack("<I", uid), 4, "early-39"),
                (0x2E, 1, 0, struct.pack("<I", uid), 33, "early-46-a"),
                (0x04, 1, 0, token_standin, 0, "early-4-standin68"),
                (0x2E, 1, 0, struct.pack("<I", uid), 33, "early-46-b"),
                (0x2E, 1, 0, struct.pack("<I", uid), 33, "early-46-c"),
            ]
            for op, ver, val, data, cap, label in early:
                status = run_step(op, ver, val, data, cap, label,
                                  summary["early_cluster"])
                if status != 0:
                    close_session()
                    print(json.dumps(summary, indent=2, sort_keys=True))
                    return fail(f"early cluster deviated at {label}: "
                                f"status={status}")
            if args.stage == "s2b":
                # Separation macOS shows (~3 s gap): close the 4-session,
                # drain stragglers, then idle before the verdict framing.
                cancel_reply, cancel_events = biometric_command(sock, 0x0C)
                summary["s2b_sep_cancel"] = (cancel_reply[0] if isinstance(
                    cancel_reply, list) and cancel_reply else None)
                drained = len(cancel_events)
                sock.settimeout(2.0)
                try:
                    while True:
                        envelope = receive_envelope(sock)
                        if envelope[1] is False:
                            drained += 1
                            send_message(sock, [1, True, envelope[2], [0]])
                except TimeoutError:
                    pass
                finally:
                    sock.settimeout(5.0)
                summary["s2b_drained_events"] = drained
                time.sleep(3.0)

        # S3: 00:00-style no-4 session (UNLOCK_VERDICTS_2026-09-16). No
        # match-type command opens here, so no cancel — just the zero-Mesa
        # gap macOS shows, slept in-session.
        if args.stage == "s3":
            early = [
                (0x2E, 1, 0, struct.pack("<I", uid), 33, "early-46-a"),
                (0x30, 1, 0, b"", 1, "early-48-empty"),
                (0x2E, 1, 0, struct.pack("<I", uid), 33, "early-46-b"),
            ]
            for op, ver, val, data, cap, label in early:
                status = run_step(op, ver, val, data, cap, label,
                                  summary["early_cluster"])
                if status != 0:
                    close_session()
                    print(json.dumps(summary, indent=2, sort_keys=True))
                    return fail(f"early cluster deviated at {label}: "
                                f"status={status}")
            time.sleep(3.0)

        # Verdict framing, capture-exact (48 EMPTY — the fix vs 48+uid).
        # S3 uses the 00:07 canonical order (12 before the second 84);
        # older stages keep their as-run order as historical record.
        if args.stage == "s3":
            prelude = [
                (0x30, 1, 0, b"", 1, "getEnabledForUnlock-empty"),
                (0x54, 1, 0, struct.pack("<I", 2) + bytes(16), 83,
                 "accessory-B"),
                (0x27, 1, 0, struct.pack("<I", uid), 4, "sks-lock"),
                (0x0C, 1, 0, b"", 0, "cancel-idle"),
                (0x54, 1, 0, struct.pack("<I", 2) + bytes(16), 83,
                 "accessory-B"),
            ]
        else:
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
            status = run_step(op, ver, val, data, cap, label,
                              summary["prelude"])
            if status != 0:
                close_session()
                print(json.dumps(summary, indent=2, sort_keys=True))
                return fail(f"prelude deviated at {label}: status={status}")

        summary["match_input"] = "empty-session"
        try:
            match_reply, events = biometric_command(
                sock, MATCH74_OPCODE, data=b"")
        except Exception as error:
            summary["match_transport_error"] = f"{type(error).__name__}"
            close_session()
            print(json.dumps(summary, indent=2, sort_keys=True))
            return fail(f"74 halt-state: transport {type(error).__name__}; "
                        "analyze, no further shots")
        start_status = (match_reply[0] if isinstance(match_reply, list)
                        and match_reply else None)
        summary["match_start_status"] = start_status
        if start_status != 0:
            close_session()
            print(json.dumps(summary, indent=2, sort_keys=True))
            # 258/22 are the only continue-states; anything else halts.
            if start_status not in (258, 22, 0xE00002C2):
                return fail(f"74 halt-state: status={start_status}; "
                            "analyze, no further shots")
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
                kind = fork_a.summarize_event(
                    envelope[3], enrolled_records, expected_user_id=uid)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
