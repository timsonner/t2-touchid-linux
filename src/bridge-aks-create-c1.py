#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""DRAFT (staged, not yet run): C1 keybag-identity create-only probe.

Status: design only. LIVE_C1_ENABLED defaults False; even enabled,
this refuses unless ALL of the following hold:

- warm SEP: /dev/t2-sep-lab present with AKS lab available, and
  /dev/t2-acm present for the ACM form ceremony;
- re-established EP7 keybag session (/run/t2-touchid/keybag.env)
  for the ACM password bind (the created bag itself needs nothing
  pre-existing);
- explicit --confirm-live, with intent journaled pre-dispatch to a
  REQUIRED operator-private path (request-sha256 + version only).

Construction (ported from t2touch's proven MBP16,1 native path,
same GPL family — `AKSIdentityCreateV5Request` + minimal native
profile): endpoint-7 operation 0x01, v5 body
(version=5, session-u64, internal_flags=0x4100,
effective_handle=-1) + blobs (item1 = fresh 16 B ACM external form
from an operator-password-bound tracking context with mandatory
cleanup, item2/item3 empty, fresh random root-owned account UUID,
original_flags=6, scalar2=0, optional_data empty).

Body (create-only, additive by construction): journal intent ->
fresh ACM form -> build v5 body -> single lab-AKS dispatch ->
parse (version, live_handle, KEK length) -> WIPE every secret
buffer (body, response, form) -> best-effort bag-UUID readback of
the live handle (non-fatal if the allowlist refuses; C1b material)
-> journal outcome. NO bind, NO delete, NO APFS/OD side effects,
no KEK persistence anywhere, no secret bytes on stdout/logs/disk.

Response handling mirrors their `inspect_mutable` discipline:
lengths/statuses/handles only; the KEK is measured, never copied
out. A new bag handle touches no template, no macOS bag, no
identity — worst case is an orphan handle, documented and left
alone.

