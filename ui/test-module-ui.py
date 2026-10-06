#!/usr/bin/python3.13

import json
import os
import queue
import sys
import threading
import uuid
import tkinter as tk
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LANGUAGE_MANIFEST = BASE_DIR / "languages" / "manifest.json"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_strings():
    manifest = load_json(LANGUAGE_MANIFEST)
    requested = os.environ.get("NEEBLES_LANGUAGE", manifest["default"]).split(".", 1)[0].replace("-", "_")
    selected = next((item for item in manifest["languages"] if item["code"].replace("-", "_") == requested), None)
    if selected is None:
        selected = next(item for item in manifest["languages"] if item["code"] == manifest["default"])
    return load_json(BASE_DIR / "languages" / selected["file"])


STRINGS = load_strings()

PRIVATE_UI_ACTIONS = [
    "version",
    "hello",
    "notify",
    "state",
    "settings",
    "toggle",
    "events",
    "external",
]

root = tk.Tk()
root.title(STRINGS.get("app.title", "N.E.E.B.L.E.S. Test Module"))
root.geometry("760x560")
root.minsize(680, 500)

header = tk.Label(root, text=STRINGS.get("app.heading", "N.E.E.B.L.E.S. Test Module"), font=("Sans", 20, "bold"))
header.pack(pady=(20, 6))

subtitle = tk.Label(root, text=STRINGS.get("app.subtitle", "Dynamic contract test console"))
subtitle.pack(pady=(0, 18))

result = tk.Text(root, height=10, wrap="word")
result.pack(side="bottom", fill="both", expand=True, padx=20, pady=20)

RUNTIME_EVENTS = queue.Queue()

option1 = tk.BooleanVar(value=False)
option2 = tk.BooleanVar(value=False)


def send_runtime_request(message):
    sys.stdout.write(
        json.dumps(
            message,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n"
    )
    sys.stdout.flush()


def request_feature(path, variable):
    requested = bool(variable.get())

    # Persist-first law:
    # local visual state is not authoritative.
    variable.set(not requested)

    send_runtime_request(
        {
            "type": "ui_intent",
            "id": str(uuid.uuid4()),
            "intent": "setting",
            "args": [
                path,
                "true" if requested else "false",
            ],
        }
    )


def runtime_reader():
    for line in sys.stdin:
        line = line.strip()

        if not line:
            continue

        try:
            message = json.loads(
                line
            )

        except json.JSONDecodeError:
            continue

        RUNTIME_EVENTS.put(
            message
        )


def drain_runtime_events():
    while True:
        try:
            message = RUNTIME_EVENTS.get_nowait()
        except queue.Empty:
            break

        message_type = message.get("type")

        if message_type == "settings_changed":
            path = message.get("path")
            value = message.get("value")

            if path == "features.option1":
                option1.set(value == "true")
            elif path == "features.option2":
                option2.set(value == "true")

            continue

        if message_type == "ui_result":
            intent = message.get("intent", "")
            response = message.get("response", {})

            if intent == "setting":
                payload = response.get("result") or {}
                path = payload.get("path")
                value = payload.get("value")

                if path == "features.option1":
                    option1.set(value == "true")
                elif path == "features.option2":
                    option2.set(value == "true")

                if response.get("ok") is True:
                    continue

            result.delete("1.0", "end")
            result.insert(
                "end",
                "test-module private UI "
                + intent
                + "\n\n",
            )
            result.insert(
                "end",
                json.dumps(
                    response,
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
            )
            continue

        if message_type == "ui_error":
            result.delete("1.0", "end")
            result.insert(
                "end",
                message.get("message", "runtime request failed"),
            )

    root.after(25, drain_runtime_events)


features = tk.LabelFrame(
    root,
    text=STRINGS.get(
        "features.title",
        "Module Features",
    ),
)

features.pack(
    fill="x",
    padx=20,
    pady=(0, 12),
)

tk.Checkbutton(
    features,
    text=STRINGS.get(
        "features.option1",
        "Feature Option 1",
    ),
    variable=option1,
    command=lambda: request_feature(
        "features.option1",
        option1,
    ),
).pack(
    anchor="w",
    padx=12,
    pady=(8, 4),
)

tk.Checkbutton(
    features,
    text=STRINGS.get(
        "features.option2",
        "Feature Option 2",
    ),
    variable=option2,
    command=lambda: request_feature(
        "features.option2",
        option2,
    ),
).pack(
    anchor="w",
    padx=12,
    pady=(4, 8),
)


def run_ui_intent(intent):
    result.delete("1.0", "end")
    result.insert(
        "end",
        "test-module private UI "
        + intent
        + "\n\n",
    )

    send_runtime_request(
        {
            "type": "ui_intent",
            "id": str(uuid.uuid4()),
            "intent": intent,
            "args": [],
        }
    )


for intent in PRIVATE_UI_ACTIONS:
    row = tk.Frame(root)
    row.pack(fill="x", padx=20, pady=5)
    tk.Label(row, text=f"test-module private UI {intent}", anchor="w", width=45).pack(side="left", fill="x", expand=True)
    tk.Button(row, text=STRINGS.get("ui.execute", "Ejecutar"), width=12, command=lambda value=intent: run_ui_intent(value)).pack(side="right")

threading.Thread(
    target=runtime_reader,
    daemon=True,
).start()

root.after(
    25,
    drain_runtime_events,
)

root.mainloop()
