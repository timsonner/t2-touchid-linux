#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""MBA91 verify-only fprintd-compatible D-Bus facade for Apple T2 Touch ID.

MacBookAir9,1 has no Linux-local Catacomb and no canonical per-finger
labels: the SEP holds macOS-enrolled identities verified live through
the token-free opcode-4 match (proven F1/F2/N1/N2/R1/K1/K2 on the
research branch). This daemon therefore exposes exactly one
compatibility alias meaning "any enrolled identity owned by the
configured Apple user". It performs verification only:

- Claim / Release with the same pinned-caller discipline as the
  proven daemon (system-bus unique sender, pidfd-backed process
  identity, active local session, protected account generation).
- ListEnrolledFingers returns the single alias iff a live SEP
  inventory proves at least one identity for the configured Apple
  user; otherwise NoEnrolledPrints. Never a fabricated per-finger
  list, never UUIDs.
- VerifyStart accepts "any" or the alias. A successful match emits
  VerifyFingerMatched(alias); ambiguous or silent outcomes fail
  closed as verify-unknown-error, never verify-no-match.
- No enrollment, no deletion, no Catacomb writes, no adaptive sync.
  Those methods are absent from the interface.

Match verdicts come from the standard bridge-xpc-probe token-free
path under the shared operation lock: a terminal match_result event
carrying an enrolled template means verify-match; a terminal
match_result without one means verify-no-match; no terminal verdict
at all means the outcome is unknown (finger absent, locked bags, or
transport fault) and must not be presented as a rejection.
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
import sys

LOCAL_SOURCE = Path(__file__).resolve().parent
if str(LOCAL_SOURCE) not in sys.path:
    sys.path.insert(0, str(LOCAL_SOURCE))

from dbus_next import BusType, DBusError, Message, MessageType, Variant
from dbus_next.constants import PropertyAccess
from dbus_next import introspection as dbus_introspection
from dbus_next.service import ServiceInterface, dbus_property, method, signal

import t2_dbus_identity
import t2_fprint_claim
from t2_dbus_sender import (
    DBusSenderError,
    SenderAwareMessageBus,
    current_sender as current_dbus_sender,
)

BUS_NAME = "net.reactivated.Fprint"
MANAGER_PATH = "/net/reactivated/Fprint/Manager"
DEVICE_PATH = "/net/reactivated/Fprint/Device/0"
FPRINT_ERROR = "net.reactivated.Fprint.Error"
LINUX_USER = os.environ.get("T2_TOUCHID_USER", "")
MACOS_USER_ID = int(os.environ.get("T2_TOUCHID_MACOS_USER_ID", "501"))
# Compatibility alias: the single listed slot meaning "authenticate
# against any enrolled identity of the configured Apple user". It is
# not an anatomical claim and not an enrollment count; use
# t2-touchid-inventory for the truthful hardware identity count.
ENROLLMENT_ALIAS = os.environ.get(
    "T2_TOUCHID_ENROLLED_FINGER", "right-index-finger"
)
ALLOWED_PAM_USERS = (LINUX_USER,)
UNSTARTED_CLAIM_SECONDS = 5.0
COMPLETED_CLAIM_SECONDS = 0.5

if not LINUX_USER:
    raise RuntimeError("T2_TOUCHID_USER is not configured")
if not 0 <= MACOS_USER_ID <= 0xFFFFFFFF:
    raise RuntimeError("T2_TOUCHID_MACOS_USER_ID is outside uint32 range")


