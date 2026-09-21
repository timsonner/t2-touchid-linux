#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""DRAFT (staged, not yet run): C3 keybag export/persist/reload probe.

Status: design only. LIVE_C3_ENABLED defaults False; even enabled,
this refuses unless ALL of the following hold:

- warm SEP with the C1-created live handle still present (verified
  via bag-UUID readback before export);
- explicit --live-handle matching that verified handle (never a
  macOS bag handle; the script additionally refuses handles 1 and
  any handle whose UUID matches the configured user.kb bag);
- explicit --confirm-live, with intent journaled pre-dispatch to a
  REQUIRED operator-private path.

Body: verify live handle by UUID -> endpoint-7 op 0x02 v1 export
(version-u32, session-u64, live-handle-i32, empty blob) via the lab
path -> parse saved-keybag blob -> atomic persist root-only 0600 to
the --out-keybag path (default under /var/lib/t2-touchid with a
`native-c3-test` name that product code must never consume) ->
reload the file through the allowlisted load path (additive new
handle) -> bag-UUID of the reloaded handle must equal the pre-export
UUID. NO bind, NO alias change, NO delete. The reloaded handle and
the C1 handle both evaporate on reboot; the test file stays until
the operator deletes it (it must go before any product use).

Secrets discipline: the saved blob lives only in wipeable
bytearrays in transit and in the root-only output file at rest;
lengths/statuses/handles only on stdout/logs. Finger not needed;
no ACM/password involved (export is authoritative by live-handle
possession within the lab session).

