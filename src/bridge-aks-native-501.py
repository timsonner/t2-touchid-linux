#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""One type-5 keybag create, export, and reload. Statuses and lengths only.

Ran once on 2026-09-26 for Apple user 501, session 1. Operation 0x01
returned status 0, live handle 1, KEK length 162. Operation 0x02 saved
1540 bytes. Reloading that file returned handle 2 and the bag UUID
matched. The alias bind was the existing tool, not this script:

    t2-aks-tool set-system-keybag 1 2 -501

That returned status 0. The output files already exist, so a second run
refuses before any SEP command.
"""

from __future__ import annotations

import importlib.util
import json
import os
import secrets
import subprocess
import sys
import uuid
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SRC / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


create = _load("create_c1", "bridge-aks-create-c1.py")
export = _load("export_c3", "bridge-aks-export-c3.py")
from t2_acm_device import ACMDevice, identity_secret_context  # noqa: E402

SESSION = 1
USER_ID = 501
ROOT = Path("/var/lib/t2-touchid")
BAG = ROOT / "native-501.kb"
FORM = ROOT / "native-501.form"
ACCOUNT = ROOT / "native-501.account"
JOURNAL = ROOT / "native-501-create.json"


def write_private(path: Path, data: bytes, mode: int) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


def main() -> int:
    for path in (BAG, FORM, ACCOUNT, JOURNAL):
        if path.exists():
            print(f"refusing to overwrite {path.name}", file=sys.stderr)
            return 1
    secret = bytearray(secrets.token_bytes(32))
    account = uuid.uuid4().bytes
    journal: dict[str, object] = {
        "user_id": USER_ID,
        "session": SESSION,
        "wire_version": 5,
        "sep_status": None,
        "live_handle": None,
        "kek_length": None,
        "export_status": None,
        "saved_length": None,
        "reload_status": None,
        "reload_handle": None,
        "reload_uuid_match": False,
        "outcome": "unknown",
    }
    try:
        with ACMDevice() as device:
            with identity_secret_context(device, USER_ID, secret) as form:
                if len(form) != 16:
                    raise RuntimeError("external form length is not 16")
                body = create.build_v5_body(SESSION, form, account)
                sep_status, live_handle, kek_len = create.lab_create(body)
                create._wipe(body)
                journal["sep_status"] = sep_status
                journal["live_handle"] = live_handle
                journal["kek_length"] = kek_len
                if sep_status != 0 or live_handle <= 0:
                    journal["outcome"] = "create-refused"
                    return 0
                write_private(FORM, form, 0o400)
                write_private(ACCOUNT, account, 0o400)
                export_body = bytearray(
                    export.struct.pack("<IQi", 1, SESSION, live_handle)
                    + export._blob(b"")
                )
                export_status, response = export.lab_dispatch(0x02, export_body)
                export._wipe(export_body)
                journal["export_status"] = export_status
                if export_status != 0:
                    journal["outcome"] = "export-refused"
                    return 0
                if len(response) < 8:
                    raise RuntimeError("export response is truncated")
                blob_len = export.struct.unpack_from("<I", response, 4)[0]
                saved = bytearray(response[8:8 + blob_len])
                export._wipe(response)
                journal["saved_length"] = len(saved)
                write_private(BAG, bytes(saved), 0o600)
                export._wipe(saved)
        completed = subprocess.run(
            ["/usr/local/sbin/t2-aks-tool", "load-keybag", str(BAG), str(SESSION)],
            capture_output=True, text=True, check=False,
        )
        text = completed.stdout.strip()
        journal["reload_status"] = text.split()[0] if text else f"rc={completed.returncode}"
        if completed.returncode != 0 or "status=0" not in text or "handle=" not in text:
            journal["outcome"] = "reload-failed"
            return 0
        reload_handle = int(text.split("handle=")[1].split()[0])
        journal["reload_handle"] = reload_handle

        def uuid_of(handle: int) -> bytes | None:
            path = ROOT / f".uuid-{handle}"
            code, _ = export.run_tool(
                "copy-keybag-uuid", str(SESSION), str(handle), str(path))
            try:
                if code == 0 and path.is_file():
                    raw = path.read_bytes()
                    if len(raw) == 16 and any(raw):
                        return raw
            finally:
                path.unlink(missing_ok=True)
            return None

        left = uuid_of(int(journal["live_handle"]))
        right = uuid_of(reload_handle)
        journal["reload_uuid_match"] = left is not None and left == right
        journal["outcome"] = (
            "created-exported-reloaded" if journal["reload_uuid_match"]
            else "uuid-mismatch-halt"
        )
        return 0
    except Exception as error:
        journal["outcome"] = f"halt:{type(error).__name__}"
        print(f"halt:{type(error).__name__}", file=sys.stderr)
        return 1
    finally:
        secret[:] = b"\x00" * len(secret)
        JOURNAL.write_text(json.dumps(journal, indent=2) + "\n")
        os.chmod(JOURNAL, 0o600)
        print(json.dumps(journal, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
