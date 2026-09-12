import json
from pathlib import Path
import tkinter as tk


BASE_DIR = Path(__file__).resolve().parent
MANIFEST = BASE_DIR / "manifest.json"


def load_version():
    data = json.loads(
        MANIFEST.read_text(
            encoding="utf-8"
        )
    )

    return data.get(
        "version",
        "unknown"
    )


version = load_version()

root = tk.Tk()

root.title(
    f"N.E.E.B.L.E.S. Test Module {version}"
)

root.geometry(
    "640x360"
)

root.minsize(
    400,
    240
)

root.configure(
    bg="#111016"
)

root.mainloop()