class MBA91Backend:
    """Token-free verification against live SEP inventory. No mutations."""

    def __init__(self, project_dir: Path, match_seconds: float) -> None:
        self.project_dir = project_dir
        self.match_seconds = match_seconds
        self.process: asyncio.subprocess.Process | None = None
        self.operation_lock = asyncio.Lock()
        self.port: int | None = None
        self.port_from_cache = False
        port_file = Path(
            os.environ.get(
                "T2_TOUCHID_PORT_FILE", "/var/lib/t2-touchid/biometric-port"
            )
        )
        try:
            cached_port = int(port_file.read_text().strip())
            if 49152 <= cached_port <= 65535:
                self.port = cached_port
                self.port_from_cache = True
        except (OSError, ValueError):
            pass

    async def _run_probe(self, port: int, match: bool) -> dict:
        command = [
            "/usr/bin/flock",
            "--exclusive",
            "--timeout",
            "10",
            "--no-fork",
            "/run/t2-touchid/operation.lock",
            sys.executable,
            str(self.project_dir / "src/bridge-xpc-probe.py"),
            "--port",
            str(port),
            "--initialize",
            "--identity-list",
            "--macos-user-id",
            str(MACOS_USER_ID),
        ]
        if match:
            command.extend(
                [
                    "--match-seconds",
                    str(self.match_seconds),
                    "--stop-on-match-result",
                ]
            )
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self.process = process
        try:
            stdout, stderr = await process.communicate()
        finally:
            self.process = None
        if not stdout or process.returncode != 0:
            detail = stderr.decode(errors="replace").strip()
            raise RuntimeError(detail or "BridgeXPC probe failed")
        try:
            result = json.loads(stdout)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuntimeError("BridgeXPC probe returned malformed JSON") from error
        if not isinstance(result, dict):
            raise RuntimeError("BridgeXPC probe returned malformed JSON")
        return result

    async def discover(self) -> int:
        if self.port is not None:
            return self.port
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(self.project_dir / "src/discover-biometric-port.py"),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ.copy(),
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(stderr.decode(errors="replace").strip())
        self.port = int(stdout.decode().strip())
        if not 49152 <= self.port <= 65535:
            self.port = None
            raise RuntimeError("discovery returned an invalid port")
        self.port_from_cache = False
        return self.port

    async def _probe_with_rediscovery(self, match: bool) -> dict:
        port = await self.discover()
        try:
            return await self._run_probe(port, match)
        except RuntimeError:
            if not self.port_from_cache:
                raise
            self.port = None
            self.port_from_cache = False
            port = await self.discover()
            return await self._run_probe(port, match)

    @staticmethod
    def _identity_count(result: object) -> int:
        if not isinstance(result, dict):
            raise RuntimeError("malformed probe result")
        count = result.get("identity_record_count")
        if type(count) is not int or count < 0:
            raise RuntimeError("malformed identity inventory")
        return count

    async def list_fingers(self) -> tuple[str, ...]:
        async with self.operation_lock:
            result = await self._probe_with_rediscovery(match=False)
        if self._identity_count(result) < 1:
            return ()
        return (ENROLLMENT_ALIAS,)

    async def verify(self) -> tuple[str, dict]:
        async with self.operation_lock:
            result = await self._probe_with_rediscovery(match=True)
        events = result.get("match_events")
        if not isinstance(events, list):
            raise RuntimeError("probe returned no match events")
        verdicts = [
            event for event in events
            if isinstance(event, dict)
            and event.get("event_kind") == "match_result"
        ]
        if not verdicts:
            raise RuntimeError("match produced no terminal verdict")
        if any(event.get("matched") is True for event in verdicts):
            return "verify-match", result
        return "verify-no-match", result

    async def cancel(self) -> None:
        process = self.process
        if process is None or process.returncode is not None:
            return
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=2)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()


