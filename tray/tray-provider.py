#!/usr/bin/python3.13

import json
import os
import queue
import signal
import socket
import sys
import threading
import tkinter as tk
from pathlib import Path

MODULE = os.environ.get("NEEBLES_MODULE", "test-module").strip() or "test-module"
TRAY_ID = MODULE
PROTOCOL = 1
SOCKET_PATH = Path(os.environ.get("NEEBLES_TRAY_SOCKET", f"/run/user/{os.geteuid()}/neebles/tray.sock"))
EVENTS = queue.Queue()
STOP = threading.Event()
WRITE_LOCK = threading.Lock()
OPEN_SURFACE_ITEM = "open.tray"


def authoritative_open_snapshot(response):
    """Fail closed on malformed, foreign or contradictory Governor projections."""
    if not isinstance(response, dict) or response.get("type") != "surface_snapshot":
        raise ValueError("not a governed Tray surface snapshot")
    if response.get("tray_id") != TRAY_ID or response.get("item_id") != OPEN_SURFACE_ITEM:
        raise ValueError("Tray surface snapshot owner mismatch")
    state = response.get("runtime_state")
    enabled = response.get("enabled")
    allowed = response.get("open_available")
    if state not in ("closed", "opening", "open") or type(enabled) is not bool or type(allowed) is not bool:
        raise ValueError("invalid Governor runtime state or availability")
    if state != "closed" and allowed:
        raise ValueError("contradictory Governor surface availability")
    return {
        "opened": state in ("opening", "open"),
        "available": enabled and allowed and state == "closed",
    }


def load_tray_strings(locale):
    base = Path(__file__).resolve().parent.parent
    info = json.loads((base / "languages/manifest.json").read_text(encoding="utf-8"))
    language = locale.split(".", 1)[0].replace("-", "_")
    for entry in info["languages"]:
        if entry["code"].replace("-", "_") == language:
            return json.loads((base / "languages" / entry["file"]).read_text(encoding="utf-8"))
    return json.loads((base / "languages" / next(x["file"] for x in info["languages"] if x["code"] == info["default"])).read_text(encoding="utf-8"))


