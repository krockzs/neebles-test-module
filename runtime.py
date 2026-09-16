#!/usr/bin/env python3

import collections
import json
import os
import select
import signal
import socket
import struct
import subprocess
import sys
import uuid
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = BASE_DIR / "manifest.json"
COMMANDS_PATH = BASE_DIR / "contracts" / "commands.json"
LANGUAGE_MANIFEST_PATH = BASE_DIR / "languages" / "manifest.json"

MODULE = "test-module"
PROTOCOL = 1
MAX_FRAME_SIZE = 16 * 1024 * 1024
MAX_EVENT_HISTORY = 64

SOCKET_PATH = Path(
    os.environ.get(
        "NEEBLES_MODULES_SOCKET",
        "/run/neebles/modules.sock",
    )
)

STOP = False
UI_PROCESS = None

EVENT_HISTORY = collections.deque(maxlen=MAX_EVENT_HISTORY)
DEFERRED_MESSAGES = collections.deque()

SUBSCRIPTIONS = [
    "module.lifecycle",
    f"settings.{MODULE}",
]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def language_file():
    manifest = load_json(LANGUAGE_MANIFEST_PATH)

    requested = os.environ.get(
        "NEEBLES_LANGUAGE",
        manifest["default"],
    )

    normalized = requested.split(".", 1)[0].replace("-", "_")

    for item in manifest["languages"]:
        if item["code"].replace("-", "_") == normalized:
            return BASE_DIR / "languages" / item["file"]

    default = manifest["default"].replace("-", "_")

    for item in manifest["languages"]:
        if item["code"].replace("-", "_") == default:
            return BASE_DIR / "languages" / item["file"]

    raise RuntimeError("default language is not available")


def strings():
    return load_json(language_file())


def notify(message):
    text = strings()

    title = text.get(
        "notification.title",
        "N.E.E.B.L.E.S. Test Module",
    )

    subprocess.run(
        [
            "neebles",
            "notify",
            "success",
            title,
            message,
        ],
        check=False,
        stdin=subprocess.DEVNULL,
    )


def declared_endpoints():
    contracts = load_json(COMMANDS_PATH)

    return [
        definition["endpoint"]
        for definition in contracts["endpoints"].values()
    ]


def read_exact(stream, size):
    data = bytearray()

    while len(data) < size:
        chunk = stream.recv(size - len(data))

        if not chunk:
            raise EOFError("module IPC socket closed")

        data.extend(chunk)

    return bytes(data)


def read_message(stream):
    header = read_exact(stream, 4)

    length = struct.unpack(">I", header)[0]

    if length == 0 or length > MAX_FRAME_SIZE:
        raise RuntimeError(
            f"invalid module IPC frame length: {length}"
        )

    payload = read_exact(stream, length)

    return json.loads(payload.decode("utf-8"))