class FprintDevice(ServiceInterface):
    def __init__(
        self,
        backend: MBA91Backend,
        identity_bus,
        caller_collector=t2_dbus_identity.collect,
        claim_evidence_collector=t2_fprint_claim.collect,
    ) -> None:
        super().__init__("net.reactivated.Fprint.Device")
        self.backend = backend
        self.identity_bus = identity_bus
        self.caller_collector = caller_collector
        self.claim_evidence_collector = claim_evidence_collector
        self.claim_lock = asyncio.Lock()
        self.claimed_user: str | None = None
        self.claimed_sender: str | None = None
        self.claimed_caller: t2_dbus_identity.PinnedDBusCaller | None = None
        self.claimed_evidence: t2_fprint_claim.ClaimEvidence | None = None
        self.verify_task: asyncio.Task | None = None
        self.claim_expiry_task: asyncio.Task | None = None
        self.enrolled_fingers: tuple[str, ...] = (ENROLLMENT_ALIAS,)
        self.finger_present = False
        self.finger_needed = False

    @staticmethod
    def _consume_signal_send(result: object) -> None:
        if not isinstance(result, asyncio.Future):
            return

        def consume(future: asyncio.Future) -> None:
            try:
                future.exception()
            except BaseException:
                pass

        result.add_done_callback(consume)

    def _set_finger_state(self, present: object, needed: object) -> None:
        if (
            type(present) is not bool
            or type(needed) is not bool
            or (present and needed)
        ):
            raise RuntimeError("finger property state is invalid")
        changed: dict[str, Variant] = {}
        if present != self.finger_present:
            self.finger_present = present
            changed["finger-present"] = Variant("b", present)
        if needed != self.finger_needed:
            self.finger_needed = needed
            changed["finger-needed"] = Variant("b", needed)
        if not changed:
            return
        send = getattr(self.identity_bus, "send", None)
        if not callable(send):
            return
        try:
            result = send(
                Message.new_signal(
                    path=DEVICE_PATH,
                    interface="org.freedesktop.DBus.Properties",
                    member="PropertiesChanged",
                    signature="sa{sv}as",
                    body=[
                        "net.reactivated.Fprint.Device",
                        changed,
                        [],
                    ],
                )
            )
        except Exception:
            return
        self._consume_signal_send(result)

    @dbus_property(access=PropertyAccess.READ, name="name")
    def device_name(self) -> "s":
        return "Apple T2 Touch ID"

    @method()
    async def Claim(self, username: "s"):
        requested = username or LINUX_USER
        if requested not in ALLOWED_PAM_USERS:
            raise DBusError(f"{FPRINT_ERROR}.PermissionDenied", "unknown user")
        try:
            sender = current_dbus_sender()
        except DBusSenderError as error:
            raise DBusError(
                f"{FPRINT_ERROR}.PermissionDenied", "caller identity unavailable"
            ) from error
        async with self.claim_lock:
            if self.claimed_user is not None:
                old_caller = self.claimed_caller
                old_caller_dead = False
                if old_caller is not None:
                    try:
                        old_caller.verify()
                    except t2_dbus_identity.DBusIdentityError:
                        old_caller_dead = True
                if old_caller_dead:
                    await self._stop_verification(require_running=False)
                    self._clear_claim()
                else:
                    raise DBusError(
                        f"{FPRINT_ERROR}.AlreadyInUse", "device is claimed"
                    )
            caller = None
            try:
                caller = await self.caller_collector(
                    self.identity_bus, sender
                )
                if current_dbus_sender() != sender or caller.sender != sender:
                    raise t2_dbus_identity.DBusIdentityError(
                        "D-Bus caller changed during claim"
                    )
                caller.verify()
                evidence = await asyncio.to_thread(
                    self.claim_evidence_collector, caller, requested
                )
                if not isinstance(evidence, t2_fprint_claim.ClaimEvidence):
                    raise t2_fprint_claim.FprintClaimError(
                        "claim evidence collector returned an invalid result"
                    )
                if current_dbus_sender() != sender or caller.sender != sender:
                    raise t2_dbus_identity.DBusIdentityError(
                        "D-Bus caller changed during claim evidence collection"
                    )
                caller.verify()
            except (
                DBusSenderError,
                t2_dbus_identity.DBusIdentityError,
                t2_fprint_claim.FprintClaimError,
            ) as error:
                if caller is not None:
                    caller.close()
                raise DBusError(
                    f"{FPRINT_ERROR}.PermissionDenied",
                    "caller process identity unavailable",
                ) from error
            self.claimed_user = requested
            self.claimed_sender = sender
            self.claimed_caller = caller
            self.claimed_evidence = evidence
            self.claim_expiry_task = asyncio.create_task(
                self._expire_unstarted_claim()
            )

    def _clear_claim(self) -> None:
        caller = self.claimed_caller
        self.claimed_user = None
        self.claimed_sender = None
        self.claimed_caller = None
        self.claimed_evidence = None
        if caller is not None:
            caller.close()

    def _require_claim_owner(self) -> None:
        if (
            self.claimed_user is None
            or self.claimed_sender is None
            or self.claimed_caller is None
            or self.claimed_evidence is None
        ):
            raise DBusError(
                f"{FPRINT_ERROR}.ClaimDevice", "device is not claimed"
            )
        try:
            sender = current_dbus_sender()
        except DBusSenderError as error:
            raise DBusError(
                f"{FPRINT_ERROR}.PermissionDenied", "caller identity unavailable"
            ) from error
        if sender != self.claimed_sender:
            raise DBusError(
                f"{FPRINT_ERROR}.PermissionDenied",
                "device is claimed by another D-Bus connection",
            )
        try:
            if self.claimed_caller.sender != sender:
                raise t2_dbus_identity.DBusIdentityError(
                    "pinned sender does not match the claim"
                )
            self.claimed_caller.verify()
            self.claimed_evidence.revalidate(self.claimed_caller)
        except (
            t2_dbus_identity.DBusIdentityError,
            t2_fprint_claim.FprintClaimError,
        ) as error:
            raise DBusError(
                f"{FPRINT_ERROR}.PermissionDenied",
                "caller process identity is no longer valid",
            ) from error

    @method()
    async def Release(self):
        self._require_claim_owner()
        await self._stop_verification(require_running=False)
        self._clear_claim()

    @method()
    async def ListEnrolledFingers(self, username: "s") -> "as":
        requested = username or LINUX_USER
        if requested not in ALLOWED_PAM_USERS:
            raise DBusError(f"{FPRINT_ERROR}.PermissionDenied", "unknown user")
        try:
            self.enrolled_fingers = await self.backend.list_fingers()
        except Exception as error:
            raise DBusError(
                f"{FPRINT_ERROR}.Internal", "fingerprint inventory unavailable"
            ) from error
        if not self.enrolled_fingers:
            raise DBusError(
                f"{FPRINT_ERROR}.NoEnrolledPrints",
                "no fingerprints are enrolled",
            )
        return list(self.enrolled_fingers)

    @method()
    async def VerifyStart(self, finger_name: "s"):
        self._require_claim_owner()
        if self.verify_task is not None:
            raise DBusError(f"{FPRINT_ERROR}.AlreadyInUse", "verification is active")
        if finger_name != "any" and finger_name != ENROLLMENT_ALIAS:
            raise DBusError(
                f"{FPRINT_ERROR}.NoEnrolledPrints",
                "finger is not enrolled",
            )
        if self.claim_expiry_task is not None:
            self.claim_expiry_task.cancel()
            self.claim_expiry_task = None
        current_task = asyncio.current_task()
        if current_task is None:
            raise DBusError(
                f"{FPRINT_ERROR}.Internal",
                "verification task identity is unavailable",
            )
        self.verify_task = current_task
        started = False
        try:
            self._require_claim_owner()
            if self.verify_task is not current_task:
                raise RuntimeError("verification task binding changed")
            self.VerifyFingerSelected(finger_name)
            operation = asyncio.create_task(self._run_verification())
            self.verify_task = operation
            self._set_finger_state(False, True)
            started = True
        except DBusError:
            raise
        except Exception as error:
            raise DBusError(
                f"{FPRINT_ERROR}.Internal",
                "verification could not be started",
            ) from error
        finally:
            if not started and self.verify_task is current_task:
                self.verify_task = None
            self._arm_unstarted_claim_expiry()

    @method()
    async def VerifyStop(self):
        self._require_claim_owner()
        await self._stop_verification(require_running=True)

    async def _run_verification(self) -> None:
        current_task = asyncio.current_task()
        try:
            verdict, _result = await self.backend.verify()
            print(f"mba91-fprintd: verify {verdict}", flush=True)
            if verdict == "verify-match":
                self.VerifyFingerMatched(ENROLLMENT_ALIAS)
            self.VerifyStatus(verdict, True)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            print(
                f"mba91-fprintd: verify errored: {type(error).__name__}: "
                f"{str(error)[:200]}",
                flush=True,
            )
            self.VerifyStatus("verify-unknown-error", True)
        finally:
            self._set_finger_state(False, False)
        self.claim_expiry_task = asyncio.create_task(
            self._expire_stale_claim(current_task)
        )

    async def _expire_stale_claim(self, completed_task: asyncio.Task) -> None:
        await asyncio.sleep(COMPLETED_CLAIM_SECONDS)
        if self.verify_task is completed_task:
            self.verify_task = None
            self._clear_claim()
        self.claim_expiry_task = None

    async def _expire_unstarted_claim(self) -> None:
        await asyncio.sleep(UNSTARTED_CLAIM_SECONDS)
        if self.verify_task is None:
            self._clear_claim()
        self.claim_expiry_task = None

    async def sender_departed(self, sender: str) -> None:
        async with self.claim_lock:
            if sender != self.claimed_sender:
                return
            await self._stop_verification(require_running=False)
            self._clear_claim()

    async def _stop_verification(self, require_running: bool) -> None:
        expiry_task = self.claim_expiry_task
        if expiry_task is not None:
            expiry_task.cancel()
            self.claim_expiry_task = None
        task = self.verify_task
        if task is None:
            self._set_finger_state(False, False)
            if require_running:
                raise DBusError(
                    f"{FPRINT_ERROR}.NoActionInProgress",
                    "verification is not active",
                )
            return
        await self.backend.cancel()
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        self.verify_task = None
        self._set_finger_state(False, False)

    def _arm_unstarted_claim_expiry(self) -> None:
        if (
            self.claimed_user is not None
            and self.claim_expiry_task is None
            and self.verify_task is None
        ):
            self.claim_expiry_task = asyncio.create_task(
                self._expire_unstarted_claim()
            )

    @signal()
    def VerifyFingerSelected(self, finger_name: "s") -> "s":
        return finger_name

    @signal()
    def VerifyFingerMatched(self, finger_name: "s") -> "s":
        return finger_name

    @signal()
    def VerifyStatus(self, result: "s", done: "b") -> "sb":
        return [result, done]


