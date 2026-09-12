import json
import os
import sys
from pathlib import Path
import tkinter as tk


BASE_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = BASE_DIR / "manifest.json"
LANGUAGES_DIR = BASE_DIR / "languages"
LANGUAGE_MANIFEST_PATH = LANGUAGES_DIR / "manifest.json"


def load_json(path):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def load_version():
    data = load_json(
        MANIFEST_PATH
    )

    return data["version"]


def normalize_locale(value):
    value = value.strip()

    if "." in value:
        value = value.split(".", 1)[0]

    if "@" in value:
        value = value.split("@", 1)[0]

    return value.replace("-", "_")


def resolve_language():
    manifest = load_json(
        LANGUAGE_MANIFEST_PATH
    )

    languages = manifest.get(
        "languages",
        []
    )

    if not languages:
        raise RuntimeError(
            "module language manifest declares no languages"
        )

    requested = normalize_locale(
        os.environ.get(
            "NEEBLES_LANGUAGE",
            ""
        )
    )

    for language in languages:
        if normalize_locale(
            language["code"]
        ) == requested:
            return language

    default = manifest.get(
        "default",
        ""
    ).strip()

    if default:
        normalized_default = normalize_locale(
            default
        )

        for language in languages:
            if normalize_locale(
                language["code"]
            ) == normalized_default:
                return language

        raise RuntimeError(
            f"default module language '{default}' is not declared"
        )

    return languages[0]


def load_strings():
    language = resolve_language()

    language_file = (
        LANGUAGES_DIR
        / language["file"]
    )

    return load_json(
        language_file
    )


def translate(strings, key, *args):
    if key not in strings:
        raise RuntimeError(
            f"missing translation key: {key}"
        )

    value = strings[key]

    for index, argument in enumerate(
        args,
        start=1
    ):
        value = value.replace(
            f"%{index}",
            str(argument)
        )

    return value


version = load_version()
strings = load_strings()


if "--print-info" in sys.argv:
    print(
        translate(
            strings,
            "cli.info",
            version
        )
    )
    raise SystemExit(0)


root = tk.Tk()

root.title(
    translate(
        strings,
        "app.title",
        version
    )
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


content = tk.Frame(
    root,
    bg="#111016"
)

content.pack(
    expand=True,
    fill="both"
)


heading = tk.Label(
    content,
    text=translate(
        strings,
        "app.heading"
    ),
    bg="#111016",
    fg="#F5F5F5",
    font=(
        "Sans",
        22,
        "bold"
    )
)

heading.pack(
    pady=(
        110,
        12
    )
)


subtitle = tk.Label(
    content,
    text=translate(
        strings,
        "app.subtitle"
    ),
    bg="#111016",
    fg="#A78BFA",
    font=(
        "Sans",
        14
    )
)

subtitle.pack()


root.mainloop()