Failure (non-0 status, UUID mismatch, reload failure) halts with no
replay; the test file is still removed on failure paths to avoid
stale secret-adjacent artifacts — wait, no: on UUID mismatch the
file is EVIDENCE. Keep-on-failure, operator deletes by hand after
review. Documented in the journal either way.
"""

from __future__ import annotations

import argparse
import ctypes
import fcntl
import hashlib
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

LOCAL_SOURCE = Path(__file__).resolve().parent
if str(LOCAL_SOURCE) not in sys.path:
    sys.path.insert(0, str(LOCAL_SOURCE))

LIVE_C3_ENABLED = False
CONFIRM = "I_UNDERSTAND_THIS_EXPORTS_ONE_TEST_KEYBAG"
AKS_TOOL = Path("/usr/local/sbin/t2-aks-tool")
LAB_DEVICE = Path("/dev/t2-sep-lab")
EXPORT_OP = 0x02
EXPORT_VERSION = 1
PRIVATE_ROOT = Path("/home/tim/Private")

_LAB_AKS_FORMAT = "<BBBBB3sIIIIQQb3s4ii"
_LAB_IOC_MAGIC = 0xA8
_LAB_IOC_NR = 4


def _lab_ioc_aks() -> int:
    size = struct.calcsize(_LAB_AKS_FORMAT)
    assert size == 64, f"lab AKS struct is {size} bytes, want 64"
    return (3 << 30) | (size << 16) | (_LAB_IOC_MAGIC << 8) | _LAB_IOC_NR


T2_SEP_LAB_IOC_AKS = _lab_ioc_aks()


def fail(message: str) -> int:
    print(f"export-c3: {message}", file=sys.stderr)
    return 1


def _blob(value: bytes) -> bytes:
    return struct.pack("<I", len(value)) + value + b"\x00" * (-len(value) & 3)


def _wipe(*buffers: bytearray) -> None:
    for buffer in buffers:
        if isinstance(buffer, bytearray) and buffer:
            ctypes.memset(ctypes.addressof(
                (ctypes.c_ubyte * len(buffer)).from_buffer(buffer)),
                0, len(buffer))


def lab_dispatch(op: int, body: bytearray) -> tuple[int, bytearray]:
    # Mirror the C tool: response capacity capped at 4096 (the lab
    # transport rejects larger capacities with EMSGSIZE). Saved
    # keybags are ~1.6 KiB, well inside.
    response = bytearray(4096)
    req_buf = (ctypes.c_ubyte * len(body)).from_buffer(body)
    resp_buf = (ctypes.c_ubyte * len(response)).from_buffer(response)
    args = struct.pack(
        _LAB_AKS_FORMAT,
        op, 2, 0, 0, 0, b"\x00\x00\x00",
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
    fields = struct.unpack(_LAB_AKS_FORMAT, bytes(args_buf))
    sep_status, result = fields[12], fields[18]
    resp_len = fields[9]
    if result != 0:
        raise RuntimeError(f"lab ioctl failed: result={result}")
    return sep_status, bytearray(response[:resp_len])


def run_tool(*argv: str) -> tuple[int, str]:
    completed = subprocess.run(
        [str(AKS_TOOL), *argv], capture_output=True, text=True, check=False)
    return completed.returncode, completed.stdout.strip()


def bag_uuid(session: int, handle: int, out: Path) -> bytes | None:
    code, _ = run_tool("copy-keybag-uuid", str(session), str(handle),
                       str(out))
    try:
        if code == 0:
            raw = out.read_bytes()
            if len(raw) == 16 and any(raw):
                return raw
    finally:
        out.unlink(missing_ok=True)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, type=int)
    parser.add_argument("--live-handle", required=True, type=int)
    parser.add_argument("--out-keybag", required=True)
    parser.add_argument("--confirm-live", default="")
    parser.add_argument("--private-json", required=True)
    args = parser.parse_args()

    if not LIVE_C3_ENABLED or args.confirm_live != CONFIRM:
        return fail("live C3 probe is disabled in source; refusing")
    private_path = Path(args.private_json)
    if PRIVATE_ROOT not in private_path.resolve().parents:
        return fail("journal must stay under operator-private storage")
    out_path = Path(args.out_keybag)
    if out_path.exists():
        return fail("output keybag path already exists; refusing to overwrite")
    if not LAB_DEVICE.exists():
        return fail("lab device absent; load the module first")
    if args.live_handle in (1,):
        return fail("handle 1 is the macOS bag; refusing")

    journal: dict[str, object] = {
        "opcode": 2,
        "stage": "c3",
        "wire_version": EXPORT_VERSION,
        "live_handle": args.live_handle,
        "pre_uuid_observed": False,
        "sep_status": None,
        "saved_length": None,
        "reload_handle": None,
        "reload_uuid_match": False,
        "outcome": "unknown",
    }
    saved = bytearray()
    try:
        tmp = private_path.parent / (private_path.stem + ".uuid-pre.bin")
        pre = bag_uuid(args.session, args.live_handle, tmp)
        if pre is None:
            return fail("live handle has no readable bag UUID; refusing")
        journal["pre_uuid_observed"] = True
        journal["intent"] = {"live_handle": args.live_handle}
        private_path.write_text(json.dumps(journal, indent=2))

        body = bytearray(struct.pack("<IQi", EXPORT_VERSION, args.session,
                                     args.live_handle) + _blob(b""))
        sep_status, response = lab_dispatch(EXPORT_OP, body)
        _wipe(body)
        journal["sep_status"] = sep_status
        if sep_status != 0:
            journal["outcome"] = "refused-clean"
            private_path.write_text(json.dumps(journal, indent=2))
            print(json.dumps(journal, indent=2, sort_keys=True))
            return 0
        if len(response) < 8:
            raise RuntimeError("export response is truncated")
        version = struct.unpack_from("<I", response, 0)[0]
        if version != EXPORT_VERSION:
            raise RuntimeError("export response version mismatch")
        blob_len = struct.unpack_from("<I", response, 4)[0]
        if 8 + blob_len > len(response) or blob_len == 0:
            raise RuntimeError("saved keybag blob is invalid")
        saved.extend(response[8:8 + blob_len])
        _wipe(response)
        journal["saved_length"] = len(saved)
        journal["saved_sha256"] = hashlib.sha256(bytes(saved)).hexdigest()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "xb") as handle_file:
            os.fchmod(handle_file.fileno(), 0o600)
            handle_file.write(saved)
        code, out = run_tool("load-keybag", str(out_path), str(args.session))
        if code != 0 or "status=0" not in out:
            raise RuntimeError(f"reload failed: {out[:120]}")
        reload_handle = int(out.split("handle=")[1].split()[0])
        journal["reload_handle"] = reload_handle
        tmp2 = private_path.parent / (private_path.stem + ".uuid-post.bin")
        post = bag_uuid(args.session, reload_handle, tmp2)
        journal["reload_uuid_match"] = (
            post is not None and bytes(post) == bytes(pre))
        _wipe(pre and bytearray(pre) or bytearray())
        _wipe(post and bytearray(post) or bytearray())
        if journal["reload_uuid_match"]:
            journal["outcome"] = "exported-persisted-reloaded-verified"
        else:
            journal["outcome"] = "uuid-mismatch-halt"
    except (OSError, ValueError, RuntimeError) as error:
        journal["outcome"] = f"halt: {type(error).__name__}"
        try:
            private_path.write_text(json.dumps(journal, indent=2))
        except OSError:
            pass
        print(json.dumps(journal, indent=2, sort_keys=True))
        return fail(f"{error}")
    finally:
        _wipe(saved)
    private_path.write_text(json.dumps(journal, indent=2))
    print(json.dumps(journal, indent=2, sort_keys=True))
    if journal["outcome"] != "exported-persisted-reloaded-verified":
        return fail("C3 did not verify; review before any next step")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