class FprintManager(ServiceInterface):
    def __init__(self) -> None:
        super().__init__("net.reactivated.Fprint.Manager")

    @method()
    def GetDevices(self) -> "ao":
        return [DEVICE_PATH]

    @method()
    def GetDefaultDevice(self) -> "o":
        return DEVICE_PATH


def legacy_property_reply(message: Message, device: FprintDevice):
    if (
        not isinstance(message, Message)
        or not isinstance(device, FprintDevice)
        or message.message_type != MessageType.METHOD_CALL
        or message.path != DEVICE_PATH
        or message.interface != "org.freedesktop.DBus.Properties"
    ):
        return False
    values = {
        "name": Variant("s", "Apple T2 Touch ID"),
        "num-enroll-stages": Variant("i", -1),
        "scan-type": Variant("s", "press"),
        "finger-present": Variant("b", device.finger_present),
        "finger-needed": Variant("b", device.finger_needed),
    }
    if (
        message.member == "Get"
        and message.body
        and message.body[0] == "net.reactivated.Fprint.Device"
        and len(message.body) == 2
        and message.body[1] in values
    ):
        return Message.new_method_return(
            message, signature="v", body=[values[message.body[1]]]
        )
    if (
        message.member == "GetAll"
        and message.body == ["net.reactivated.Fprint.Device"]
    ):
        return Message.new_method_return(
            message, signature="a{sv}", body=[values]
        )
    return False