def write_message(stream, message):
    payload = json.dumps(
        message,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    if len(payload) > MAX_FRAME_SIZE:
        raise RuntimeError("module IPC frame too large")

    stream.sendall(
        struct.pack(">I", len(payload)) + payload
    )


def validate_identity(message, session_id):
    module = message.get("module")

    if module is not None and module != MODULE:
        raise RuntimeError(
            f"module IPC identity mismatch: "
            f"expected '{MODULE}' received '{module}'"
        )

    received_session = message.get("session_id")

    if (
        received_session is not None
        and received_session != session_id
    ):
        raise RuntimeError(
            "module IPC session mismatch"
        )


def record_event(message):
    EVENT_HISTORY.append(
        {
            "topic": message.get("topic"),
            "event": message.get("event"),
            "payload": message.get("payload"),
        }
    )


def pong(stream, session_id):
    write_message(
        stream,
        {
            "type": "pong",
            "module": MODULE,
            "session_id": session_id,
        },
    )


def handle_control_message(stream, session_id, message):
    global STOP

    message_type = message.get("type")

    if message_type == "ping":
        validate_identity(message, session_id)
        pong(stream, session_id)
        return True

    if message_type == "event":
        validate_identity(message, session_id)
        record_event(message)
        return True

    if message_type == "shutdown":
        validate_identity(message, session_id)

        write_message(
            stream,
            {
                "type": "shutdown_ack",
                "module": MODULE,
                "session_id": session_id,
            },
        )

        STOP = True
        return True

    return False


def wait_for(
    stream,
    session_id,
    predicate,
):
    while not STOP:
        message = read_message(stream)

        if predicate(message):
            return message

        if handle_control_message(
            stream,
            session_id,
            message,
        ):
            continue

        if message.get("type") == "invoke":
            DEFERRED_MESSAGES.append(message)
            continue

        raise RuntimeError(
            "unexpected module IPC message while waiting: "
            f"{message}"
        )

    raise RuntimeError(
        "runtime stopped while waiting for Boss response"
    )


def settings_get(stream, session_id, path):
    request_id = str(uuid.uuid4())

    write_message(
        stream,
        {
            "type": "settings_get",
            "id": request_id,
            "module": MODULE,
            "session_id": session_id,
            "path": path,
        },
    )

    result = wait_for(
        stream,
        session_id,
        lambda message: (
            message.get("id") == request_id
            and message.get("type")
            in {"settings_value", "error"}
        ),
    )

    if result["type"] == "error":
        error = result.get("error", {})

        raise RuntimeError(
            error.get(
                "message",
                "Boss settings read failed",
            )
        )

    validate_identity(result, session_id)

    return result["value"]


def settings_set(
    stream,
    session_id,
    path,
    value,
):
    request_id = str(uuid.uuid4())

    write_message(
        stream,
        {
            "type": "settings_set",
            "id": request_id,
            "module": MODULE,
            "session_id": session_id,
            "path": path,
            "value": value,
        },
    )

    result = wait_for(
        stream,
        session_id,
        lambda message: (
            message.get("id") == request_id
            and message.get("type")
            in {"settings_value", "error"}
        ),
    )

    if result["type"] == "error":
        error = result.get("error", {})

        raise RuntimeError(
            error.get(
                "message",
                "Boss settings write failed",
            )
        )

    validate_identity(result, session_id)

    return result["value"]


def response(
    message,
    result=None,
    ok=True,
    code=0,
    error=None,
):
    return {
        "type": "response",
        "id": message["id"],
        "module": MODULE,
        "session_id": message["session_id"],
        "contract": message["contract"],
        "endpoint": message["endpoint"],
        "ok": ok,
        "code": code,
        "result": result,
        "error": error,
    }


def execute_endpoint(
    stream,
    session_id,
    message,
):
    endpoint = message.get("endpoint", "")

    manifest = load_json(MANIFEST_PATH)
    text = strings()

    if endpoint == "test.version":
        notify(
            text.get(
                "notification.command.version",
                "Command version executed",
            )
        )

        return response(
            message,
            {
                "version": manifest["version"],
            },
        )

    if endpoint == "test.hello":
        notify(
            text.get(
                "notification.command.hello",
                "Command hello executed",
            )
        )

        return response(
            message,
            {
                "message": text.get(
                    "runtime.hello",
                    "Hello from test-module",
                )
            },
        )

    if endpoint == "test.notify":
        notify(
            text.get(
                "notification.command.notify",
                "Notification command executed",
            )
        )

        return response(
            message,
            {
                "notified": True,
            },
        )

    if endpoint == "test.state":
        notify(
            text.get(
                "notification.command.state",
                "Command state executed",
            )
        )

        return response(
            message,
            {
                "runtime": "ready",
                "session_id": session_id,
                "ui_open": (
                    UI_PROCESS is not None
                    and UI_PROCESS.poll() is None
                ),
                "subscriptions": SUBSCRIPTIONS,
                "event_count": len(EVENT_HISTORY),
            },
        )

    if endpoint == "test.settings":
        option1 = settings_get(
            stream,
            session_id,
            "tray.option1",
        )

        option2 = settings_get(
            stream,
            session_id,
            "tray.option2",
        )

        notify(
            text.get(
                "notification.command.settings",
                "Settings read through Boss",
            )
        )

        return response(
            message,
            {
                "tray.option1": option1,
                "tray.option2": option2,
            },
        )

    if endpoint == "test.toggle":
        previous = settings_get(
            stream,
            session_id,
            "tray.option1",
        )

        next_value = (
            "false"
            if previous == "true"
            else "true"
        )

        persisted = settings_set(
            stream,
            session_id,
            "tray.option1",
            next_value,
        )

        notify(
            text.get(
                "notification.command.toggle",
                "Setting changed through Boss",
            )
        )

        return response(
            message,
            {
                "path": "tray.option1",
                "previous": previous,
                "value": persisted,
            },
        )

    if endpoint == "test.events":
        return response(
            message,
            {
                "subscriptions": SUBSCRIPTIONS,
                "events": list(EVENT_HISTORY),
            },
        )

    if endpoint == "test.external":
        write_message(
            stream,
            {
                "type": "error",
                "module": MODULE,
                "error": {
                    "kind": "test_external",
                    "message": (
                        "Intentional test-module External "
                        "diagnostic event"
                    ),
                    "details": {
                        "source": MODULE,
                        "purpose": "contract-test",
                    },
                },
            },
        )

        notify(
            text.get(
                "notification.command.external",
                "External diagnostic event emitted",
            )
        )

        return response(
            message,
            {
                "reported": True,
                "telemetry_authority": "boss",
            },
        )

    return response(
        message,
        ok=False,
        code=2,
        error={
            "kind": "unknown_endpoint",
            "message": (
                "unknown test-module endpoint: "
                f"{endpoint}"
            ),
            "details": None,
        },
    )


def stop_handler(_signum, _frame):
    global STOP
    STOP = True


def launch_ui():
    return subprocess.Popen(
        [
            sys.executable,
            str(
                BASE_DIR
                / "ui"
                / "test-module-ui.py"
            ),
        ],
        cwd=BASE_DIR,
        env=os.environ.copy(),
    )


def subscribe(
    stream,
    session_id,
):
    write_message(
        stream,
        {
            "type": "subscribe",
            "module": MODULE,
            "session_id": session_id,
            "topics": SUBSCRIPTIONS,
        },
    )

    subscribed = wait_for(
        stream,
        session_id,
        lambda message: (
            message.get("type")
            in {"subscribed", "error"}
        ),
    )

    if subscribed["type"] == "error":
        raise RuntimeError(
            "module subscription failed: "
            f"{subscribed}"
        )

    validate_identity(
        subscribed,
        session_id,
    )

    accepted = set(
        subscribed.get("topics", [])
    )

    if accepted != set(SUBSCRIPTIONS):
        raise RuntimeError(
            "Boss accepted an unexpected "
            f"subscription set: {accepted}"
        )


def next_runtime_message(stream):
    if DEFERRED_MESSAGES:
        return DEFERRED_MESSAGES.popleft()

    readable, _, _ = select.select(
        [stream],
        [],
        [],
        0.25,
    )

    if not readable:
        return None

    return read_message(stream)


def main():
    global STOP, UI_PROCESS

    identity = os.environ.get(
        "NEEBLES_MODULE",
        MODULE,
    ).strip()

    if identity != MODULE:
        raise RuntimeError(
            f"runtime identity '{identity}' "
            f"does not match '{MODULE}'"
        )

    session_id = str(uuid.uuid4())

    signal.signal(
        signal.SIGTERM,
        stop_handler,
    )

    signal.signal(
        signal.SIGINT,
        stop_handler,
    )

    stream = socket.socket(
        socket.AF_UNIX,
        socket.SOCK_STREAM,
    )

    stream.connect(
        str(SOCKET_PATH)
    )

    write_message(
        stream,
        {
            "type": "register",
            "protocol": PROTOCOL,
            "module": MODULE,
            "session_id": session_id,
            "endpoints": {
                "commands": declared_endpoints(),
            },
        },
    )

    registered = read_message(stream)

    if registered.get("type") != "registered":
        raise RuntimeError(
            "runtime registration failed: "
            f"{registered}"
        )

    validate_identity(
        registered,
        session_id,
    )

    if registered.get("protocol") != PROTOCOL:
        raise RuntimeError(
            "Boss registered an unexpected "
            f"protocol: {registered}"
        )

    subscribe(
        stream,
        session_id,
    )

    UI_PROCESS = launch_ui()

    try:
        while not STOP:
            if (
                UI_PROCESS is not None
                and UI_PROCESS.poll() is not None
            ):
                break

            message = next_runtime_message(
                stream
            )

            if message is None:
                continue

            if handle_control_message(
                stream,
                session_id,
                message,
            ):
                continue

            message_type = message.get("type")

            if message_type == "invoke":
                validate_identity(
                    message,
                    session_id,
                )

                write_message(
                    stream,
                    execute_endpoint(
                        stream,
                        session_id,
                        message,
                    ),
                )

                continue

            if message_type == "error":
                raise RuntimeError(
                    "Boss module IPC error: "
                    f"{message}"
                )

            raise RuntimeError(
                "unexpected module IPC message: "
                f"{message}"
            )

        if not STOP:
            write_message(
                stream,
                {
                    "type": "unregister",
                    "module": MODULE,
                    "session_id": session_id,
                    "reason": "ui_closed",
                },
            )

    finally:
        if (
            UI_PROCESS is not None
            and UI_PROCESS.poll() is None
        ):
            UI_PROCESS.terminate()

            try:
                UI_PROCESS.wait(
                    timeout=3
                )

            except subprocess.TimeoutExpired:
                UI_PROCESS.kill()
                UI_PROCESS.wait()

        try:
            stream.close()

        except OSError:
            pass


if __name__ == "__main__":
    try:
        main()

    except (
        EOFError,
        OSError,
        RuntimeError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
    ) as error:
        print(
            "N.E.E.B.L.E.S. test-module "
            f"runtime error: {error}",
            file=sys.stderr,
        )

        raise SystemExit(1)
