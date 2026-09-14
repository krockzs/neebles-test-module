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
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_locale(value):
    value = value.strip()

    if "." in value:
        value = value.split(".", 1)[0]

    if "@" in value:
        value = value.split("@", 1)[0]

    return value.replace("-", "_")


def load_module_manifest():
    data = load_json(MANIFEST_PATH)

    if data.get("schema") != 3:
        raise RuntimeError("module manifest schema must be 3")

    name = data.get("name")

    if not isinstance(name, str) or not name.strip():
        raise RuntimeError("module manifest name is missing")

    version = data.get("version")

    if not isinstance(version, str) or not version.strip():
        raise RuntimeError("module manifest version is missing")

    return data


def resolve_identity(module_manifest):
    declared = module_manifest["name"].strip()

    if "NEEBLES_MODULE" not in os.environ:
        return declared

    explicit = os.environ["NEEBLES_MODULE"].strip()

    if not explicit:
        raise RuntimeError(
            "explicit NEEBLES_MODULE cannot be empty"
        )

    if explicit != declared:
        raise RuntimeError(
            f"explicit NEEBLES_MODULE '{explicit}' does not match "
            f"module manifest name '{declared}'"
        )

    return explicit


def load_language_manifest():
    manifest = load_json(LANGUAGE_MANIFEST_PATH)

    if manifest.get("schema") != 1:
        raise RuntimeError(
            "module language manifest schema must be 1"
        )

    languages = manifest.get("languages")

    if not isinstance(languages, list) or not languages:
        raise RuntimeError(
            "module language manifest declares no languages"
        )

    default = manifest.get("default")

    if not isinstance(default, str) or not default.strip():
        raise RuntimeError(
            "module language manifest default is missing"
        )

    seen_codes = set()
    resolved = []

    for language in languages:
        if not isinstance(language, dict):
            raise RuntimeError(
                "module language entry must be an object"
            )

        code = language.get("code")
        filename = language.get("file")

        if not isinstance(code, str) or not code.strip():
            raise RuntimeError(
                "module language code is missing"
            )

        if not isinstance(filename, str) or not filename.strip():
            raise RuntimeError(
                f"module language '{code}' file is missing"
            )

        normalized_code = normalize_locale(code)

        if normalized_code in seen_codes:
            raise RuntimeError(
                f"duplicate module language '{code}'"
            )

        seen_codes.add(normalized_code)

        file_path = LANGUAGES_DIR / filename

        if (
            Path(filename).name != filename
            or filename in (".", "..")
        ):
            raise RuntimeError(
                f"unsafe language file path '{filename}'"
            )

        if not file_path.is_file():
            raise RuntimeError(
                f"module language file not found: {filename}"
            )

        resolved.append(
            {
                "code": code,
                "normalized": normalized_code,
                "file": filename,
            }
        )

    normalized_default = normalize_locale(default)

    if normalized_default not in seen_codes:
        raise RuntimeError(
            f"default module language '{default}' is not declared"
        )

    return manifest, resolved


def find_language(languages, requested):
    normalized = normalize_locale(requested)

    for language in languages:
        if language["normalized"] == normalized:
            return language

    return None


def system_locale():
    for key in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(key, "").strip()

        if value:
            return value

    return ""


def resolve_language():
    manifest, languages = load_language_manifest()

    if "NEEBLES_LANGUAGE" in os.environ:
        explicit = os.environ["NEEBLES_LANGUAGE"]

        if not explicit.strip():
            raise RuntimeError(
                "explicit NEEBLES_LANGUAGE cannot be empty"
            )

        language = find_language(languages, explicit)

        if language is None:
            raise RuntimeError(
                f"explicit NEEBLES_LANGUAGE '{explicit}' "
                "is not supported by this module"
            )

        return language

    discovered = system_locale()

    if discovered:
        language = find_language(languages, discovered)

        if language is not None:
            return language

    default = manifest["default"]
    language = find_language(languages, default)

    if language is None:
        raise RuntimeError(
            f"default module language '{default}' is not declared"
        )

    return language


def load_strings():
    language = resolve_language()

    language_file = LANGUAGES_DIR / language["file"]
    strings = load_json(language_file)

    if not isinstance(strings, dict):
        raise RuntimeError(
            f"language file '{language['file']}' must contain an object"
        )

    return strings


def translate(strings, key, *args):
    if key not in strings:
        raise RuntimeError(
            f"missing translation key: {key}"
        )

    value = strings[key]

    if not isinstance(value, str):
        raise RuntimeError(
            f"translation key '{key}' must contain a string"
        )

    for index, argument in enumerate(args, start=1):
        value = value.replace(
            f"%{index}",
            str(argument)
        )

    return value


try:
    module_manifest = load_module_manifest()
    module_identity = resolve_identity(module_manifest)
    version = module_manifest["version"]
    strings = load_strings()
except (RuntimeError, ValueError, KeyError, json.JSONDecodeError, OSError) as error:
    print(
        f"N.E.E.B.L.E.S. module error: {error}",
        file=sys.stderr,
    )
    raise SystemExit(1)


if "--print-info" in sys.argv:
    print(
        translate(
            strings,
            "cli.info",
            version
        )
    )
    raise SystemExit(0)


if "--notification-text" in sys.argv:
    print(
        json.dumps(
            {
                "title": translate(
                    strings,
                    "notification.title"
                ),
                "message": translate(
                    strings,
                    "notification.message"
                ),
            },
            ensure_ascii=False,
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

root.geometry("640x360")
root.minsize(400, 240)
root.configure(bg="#111016")

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
    font=("Sans", 22, "bold")
)

heading.pack(
    pady=(110, 12)
)

subtitle = tk.Label(
    content,
    text=translate(
        strings,
        "app.subtitle"
    ),
    bg="#111016",
    fg="#A78BFA",
    font=("Sans", 14)
)

subtitle.pack()

root.mainloop()
