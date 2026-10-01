#!/usr/bin/python3.13

import json
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LANGUAGE_MANIFEST = BASE_DIR / "languages" / "manifest.json"
COMMANDS_CONTRACT = BASE_DIR / "contracts" / "commands.json"
BOSS_CLI = Path(os.environ.get("NEEBLES_CLI", "/usr/local/bin/neebles"))


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

COMMANDS = [
    name
    for name, definition
    in load_json(
        COMMANDS_CONTRACT
    )["endpoints"].items()
    if (
        definition.get(
            "launcher"
        ) is not True
        and name != "setting"
    )
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


def boss_module_command(*arguments):
    return subprocess.run(
        [
            str(BOSS_CLI),
            "test-module",
            *arguments,
        ],
        cwd=BASE_DIR,
        text=True,
        capture_output=True,
        check=False,
    )


def canonical_settings():
    completed = boss_module_command(
        "settings"
    )

    if completed.returncode != 0:
        raise RuntimeError(
            completed.stderr.strip()
            or "could not read canonical module settings"
        )

    payload = json.loads(
        completed.stdout
    )

    option1.set(
        payload.get(
            "features.option1"
        ) == "true"
    )

    option2.set(
        payload.get(
            "features.option2"
        ) == "true"
    )


def request_feature(path, variable):
    requested = bool(
        variable.get()
    )

    # Persist-first law:
    # the local visual state is not authoritative.
    variable.set(
        not requested
    )

    completed = boss_module_command(
        "setting",
        path,
        (
            "true"
            if requested
            else "false"
        ),
    )

    if completed.returncode != 0:
        result.delete(
            "1.0",
            "end",
        )

        result.insert(
            "end",
            completed.stderr
            or "setting write failed",
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
            message = (
                RUNTIME_EVENTS
                .get_nowait()
            )

        except queue.Empty:
            break

        if (
            message.get("type")
            != "settings_changed"
        ):
            continue

        path = message.get("path")
        value = message.get("value")

        if path == "features.option1":
            option1.set(
                value == "true"
            )

        elif path == "features.option2":
            option2.set(
                value == "true"
            )

    root.after(
        25,
        drain_runtime_events,
    )


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


def run_command(command):
    completed = boss_module_command(
        command
    )

    result.delete(
        "1.0",
        "end",
    )

    result.insert(
        "end",
        "neebles test-module "
        + command
        + "\n\n",
    )

    if completed.stdout:
        result.insert(
            "end",
            completed.stdout,
        )

    if completed.stderr:
        result.insert(
            "end",
            completed.stderr,
        )

    result.insert(
        "end",
        "\nexit_code="
        + str(completed.returncode)
        + "\n",
    )


for command in COMMANDS:
    row = tk.Frame(root)
    row.pack(fill="x", padx=20, pady=5)
    tk.Label(row, text=f"neebles test-module {command}", anchor="w", width=45).pack(side="left", fill="x", expand=True)
    tk.Button(row, text=STRINGS.get("ui.execute", "Ejecutar"), width=12, command=lambda value=command: run_command(value)).pack(side="right")

threading.Thread(
    target=runtime_reader,
    daemon=True,
).start()

root.after(
    25,
    drain_runtime_events,
)

root.mainloop()
