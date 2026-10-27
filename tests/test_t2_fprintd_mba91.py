#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Fail-closed MBA91 verify verdicts. No hardware and no identifiers."""

import importlib.util
import os
from pathlib import Path
import struct
import unittest
import uuid


os.environ.setdefault("T2_TOUCHID_USER", "test")

PROBE_PATH = Path(__file__).resolve().parents[1] / "src/bridge-xpc-probe.py"
PROBE_SPEC = importlib.util.spec_from_file_location(
    "bridge_xpc_probe_mba91", PROBE_PATH
)
PROBE = importlib.util.module_from_spec(PROBE_SPEC)
assert PROBE_SPEC.loader is not None
PROBE_SPEC.loader.exec_module(PROBE)

DAEMON_PATH = Path(__file__).resolve().parents[1] / "src/t2-fprintd-mba91.py"
DAEMON_SPEC = importlib.util.spec_from_file_location(
    "t2_fprintd_mba91", DAEMON_PATH
)
DAEMON = importlib.util.module_from_spec(DAEMON_SPEC)
assert DAEMON_SPEC.loader is not None
DAEMON_SPEC.loader.exec_module(DAEMON)

from tests.test_bridge_xpc_probe import match_result_event


def _probe_summary(raw: bytes, enrolled: bytes) -> dict:
    event = PROBE.summarize_event(
        [9, 0xE3FF8000, raw, None, None],
        (enrolled,),
        expected_user_id=501,
    )
    return {"identity_record_count": 1, "match_events": [event]}


class MBA91VerdictTests(unittest.TestCase):
    def test_attached_no_touch_summary_is_not_verify_match(self):
        """Captured summary: matched from a whole-blob UUID hit.

        data_length 3268, version 2, no structural result fields.
        """

        captured = {
            "identity_record_count": 1,
            "match_events": [
                {
                    "method": "serviceStatus",
                    "data_length": 3268,
                    "embedded_type": "0xe3ff8002",
                    "version": 2,
                    "event_kind": "match_result",
                    "contains_enrolled_identity_uuid": True,
                    "matched": True,
                    "matches_enrolled_identity": True,
                }
            ],
        }
        with self.assertRaises(RuntimeError):
            DAEMON.verdict_from_result(captured)

    def test_opaque_uuid_in_3268_byte_result_is_verify_no_match(self):
        enrolled = struct.pack("<I", 501) + uuid.UUID(int=21).bytes
        raw = match_result_event(
            struct.pack("<i", -1) + bytes(16),
            lotl_count=5,
            flags=0,
            opaque_uuid=enrolled[4:20],
        )
        self.assertEqual(len(raw), 3268)
        self.assertIn(enrolled[4:20], raw)
        self.assertEqual(
            DAEMON.verdict_from_result(_probe_summary(raw, enrolled)),
            "verify-no-match",
        )

    def test_leading_enrolled_record_still_verifies(self):
        enrolled = struct.pack("<I", 501) + uuid.UUID(int=22).bytes
        raw = match_result_event(enrolled, lotl_count=5)
        self.assertEqual(
            DAEMON.verdict_from_result(_probe_summary(raw, enrolled)),
            "verify-match",
        )

    def test_silence_is_unknown(self):
        with self.assertRaises(RuntimeError):
            DAEMON.verdict_from_result({"match_events": []})