def legacy_introspection_reply(message: Message, device: FprintDevice):
    if (
        not isinstance(message, Message)
        or not isinstance(device, FprintDevice)
        or message.message_type != MessageType.METHOD_CALL
        or message.path != DEVICE_PATH
        or message.interface != "org.freedesktop.DBus.Introspectable"
        or message.member != "Introspect"
        or message.body
        or str(message.signature)
    ):
        return False
    node = dbus_introspection.Node.default(DEVICE_PATH)
    node.interfaces.append(device.introspect())
    document = node.tostring()
    closing = document.rfind("</interface>")
    if closing < 0:
        raise RuntimeError("fprint introspection has no device interface")
    declarations = "".join(
        f'    <property name="{name}" type="{signature}" access="read" />\n'
        for name, signature in (
            ("num-enroll-stages", "i"),
            ("scan-type", "s"),
            ("finger-present", "b"),
            ("finger-needed", "b"),
        )
    )
    document = document[:closing] + declarations + document[closing:]
    return Message.new_method_return(
        message, signature="s", body=[document]
    )


async def main_async(args: argparse.Namespace) -> None:
    project_dir = Path(
        os.environ.get(
            "T2_TOUCHID_PROJECT_DIR", Path(__file__).resolve().parent.parent
        )
    )
    backend = MBA91Backend(project_dir, args.match_seconds)
    bus = await SenderAwareMessageBus(
        bus_type=BusType.SYSTEM, negotiate_unix_fd=True
    ).connect()
    device = FprintDevice(backend, bus)

    def legacy_property_handler(message: Message):
        return legacy_property_reply(message, device)

    def sender_departure_handler(message: Message):
        if (
            message.message_type == MessageType.SIGNAL
            and message.sender == "org.freedesktop.DBus"
            and message.path == "/org/freedesktop/DBus"
            and message.interface == "org.freedesktop.DBus"
            and message.member == "NameOwnerChanged"
            and len(message.body) == 3
            and message.body[0] == message.body[1]
            and not message.body[2]
        ):
            asyncio.create_task(device.sender_departed(message.body[0]))
        return False

    def legacy_introspection_handler(message: Message):
        return legacy_introspection_reply(message, device)

    bus.add_message_handler(legacy_introspection_handler)
    bus.add_message_handler(legacy_property_handler)
    bus.add_message_handler(sender_departure_handler)
    bus.export(MANAGER_PATH, FprintManager())
    bus.export(DEVICE_PATH, device)
    await bus.request_name(BUS_NAME)
    await asyncio.get_running_loop().create_future()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--match-seconds", type=float, default=30.0)
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
