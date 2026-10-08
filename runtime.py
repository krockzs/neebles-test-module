#!/usr/bin/python3.13

import collections
import json
import os
import queue
import select
import signal
import socket
import struct
import subprocess
import threading
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
UI_REQUESTS = queue.Queue()

PRIVATE_UI_ENDPOINTS = {
    "version": "test.version",
    "hello": "test.hello",
    "notify": "test.notify",
    "state": "test.state",
    "settings": "test.settings",
    "setting": "test.setting",
    "toggle": "test.toggle",
    "events": "test.events",
    "external": "test.external",
}

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


def notify(
    stream,
    session_id,
    message,
):
    request_id = str(uuid.uuid4())

    text = strings()

    write_message(
        stream,
        {
            "type": "default_notification",
            "id": request_id,
            "module": MODULE,
            "session_id": session_id,
            "severity": "success",
            "icon": "icon.jpeg",
            "title": text.get(
                "notification.title",
                "N.E.E.B.L.E.S. Test Module",
            ),
            "message": message,
            "expire_timeout_ms": None,
            "replace_id": None,
        },
    )

    result = wait_for(
        stream,
        session_id,
        lambda message: (
            message.get("id") == request_id
            and message.get("type")
            in {
                "notification_ack",
                "error",
            }
        ),
    )

    if result["type"] == "error":
        error = result.get(
            "error",
            {},
        )

        raise RuntimeError(
            error.get(
                "message",
                "Boss notification failed",
            )
        )

    validate_identity(
        result,
        session_id,
    )

    return result.get(
        "notification_id"
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


def push_ui_message(message):
    global UI_PROCESS

    if (
        UI_PROCESS is None
        or UI_PROCESS.poll() is not None
        or UI_PROCESS.stdin is None
    ):
        return

    try:
        UI_PROCESS.stdin.write(
            json.dumps(
                message,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n"
        )

        UI_PROCESS.stdin.flush()

    except (
        BrokenPipeError,
        OSError,
        ValueError,
    ):
        pass


def read_ui_requests(process):
    if process.stdout is None:
        return

    for line in process.stdout:
        line = line.strip()

        if not line:
            continue

        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue

        if isinstance(message, dict):
            UI_REQUESTS.put(message)


def push_ui_error(request_id, message):
    push_ui_message(
        {
            "type": "ui_error",
            "id": request_id,
            "message": message,
        }
    )


def handle_ui_request(stream, session_id, message):
    request_id = message.get("id")

    if (
        not isinstance(request_id, str)
        or not request_id.strip()
    ):
        push_ui_error(None, "UI request id is missing")
        return

    if message.get("type") != "ui_intent":
        push_ui_error(request_id, "unsupported UI request type")
        return

    intent = message.get("intent")
    args = message.get("args", [])

    if not isinstance(intent, str) or not intent:
        push_ui_error(request_id, "UI intent identity is missing")
        return

    if not isinstance(args, list) or not all(
        isinstance(value, str)
        for value in args
    ):
        push_ui_error(request_id, "UI intent args must be strings")
        return

    endpoint = PRIVATE_UI_ENDPOINTS.get(intent)

    if endpoint is None:
        push_ui_error(request_id, "UI requested an undeclared private intent")
        return

    if intent == "setting":
        if len(args) != 2:
            push_ui_error(request_id, "UI setting intent requires path and value")
            return

    elif args:
        push_ui_error(request_id, "UI intent does not accept arguments")
        return

    invoke = {
        "id": request_id,
        "module": MODULE,
        "session_id": session_id,
        "contract": "private-ui",
        "endpoint": endpoint,
        "args": args,
    }

    try:
        executed = execute_endpoint(
            stream,
            session_id,
            invoke,
        )
    except (
        EOFError,
        OSError,
        RuntimeError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
    ) as error:
        push_ui_error(request_id, str(error))
        return

    push_ui_message(
        {
            "type": "ui_result",
            "id": request_id,
            "intent": intent,
            "response": executed,
        }
    )

def drain_ui_requests(stream, session_id):
    while True:
        try:
            message = UI_REQUESTS.get_nowait()
        except queue.Empty:
            return

        handle_ui_request(
            stream,
            session_id,
            message,
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

        if (
            message.get("topic")
            == f"settings.{MODULE}"
            and message.get("event")
            == "changed"
        ):
            payload = message.get(
                "payload",
                {},
            )

            path = payload.get("path")
            value = payload.get("value")

            if (
                isinstance(path, str)
                and isinstance(value, str)
            ):
                push_ui_message(
                    {
                        "type":
                            "settings_changed",

                        "path":
                            path,

                        "value":
                            value,
                    }
                )

        return True

    if message_type == "notification_closed":
        # Boss sends this asynchronous callback after a notification closes.
        # Treat it as protocol input, not a fatal unknown IPC message.
        validate_identity(message, session_id)
        record_event({
            "topic": "notification",
            "event": "closed",
            "payload": {
                "notification_id": message.get("notification_id"),
                "reason": message.get("reason"),
            },
        })
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
    global UI_PROCESS

    endpoint = message.get("endpoint", "")

    manifest = load_json(MANIFEST_PATH)
    text = strings()

    if endpoint == "ui.open":
        already_open = (
            UI_PROCESS is not None
            and UI_PROCESS.poll() is None
        )

        if not already_open:
            UI_PROCESS = launch_ui()

            for setting_path in (
                "features.option1",
                "features.option2",
            ):
                push_ui_message(
                    {
                        "type":
                            "settings_changed",

                        "path":
                            setting_path,

                        "value":
                            settings_get(
                                stream,
                                session_id,
                                setting_path,
                            ),
                    }
                )

        return response(
            message,
            {
                "opened": True,
                "already_open": already_open,
                "pid": (
                    UI_PROCESS.pid
                    if UI_PROCESS is not None
                    else None
                ),
            },
        )

    if endpoint == "test.version":
        notify(
            stream,
            session_id,
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
            stream,
            session_id,
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
            stream,
            session_id,
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
            stream,
            session_id,
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
            "features.option1",
        )

        option2 = settings_get(
            stream,
            session_id,
            "features.option2",
        )

        notify(

            stream,

            session_id,
            text.get(
                "notification.command.settings",
                "Settings read through Boss",
            )
        )

        return response(
            message,
            {
                "features.option1": option1,
                "features.option2": option2,
            },
        )

    if endpoint == "test.setting":
        args = message.get(
            "args",
            [],
        )

        if len(args) != 2:
            return response(
                message,
                ok=False,
                code=2,
                error={
                    "kind":
                        "invalid_setting_arguments",

                    "message":
                        "setting requires path and value",

                    "details":
                        None,
                },
            )

        path, requested = args

        allowed = {
            "features.option1",
            "features.option2",
        }

        if path not in allowed:
            return response(
                message,
                ok=False,
                code=2,
                error={
                    "kind":
                        "unknown_setting",

                    "message":
                        "unsupported test-module setting: "
                        + path,

                    "details":
                        None,
                },
            )

        if requested not in {
            "true",
            "false",
        }:
            return response(
                message,
                ok=False,
                code=2,
                error={
                    "kind":
                        "invalid_setting_value",

                    "message":
                        "setting value must be true or false",

                    "details":
                        None,
                },
            )

        previous = settings_get(
            stream,
            session_id,
            path,
        )

        persisted = settings_set(
            stream,
            session_id,
            path,
            requested,
        )

        return response(
            message,
            {
                "path": path,
                "previous": previous,
                "value": persisted,
            },
        )

    if endpoint == "test.toggle":
        previous = settings_get(
            stream,
            session_id,
            "features.option1",
        )

        next_value = (
            "false"
            if previous == "true"
            else "true"
        )

        persisted = settings_set(
            stream,
            session_id,
            "features.option1",
            next_value,
        )

        notify(

            stream,

            session_id,
            text.get(
                "notification.command.toggle",
                "Setting changed through Boss",
            )
        )

        return response(
            message,
            {
                "path": "features.option1",
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

            stream,

            session_id,
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
    process = subprocess.Popen(
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
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    threading.Thread(
        target=read_ui_requests,
        args=(process,),
        daemon=True,
    ).start()

    return process


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


def requested_intent():
    arguments = sys.argv[1:]

    if not arguments:
        return None

    if arguments == ["--intent", "open"]:
        return "open"

    raise ValueError(
        "unsupported runtime arguments: "
        + " ".join(arguments)
    )


def main():
    global STOP, UI_PROCESS

    intent = requested_intent()

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

    if intent == "open":
        UI_PROCESS = launch_ui()

        for setting_path in (
            "features.option1",
            "features.option2",
        ):
            push_ui_message(
                {
                    "type": "settings_changed",
                    "path": setting_path,
                    "value": settings_get(
                        stream,
                        session_id,
                        setting_path,
                    ),
                }
            )

    try:
        while not STOP:
            if (
                UI_PROCESS is not None
                and UI_PROCESS.poll() is not None
            ):
                # This Open session owns the UI process. Its exit must also
                # end the authenticated Module IPC session. Keeping the
                # parent alive here leaves Boss permanently saying "open".
                # The optional Tray provider is a separate runtime.
                break

            drain_ui_requests(
                stream,
                session_id,
            )

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
                    "reason": "runtime_exit",
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