Version fallback (v4, per-firmware selection in their tree) is a
separate C2 window, never combined here. Any transport error, any
refusal other than a clean SEP status, or any parse failure halts
with buffers wiped and no replay.
"""

from __future__ import annotations

import argparse
import ctypes
import fcntl
import hashlib
import importlib.util as _importlib_util
import json
import os
import struct
import subprocess
import sys
import uuid
from pathlib import Path

LOCAL_SOURCE = Path(__file__).resolve().parent
if str(LOCAL_SOURCE) not in sys.path:
    sys.path.insert(0, str(LOCAL_SOURCE))

from t2_acm_device import (  # noqa: E402
    ACMDevice,
    ACMDeviceError,
    with_authorized_context,
)

LIVE_C1_ENABLED = False
CONFIRM = "I_UNDERSTAND_THIS_CREATES_ONE_KEYBAG_IDENTITY"
AKS_TOOL = Path("/usr/local/sbin/t2-aks-tool")
LAB_DEVICE = Path("/dev/t2-sep-lab")
ACM_DEVICE = Path("/dev/t2-acm")
CREATE_OP = 0x01
CREATE_VERSION = 5
INTERNAL_FLAGS = 0x4100
ORIGINAL_FLAGS = 6
PRIVATE_ROOT = Path("/home/tim/Private")

# struct t2_sep_lab_ioc_aks, 64 bytes native-packed (see
# src/t2_sep_transport_uapi.h).
_LAB_AKS_FORMAT = "<BBBBB3sIIIIQQb3s4i i".replace(" ", "")
_LAB_IOC_MAGIC = 0xA8
_LAB_IOC_NR = 4


def _lab_ioc_aks() -> int:
    size = struct.calcsize(_LAB_AKS_FORMAT)
    assert size == 64, f"lab AKS struct is {size} bytes, want 64"
    direction = 3  # _IOWR: read|write
    return (direction << 30) | (size << 16) | (_LAB_IOC_MAGIC << 8) | _LAB_IOC_NR


T2_SEP_LAB_IOC_AKS = _lab_ioc_aks()


def _load_helpers():
    path = LOCAL_SOURCE / "bridge-xpc-authorized-enroll.py"
    spec = _importlib_util.spec_from_file_location(
        "bridge_aks_create_c1_helpers", path)
    assert spec and spec.loader
    module = _importlib_util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fail(message: str) -> int:
    print(f"create-c1: {message}", file=sys.stderr)
    return 1


def _blob(value: bytes) -> bytes:
    return struct.pack("<I", len(value)) + value + b"\x00" * (-len(value) & 3)


def build_v5_body(session: int, form: bytes, account_uuid: bytes) -> bytearray:
    if len(form) != 16 or len(account_uuid) != 16 or not any(account_uuid):
        raise ValueError("create inputs are invalid")
    body = bytearray()
    body += struct.pack("<IQIi", CREATE_VERSION, session, INTERNAL_FLAGS, -1)
    body += _blob(form)
    body += _blob(b"")
    body += _blob(account_uuid)
    body += _blob(b"")
    body += struct.pack("<QQ", ORIGINAL_FLAGS, 0)
    body += _blob(b"")
    return body


def _wipe(*buffers: bytearray) -> None:
    for buffer in buffers:
        if isinstance(buffer, bytearray):
            ctypes.memset(ctypes.addressof(
                (ctypes.c_ubyte * len(buffer)).from_buffer(buffer)),
                0, len(buffer))


def lab_create(body: bytearray) -> tuple[int, int, int]:
    """Dispatch EP7 op 0x01; return (sep_status, live_handle, kek_length)."""
    response = bytearray(4096)
    req_buf = (ctypes.c_ubyte * len(body)).from_buffer(body)
    resp_buf = (ctypes.c_ubyte * len(response)).from_buffer(response)
    args = struct.pack(
        _LAB_AKS_FORMAT,
        CREATE_OP, 2, 0, 0, 0, b"\x00\x00\x00",
        30000, len(body), len(response), 0,
        ctypes.addressof(req_buf), ctypes.addressof(resp_buf),
        0, b"\x00\x00\x00", 0, 0, 0, 0, 0,
    )
    args_buf = bytearray(args)
    fd = os.open(str(LAB_DEVICE), os.O_RDWR)
    try:
        fcntl.ioctl(fd, T2_SEP_LAB_IOC_AKS, args_buf)
    finally:
        os.close(fd)
    (op, ver, _, _, _, _, timeout, body_len, resp_cap, resp_len,
     _req, _resp, sep_status, _, rw0, rw1, rw2, rw3, result) = struct.unpack(
        _LAB_AKS_FORMAT, bytes(args_buf))
    if result != 0:
        raise RuntimeError(f"lab ioctl failed: result={result}")
    if sep_status != 0:
        return sep_status, -1, -1
    if resp_len < 12:
        raise RuntimeError("create response is truncated")
    version, live_handle = struct.unpack_from("<Ii", response, 0)
    if version != CREATE_VERSION:
        raise RuntimeError("create response version mismatch")
    offset = 8
    if offset + 4 > resp_len:
        raise RuntimeError("KEK blob header truncated")
    kek_len = struct.unpack_from("<I", response, offset)[0]
    kek_end = offset + 4 + kek_len
    if kek_end > resp_len:
        raise RuntimeError("KEK blob overruns response")
    return sep_status, live_handle, kek_len


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-live", default="")
    parser.add_argument("--private-json", required=True)
    args = parser.parse_args()

    if not LIVE_C1_ENABLED or args.confirm_live != CONFIRM:
        return fail("live C1 probe is disabled in source; refusing")
    private_path = Path(args.private_json)
    if PRIVATE_ROOT not in private_path.resolve().parents:
        return fail("journal must stay under operator-private storage")
    if not LAB_DEVICE.exists() or not ACM_DEVICE.exists():
        return fail("lab/ACM devices absent; load the module first")

    helpers = _load_helpers()
    try:
        user_id, special, mapped_uid = helpers.configuration()
        if not helpers.caller_is_mapped(mapped_uid):
            return fail(
                "caller is not the mapped Linux user via sudo/pkexec")
        session, handle = helpers.keybag_runtime(special)
    except helpers.EnrollRunnerError as error:
        return fail(f"precondition: {error}")

    account_uuid = uuid.uuid4().bytes
    journal: dict[str, object] = {
        "opcode": 1,
        "stage": "c1",
        "wire_version": CREATE_VERSION,
        "warm_gate": True,
        "sep_status": None,
        "live_handle": None,
        "kek_length": None,
        "bag_uuid_observed": False,
        "outcome": "unknown",
    }

    def bind_password(context: bytes) -> None:
        completed = subprocess.run(
            [str(AKS_TOOL), "verify-password-acm",
             str(session), str(handle)],
            input=context, check=False)
        if completed.returncode:
            raise ACMDeviceError("AKS password binding failed")

    body = bytearray()
    response_scratch = bytearray()
    form_scratch = bytearray()
    try:
        with ACMDevice() as device:
            def consume(external_form: bytes) -> bytes:
                form_scratch.extend(external_form)
                body.extend(build_v5_body(session, form_scratch,
                                          account_uuid))
                journal["request_sha256"] = hashlib.sha256(
                    bytes(body)).hexdigest()
                private_path.write_text(json.dumps(journal, indent=2))
                sep_status, live_handle, kek_len = lab_create(body)
                journal["sep_status"] = sep_status
                journal["live_handle"] = live_handle
                journal["kek_length"] = kek_len
                if sep_status == 0 and live_handle > 0:
                    journal["outcome"] = "created-unbound"
                    uuid_out = private_path.parent / (
                        private_path.stem + ".bag-uuid.bin")
                    completed = subprocess.run(
                        [str(AKS_TOOL), "copy-keybag-uuid", str(session),
                         str(live_handle), str(uuid_out)],
                        capture_output=True, text=True, check=False)
                    if completed.returncode == 0:
                        try:
                            raw = uuid_out.read_bytes()
                            journal["bag_uuid_observed"] = (
                                len(raw) == 16 and any(raw))
                        finally:
                            uuid_out.unlink(missing_ok=True)
                else:
                    journal["outcome"] = "refused-clean"
                return b""
            initial, final, _ = with_authorized_context(
                device, user_id, bind_password, consume, tracking=True)
            journal["policy_satisfied"] = final.satisfied
    except (OSError, ValueError, ACMDeviceError, RuntimeError) as error:
        journal["outcome"] = f"halt: {type(error).__name__}"
        return fail(f"{error}")
    finally:
        _wipe(body, response_scratch, form_scratch)
    private_path.write_text(json.dumps(journal, indent=2))
    public = {k: v for k, v in journal.items()}
    print(json.dumps(public, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
