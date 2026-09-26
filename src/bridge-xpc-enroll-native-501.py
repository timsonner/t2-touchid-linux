#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""One first-finger enroll against the Linux-owned user-501 bag.

The saved creation reference is type-5 data on an input context. A second
context for the same user is the enroll token. Operation 0x21 option 0x100
names both forms and reload handle 2. The zero-group 68-byte start is sent
only after that authorization returns status 0, and only while both
contexts are still live. A non-zero start is cancelled. No second create.
"""

from __future__ import annotations

import importlib.util
import json
import os
import struct
import sys
import time
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

CONFIRM = "I_UNDERSTAND_THIS_ENROLLS_ONE_NEW_FINGERPRINT"
HANDLE = 2
SESSION = 1
USER_ID = 501
OPTIONS = 0x100
ROOT = Path("/var/lib/t2-touchid")
FORM_PATH = ROOT / "native-501.form"
JOURNAL = ROOT / "native-501-enroll.json"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SRC / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


export = _load("export_c3", "bridge-aks-export-c3.py")
enroll = _load("enroll_helpers", "bridge-xpc-authorized-enroll.py")
acm = _load("acm_device", "t2_acm_device.py")
protocol = _load("acm_protocol", "t2_acm_protocol.py")
wire = _load("bridge_wire", "t2_bridge_wire.py")


def status_of(reply: object) -> int | None:
    if isinstance(reply, list) and reply and isinstance(reply[0], int):
        return reply[0]
    return None


def verify_body(handle: int, input_form: bytes, target_form: bytes) -> bytearray:
    body = bytearray(64)
    struct.pack_into("<IQII", body, 0, 1, SESSION, handle, 16)
    body[20:36] = input_form
    struct.pack_into("<I", body, 36, 16)
    body[40:56] = target_form
    struct.pack_into("<Q", body, 56, OPTIONS)
    return body


def main() -> int:
    if "--confirm-live" not in sys.argv or CONFIRM not in sys.argv:
        print("enroll-native-501: live probe is disabled; refusing", file=sys.stderr)
        return 1
    form = bytearray(FORM_PATH.read_bytes())
    if len(form) != 16:
        print("enroll-native-501: saved form length is not 16", file=sys.stderr)
        return 1
    journal: dict[str, object] = {
        "authorize_status": None,
        "prep": [],
        "dispatch_status": None,
        "continues": [],
        "identities_before": None,
        "identities_after": None,
        "cancel_status": None,
        "outcome": "unknown",
    }
    handles = []
    try:
        port = int(ROOT.joinpath("biometric-port").read_text().strip())
        conf = dict(
            line.split("=", 1)
            for line in Path("/etc/t2-touchid.conf").read_text().splitlines()
            if line and not line.startswith("#") and "=" in line
        )
        sock = enroll.open_bridge(
            conf["T2_TOUCHID_HOST"], port, conf["T2_TOUCHID_INTERFACE"])
        try:
            before_reply, _ = wire.biometric_command(
                sock, 0x42, data=struct.pack("<I", USER_ID), output_capacity=200)
            before = enroll.reply_bytes(before_reply) or b""
            journal["identities_before"] = (
                0 if wire.is_biometric_nil_output(
                    before_reply[1] if isinstance(before_reply, list)
                    and len(before_reply) > 1 else None)
                else len(before) // 20)
            for opcode, version, data, cap, label in [
                (0x52, 1, b"", 264, "device-list"),
                (0x53, 1, b"", 1, "sensor-readiness"),
                (0x43, 2, b"", 64, "system-protected-config"),
                (0x4C, 1, b"", 1, "xart-available"),
                (0x30, 1, struct.pack("<I", USER_ID), 1, "enabled-unlock"),
            ]:
                reply, _ = wire.biometric_command(
                    sock, opcode, version=version, data=data, output_capacity=cap)
                code = status_of(reply)
                journal["prep"].append({"label": label, "status": code})
                if code != 0:
                    journal["outcome"] = f"prep-refused:{label}"
                    return 0
            with acm.ACMDevice() as device:
                created = device.exchange(
                    protocol.build_create(user_id=USER_ID, tracking=True), 21)
                input_handle = protocol.parse_create_response(created, tracking=True)
                handles.append(input_handle)
                acm.set_identity_secret(device, input_handle, form)
                input_form = acm.externalize_context(device, input_handle)
                created = device.exchange(
                    protocol.build_create(user_id=USER_ID, tracking=True), 21)
                target_handle = protocol.parse_create_response(created, tracking=True)
                handles.append(target_handle)
                target_form = acm.externalize_context(device, target_handle)
                body = verify_body(HANDLE, input_form, target_form)
                auth_status, response = export.lab_dispatch(0x21, body)
                export._wipe(body)
                export._wipe(response)
                journal["authorize_status"] = auth_status
                if auth_status != 0:
                    journal["outcome"] = "authorize-refused"
                    return 0
                payload = (struct.pack("<IIII", 0, USER_ID, 0, 16)
                           + target_form + bytes(36))
                start_reply, _ = wire.biometric_command(
                    sock, 0x03, version=2, data=payload, output_capacity=0)
                journal["dispatch_status"] = status_of(start_reply)
                if journal["dispatch_status"] != 0:
                    journal["outcome"] = "enroll-refused"
                    return 0
                print("ENROLL OPEN. Place a finger flat on Touch ID.", flush=True)
                for index in range(1, 9):
                    if index > 1:
                        print(f"Lift, then place the finger again ({index}/8).",
                              flush=True)
                        time.sleep(1.5)
                    cont_reply, cont_events = wire.biometric_command(
                        sock, 0x0E, version=1, data=b"", output_capacity=0)
                    journal["continues"].append({
                        "n": index,
                        "status": status_of(cont_reply),
                        "events": len(cont_events),
                    })
                    if status_of(cont_reply) != 0:
                        journal["outcome"] = f"continue-refused:{index}"
                        return 0
                print("Dance complete. Lift the finger.", flush=True)
                after_reply, _ = wire.biometric_command(
                    sock, 0x42, data=struct.pack("<I", USER_ID),
                    output_capacity=200)
                after = enroll.reply_bytes(after_reply) or b""
                journal["identities_after"] = (
                    0 if wire.is_biometric_nil_output(
                        after_reply[1] if isinstance(after_reply, list)
                        and len(after_reply) > 1 else None)
                    else len(after) // 20)
                journal["outcome"] = (
                    "enrolled-pending-reboot-proof"
                    if journal["identities_after"] == 1 else "count-not-one")
                return 0
        finally:
            try:
                cancel_reply, _ = wire.biometric_command(sock, 0x0C)
                journal["cancel_status"] = status_of(cancel_reply)
            except Exception:
                journal["cancel_status"] = -1
            sock.close()
    except Exception as error:
        journal["outcome"] = f"halt:{type(error).__name__}"
        print(f"halt:{type(error).__name__}", file=sys.stderr)
        return 1
    finally:
        form[:] = b"\x00" * len(form)
        try:
            with acm.ACMDevice() as device:
                for handle in reversed(handles):
                    device.exchange(protocol.build_delete(handle), 0)
        except Exception:
            journal["context_cleanup"] = "failed"
        JOURNAL.write_text(json.dumps(journal, indent=2) + "\n")
        os.chmod(JOURNAL, 0o600)
        print(json.dumps(journal, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