def send_line(stream, message):
    payload = (json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    with WRITE_LOCK:
        stream.sendall(payload)


def report_message(message):
    print(
        "N.E.E.B.L.E.S. Test Module Tray: "
        + str(message),
        file=sys.stderr,
    )



def tray_settings_request(message):
    stream = socket.socket(
        socket.AF_UNIX,
        socket.SOCK_STREAM
    )

    try:
        stream.connect(
            str(SOCKET_PATH)
        )

        payload = (
            json.dumps(
                message,
                ensure_ascii=False,
                separators=(",", ":")
            )
            + "\n"
        ).encode("utf-8")

        stream.sendall(payload)
        stream.shutdown(socket.SHUT_WR)

        file = stream.makefile(
            "r",
            encoding="utf-8"
        )

        try:
            line = file.readline()
        finally:
            file.close()

    finally:
        stream.close()

    if not line:
        raise RuntimeError(
            "Tray Manager returned an empty settings response"
        )

    response = json.loads(line)

    if response.get("type") == "error":
        raise RuntimeError(
            response.get(
                "message",
                "unknown tray settings error"
            )
        )

    if response.get("type") != "settings_value":
        raise RuntimeError(
            "unexpected tray settings response: "
            f"{response.get('type')}"
        )

    if response.get("owner_module") != MODULE:
        raise RuntimeError(
            "tray settings response owner mismatch"
        )

    return response.get("value")


def settings_get(path):
    return tray_settings_request(
        {
            "type": "settings_get",
            "owner_module": MODULE,
            "path": path,
        }
    )


def settings_set(path, value):
    return tray_settings_request(
        {
            "type": "settings_set",
            "owner_module": MODULE,
            "path": path,
            "value": value,
        }
    )


def session_visibility(visible):
    # The public session-client Tray API is independent of the registered
    # provider stream. It updates this module's live SNI visibility only.
    stream = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    stream.settimeout(5)
    try:
        stream.connect(str(SOCKET_PATH))
        send_line(stream, {
            "type": "set_visibility",
            "tray_id": TRAY_ID,
            "visible": bool(visible),
        })
        file = stream.makefile("r", encoding="utf-8")
        try:
            line = file.readline()
        finally:
            file.close()
    finally:
        stream.close()
    if not line:
        raise RuntimeError("Tray visibility request has no reply")
    message = json.loads(line)
    if message.get("type") == "error":
        raise RuntimeError(message.get("message", "Tray visibility rejected"))
    if message.get("type") != "ack" or message.get("event") != "set_visibility":
        raise RuntimeError(f"unexpected Tray visibility response: {message}")


def reader(file):
    try:
        while not STOP.is_set():
            line = file.readline()
            if not line:
                break
            EVENTS.put(json.loads(line))
    finally:
        STOP.set()


def heartbeat(stream):
    while not STOP.wait(5):
        try:
            send_line(stream, {"type": "heartbeat", "tray_id": TRAY_ID})
        except OSError:
            STOP.set()
            return


def main():
    stream = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    stream.connect(str(SOCKET_PATH))
    file = stream.makefile("r", encoding="utf-8")

    send_line(
        stream,
        {
            "type": "register",
            "protocol": PROTOCOL,
            "tray_id": TRAY_ID,
            "owner_module": MODULE,
            "pid": os.getpid(),
        },
    )

    line = file.readline()
    if not line:
        raise RuntimeError("tray manager closed during registration")

    first = json.loads(line)
    if first.get("type") != "ack" or first.get("event") != "register":
        raise RuntimeError(f"tray registration failed: {first}")

    threading.Thread(target=reader, args=(file,), daemon=True).start()
    threading.Thread(target=heartbeat, args=(stream,), daemon=True).start()

    root = tk.Tk()
    root.title("N.E.E.B.L.E.S. Test Module Tray")
    # A Tray popup is not a conventional desktop window: no title bar or X.
    # Override-redirect also keeps the popup independent from task switching.
    root.overrideredirect(True)
    root.geometry("360x220")
    root.withdraw()

    initial_option1 = settings_get("features.option1") == "true"
    initial_option2 = settings_get("features.option2") == "true"
    initial_autostart = settings_get("tray.autostart") == "true"
    initial_visible = settings_get("tray.visible") == "true"

    # Boot identity disambiguates a user-triggered reconciliation from the
    # first provider startup after reboot. In the same boot, turning on
    # "Show Tray" must work even if Linux autostart is disabled.
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    if not boot_id:
        raise RuntimeError("cannot determine Linux boot identity")
    previous_boot_id = settings_get("tray.session_boot_id")
    if previous_boot_id != boot_id:
        settings_set("tray.session_boot_id", boot_id)
        if not initial_autostart and initial_visible:
            settings_set("tray.visible", "false")
            initial_visible = False
    if not initial_visible and initial_autostart:
        # Keep the user's autostart choice for diagnosis; a hidden icon is
        # not proof that the requested autostart setting should be erased.
        report_message("Tray autostart is enabled but visibility is disabled")

    session_visibility(initial_visible)

    option1 = tk.BooleanVar(value=initial_option1)
    option2 = tk.BooleanVar(value=initial_option2)
    ui_strings = load_tray_strings(settings_get("ui.language"))
    open_status = {"opened": False, "available": False, "busy": False, "pending": False}

    def publish_state(opened=None):
        send_line(
            stream,
            {
                "type": "state",
                "tray_id": TRAY_ID,
                "opened": opened,
                "width": root.winfo_width() if root.state() != "withdrawn" else None,
                "height": root.winfo_height() if root.state() != "withdrawn" else None,
                "state": {
                    "option1": option1.get(),
                    "option2": option2.get(),
                },
            },
        )

    def toggle1():
        value = bool(option1.get())

        try:
            settings_set(
                "features.option1",
                "true" if value else "false",
            )
        except Exception as error:
            option1.set(not value)
            report_message(f"{ui_strings.get('tray.save_failed', 'Could not save setting')}: {error}")
            publish_state(True)
            return

        report_message(ui_strings.get("tray.option1_on" if value else "tray.option1_off", "Option 1 changed"))
        publish_state(True)

    def toggle2():
        value = bool(option2.get())

        try:
            settings_set(
                "features.option2",
                "true" if value else "false",
            )
        except Exception as error:
            option2.set(not value)
            report_message(f"{ui_strings.get('tray.save_failed', 'Could not save setting')}: {error}")
            publish_state(True)
            return

        report_message(ui_strings.get("tray.option2_on" if value else "tray.option2_off", "Option 2 changed"))
        publish_state(True)

    option1_control = tk.Checkbutton(root, text=ui_strings.get("features.option1", "Feature Option 1"), variable=option1, command=toggle1)
    option1_control.pack(anchor="w", padx=30, pady=(30, 8))
    option2_control = tk.Checkbutton(root, text=ui_strings.get("features.option2", "Feature Option 2"), variable=option2, command=toggle2)
    option2_control.pack(anchor="w", padx=30, pady=8)
    test_button = tk.Button(root, text=ui_strings.get("tray.test_button", "Test button"), command=lambda: report_message(ui_strings.get("tray.test_pressed", "Tray test button pressed")))
    test_button.pack(pady=(8, 4))

    def request_open_status():
        if open_status["pending"]:
            return
        open_status["pending"] = True
        try:
            # Same authenticated provider stream; no extra host socket or CLI.
            send_line(stream, {
                "type": "surface_query", "tray_id": TRAY_ID,
                "item_id": OPEN_SURFACE_ITEM,
            })
        except OSError as error:
            open_status["pending"] = False
            open_status["available"] = False
            report_message(f"Tray surface query failed: {error}")
            refresh_open_button()

    def refresh_open_button():
        state = "normal" if (open_status["available"] and
                             not open_status["opened"] and
                             not open_status["busy"]) else "disabled"
        open_button.configure(state=state)

    def on_open_pressed():
        if open_status["opened"] or open_status["busy"] or not open_status["available"]:
            return
        open_status["busy"] = True
        refresh_open_button()
        try:
            send_line(stream, {
                "type": "surface_action", "tray_id": TRAY_ID,
                "item_id": OPEN_SURFACE_ITEM, "action": "open",
            })
        except OSError as error:
            open_status["busy"] = False
            open_status["available"] = False
            report_message(f"Tray Open failed: {error}")
            refresh_open_button()

    open_button = tk.Button(
        root, text=ui_strings.get("surface.open_tray", "Abrir Test Module"),
        command=on_open_pressed, state="disabled",
    )
    open_button.pack(pady=(3, 12))

    def apply_language(locale):
        nonlocal ui_strings
        ui_strings = load_tray_strings(locale)
        option1_control.configure(text=ui_strings.get("features.option1", "Feature Option 1"))
        option2_control.configure(text=ui_strings.get("features.option2", "Feature Option 2"))
        test_button.configure(text=ui_strings.get("tray.test_button", "Test button"))
        open_button.configure(text=ui_strings.get("surface.open_tray", "Open Test Module"))

    def poll_open_status():
        if root.state() != "withdrawn" and not open_status["pending"] and not open_status["busy"]:
            request_open_status()
        root.after(1100, poll_open_status)

    def hide():
        if root.state() == "withdrawn":
            return
        # Release the global X11 grab before withdrawing; otherwise clicks
        # outside of the popup could remain captured after it disappears.
        if root.grab_current() == root:
            root.grab_release()
        root.withdraw()
        publish_state(False)

    def dismiss_on_click(event):
        # Unlike FocusOut, an active X11 pointer grab reports external clicks
        # to the popup. We may then close without requiring any window X.
        px, py = event.x_root, event.y_root
        x, y = root.winfo_rootx(), root.winfo_rooty()
        if not (x <= px < x + root.winfo_width() and
                y <= py < y + root.winfo_height()):
            hide()

    def dismiss_if_focus_lost():
        # Under an X11 pointer grab, only an outside pointer click or Escape
        # dismisses this popup. KWin focus notifications are not reliable for
        # override-redirect windows; don't let them close it immediately.
        if root.state() == "withdrawn" or root.grab_current() == root:
            return
        focused = root.focus_get()
        if focused is None or focused.winfo_toplevel() != root:
            hide()

    def on_focus_out(_event):
        root.after(60, dismiss_if_focus_lost)

    root.bind("<FocusOut>", on_focus_out, add="+")
    root.bind("<ButtonPress>", dismiss_on_click, add="+")
    root.bind("<Escape>", lambda _event: hide(), add="+")
    root.protocol("WM_DELETE_WINDOW", hide)

    def position_popup():
        # Mirror Boss X11 tray anchoring without querying global Boss state.
        # Tk pointer coordinates and screen bounds are provided by Tk/X11.
        root.update_idletasks()
        width = max(root.winfo_reqwidth(), root.winfo_width(), 360)
        height = max(root.winfo_reqheight(), root.winfo_height(), 220)
        pointer_x = root.winfo_pointerx()
        pointer_y = root.winfo_pointery()
        screen_x = root.winfo_vrootx()
        screen_y = root.winfo_vrooty()
        screen_width = root.winfo_vrootwidth()
        screen_height = root.winfo_vrootheight()
        if screen_width <= 0 or screen_height <= 0:
            raise RuntimeError("Tk screen bounds are unavailable")
        margin = 10
        desired_x = pointer_x - width + 18
        desired_y = pointer_y - height - margin
        if desired_y < screen_y:
            desired_y = pointer_y + margin
        max_x = screen_x + max(0, screen_width - width)
        max_y = screen_y + max(0, screen_height - height)
        x = max(screen_x, min(desired_x, max_x))
        y = max(screen_y, min(desired_y, max_y))
        root.geometry(f"{width}x{height}+{x}+{y}")
        root.update_idletasks()

    def show_popup(focus=False):
        if not focus and root.state() != "withdrawn":
            # A second click on the Tray icon toggles the popup closed.
            hide()
            return
        position_popup()
        root.deiconify()
        root.lift()
        # Tk override-redirect windows do not consistently receive FocusOut
        # from KWin. A temporary global pointer grab delivers outside clicks
        # here, where dismiss_on_click releases it immediately.
        root.focus_force()
        root.grab_set_global()
        publish_state(True)
        # Fail closed while fetching a fresh Governor status for this popup.
        open_status["available"] = False
        refresh_open_button()
        if not open_status["pending"] and not open_status["busy"]:
            request_open_status()

    def process_events():
        while True:
            try:
                message = EVENTS.get_nowait()
            except queue.Empty:
                break

            kind = message.get("type")
            if kind == "surface_snapshot":
                open_status["pending"] = False
                try:
                    authoritative = authoritative_open_snapshot(message)
                except ValueError as error:
                    open_status["available"] = False
                    open_status["opened"] = False
                    report_message(f"Invalid Governor snapshot: {error}")
                else:
                    open_status["available"] = authoritative["available"]
                    open_status["opened"] = authoritative["opened"]
                refresh_open_button()
                continue
            if kind == "surface_action_result":
                if (message.get("tray_id") != TRAY_ID or
                        message.get("item_id") != OPEN_SURFACE_ITEM or
                        message.get("action") != "open"):
                    open_status["available"] = False
                    open_status["busy"] = False
                    refresh_open_button()
                    report_message("Foreign or invalid Tray surface action result")
                    continue
                open_status["busy"] = False
                open_status["available"] = False
                if message.get("ok") is True:
                    # Governor accepted the request; re-query on next popup.
                    open_status["opened"] = True
                    hide()
                else:
                    report_message("Governor rejected Open: " + str(message.get("error", "unknown error")))
                    if not open_status["pending"] and root.state() != "withdrawn":
                        request_open_status()
                refresh_open_button()
                continue
            if kind == "error":
                open_status["pending"] = False
                open_status["busy"] = False
                open_status["available"] = False
                refresh_open_button()
                report_message("Tray Manager error: " + str(message.get("message", "unknown")))
                continue
            if kind == "open":
                show_popup()
            elif kind == "close":
                hide()
            elif kind == "focus":
                show_popup(focus=True)
            elif kind == "resize":
                root.geometry(f"{int(message['width'])}x{int(message['height'])}")
                publish_state(True)
            elif kind == "settings_changed":
                if message.get("owner_module") != MODULE:
                    continue

                path = message.get("path")
                value = message.get("value")

                if path == "features.option1":
                    option1.set(value == "true")

                elif path == "features.option2":
                    option2.set(value == "true")
                elif path == "tray.visible":
                    desired = value == "true"
                    if not desired:
                        hide()
                    session_visibility(desired)
                    continue
                elif path == "tray.autostart":
                    # A session-start preference, not a live visibility flip.
                    continue
                elif path == "ui.language":
                    apply_language(value)
                    continue
                else:
                    continue

                publish_state(
                    root.state() != "withdrawn"
                )

            elif kind == "reload":
                apply_language(settings_get("ui.language"))
                option1.set(
                    settings_get(
                        "features.option1"
                    ) == "true"
                )

                option2.set(
                    settings_get(
                        "features.option2"
                    ) == "true"
                )
                visible = settings_get("tray.visible") == "true"
                if not visible:
                    hide()
                session_visibility(visible)

                publish_state(
                    root.state() != "withdrawn"
                )

        if STOP.is_set():
            try:
                send_line(stream, {"type": "unregister", "tray_id": TRAY_ID})
            except OSError:
                pass
            root.destroy()
            return

        root.after(150, process_events)

    def stop_handler(_signum, _frame):
        STOP.set()

    signal.signal(signal.SIGTERM, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)

    publish_state(False)
    root.after(150, process_events)
    root.after(1100, poll_open_status)
    root.mainloop()
    STOP.set()

    try:
        file.close()
    except OSError:
        pass
    try:
        stream.close()
    except OSError:
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"N.E.E.B.L.E.S. test-module tray error: {error}", flush=True)
        raise
