#!/usr/bin/env python3

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
LANGUAGE_MANIFEST_PATH = BASE_DIR / "languages" / "manifest.json"
MODULE = "test-module"
PROTOCOL = 1
MAX_FRAME_SIZE = 16 * 1024 * 1024
SOCKET_PATH = Path(os.environ.get("NEEBLES_MODULES_SOCKET", "/run/neebles/modules.sock"))

STOP = False
UI_PROCESS = None


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def language_file():
    manifest = load_json(LANGUAGE_MANIFEST_PATH)
    requested = os.environ.get("NEEBLES_LANGUAGE", manifest["default"])
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
    title = text.get("notification.title", "N.E.E.B.L.E.S. Test Module")
    subprocess.run(
        ["neebles", "notify", "success", title, message],
        check=False,
        stdin=subprocess.DEVNULL,
    )


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
        raise RuntimeError(f"invalid module IPC frame length: {length}")
    payload = read_exact(stream, length)
    return json.loads(payload.decode("utf-8"))


def write_message(stream, message):
    payload = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_FRAME_SIZE:
        raise RuntimeError("module IPC frame too large")
    stream.sendall(struct.pack(">I", len(payload)) + payload)


def response(message, result=None, ok=True, code=0, error=None):
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


def execute_endpoint(message):
    endpoint = message.get("endpoint", "")
    manifest = load_json(MANIFEST_PATH)
    text = strings()

    if endpoint == "test.version":
        notify(text.get("notification.command.version", "Command version executed"))
        return response(message, {"version": manifest["version"]})

    if endpoint == "test.hello":
        notify(text.get("notification.command.hello", "Command hello executed"))
        return response(
            message,
            {"message": text.get("runtime.hello", "Hello from test-module")},
        )

    if endpoint == "test.notify":
        notify(text.get("notification.command.notify", "Notification command executed"))
        return response(message, {"notified": True})

    if endpoint == "test.state":
        notify(text.get("notification.command.state", "Command state executed"))
        return response(
            message,
            {
                "runtime": "ready",
                "session_id": message["session_id"],
                "ui_open": UI_PROCESS is not None and UI_PROCESS.poll() is None,
            },
        )

    return response(
        message,
        ok=False,
        code=2,
        error={
            "kind": "unknown_endpoint",
            "message": f"unknown test-module endpoint: {endpoint}",
            "details": None,
        },
    )


def stop_handler(_signum, _frame):
    global STOP
    STOP = True


def launch_ui():
    return subprocess.Popen(
        [sys.executable, str(BASE_DIR / "ui" / "test-module-ui.py")],
        cwd=BASE_DIR,
        env=os.environ.copy(),
    )


def main():
    global STOP, UI_PROCESS

    identity = os.environ.get("NEEBLES_MODULE", MODULE).strip()
    if identity != MODULE:
        raise RuntimeError(f"runtime identity '{identity}' does not match '{MODULE}'")

    session_id = str(uuid.uuid4())

    signal.signal(signal.SIGTERM, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)

    stream = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    stream.connect(str(SOCKET_PATH))

    write_message(
        stream,
        {
            "type": "register",
            "protocol": PROTOCOL,
            "module": MODULE,
            "session_id": session_id,
            "endpoints": {
                "commands": [
                    "test.version",
                    "test.hello",
                    "test.notify",
                    "test.state",
                ]
            },
        },
    )

    registered = read_message(stream)
    if registered.get("type") != "registered":
        raise RuntimeError(f"runtime registration failed: {registered}")

    UI_PROCESS = launch_ui()

    try:
        while not STOP:
            if UI_PROCESS.poll() is not None:
                break

            readable, _, _ = select.select([stream], [], [], 0.25)
            if not readable:
                continue

            message = read_message(stream)
            message_type = message.get("type")

            if message_type == "invoke":
                write_message(stream, execute_endpoint(message))
                continue

            if message_type == "ping":
                write_message(
                    stream,
                    {
                        "type": "pong",
                        "module": MODULE,
                        "session_id": session_id,
                    },
                )
                continue

            if message_type == "shutdown":
                write_message(
                    stream,
                    {
                        "type": "shutdown_ack",
                        "module": MODULE,
                        "session_id": session_id,
                    },
                )
                STOP = True
                break

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
        if UI_PROCESS is not None and UI_PROCESS.poll() is None:
            UI_PROCESS.terminate()
            try:
                UI_PROCESS.wait(timeout=3)
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
    except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"N.E.E.B.L.E.S. test-module runtime error: {error}", file=sys.stderr)
        raise SystemExit(1)
