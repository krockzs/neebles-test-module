#!/usr/bin/env python3

import json
import os
import subprocess
import tkinter as tk
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LANGUAGE_MANIFEST = BASE_DIR / "languages" / "manifest.json"
COMMANDS_CONTRACT = BASE_DIR / "contracts" / "commands.json"


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
COMMANDS = list(load_json(COMMANDS_CONTRACT)["endpoints"].keys())

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


def run_command(command):
    completed = subprocess.run(
        ["neebles", "test-module", command],
        cwd=BASE_DIR,
        text=True,
        capture_output=True,
        check=False,
    )
    result.delete("1.0", "end")
    result.insert("end", f"$ neebles test-module {command}\n\n")
    if completed.stdout:
        result.insert("end", completed.stdout)
    if completed.stderr:
        result.insert("end", completed.stderr)
    result.insert("end", f"\nexit_code={completed.returncode}\n")


for command in COMMANDS:
    row = tk.Frame(root)
    row.pack(fill="x", padx=20, pady=5)
    tk.Label(row, text=f"neebles test-module {command}", anchor="w", width=45).pack(side="left", fill="x", expand=True)
    tk.Button(row, text=STRINGS.get("ui.execute", "Ejecutar"), width=12, command=lambda value=command: run_command(value)).pack(side="right")

root.mainloop()
