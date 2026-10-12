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
CONTROLLER_SOCKET = Path(f"/run/user/{os.geteuid()}/neebles/test-module-controller.sock")


def controller_request(action):
    if action not in {"status", "open"}:
        raise ValueError("invalid Test Module controller action")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as controller:
        controller.settimeout(24 if action == "open" else 8)
        controller.connect(str(CONTROLLER_SOCKET))
        controller.sendall((json.dumps({"action": action}) + "\n").encode("utf-8"))
        controller.shutdown(socket.SHUT_WR)
        with controller.makefile("r", encoding="utf-8") as reader:
            line = reader.readline(4096)
    if not line:
        raise RuntimeError("Test Module controller is unavailable")
    answer = json.loads(line)
    if answer.get("ok") is not True:
        raise RuntimeError(str(answer.get("error", "controller request rejected")))
    return answer


def load_tray_strings():
    base = Path(__file__).resolve().parent.parent
    info = json.loads((base / "languages/manifest.json").read_text(encoding="utf-8"))
    language = os.environ.get("NEEBLES_LANGUAGE", info["default"]).split(".", 1)[0].replace("-", "_")
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
        settings_set("tray.autostart", "false")

    session_visibility(initial_visible)

    option1 = tk.BooleanVar(value=initial_option1)
    option2 = tk.BooleanVar(value=initial_option2)
    ui_strings = load_tray_strings()
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
            report_message(f"No se pudo guardar Opción 1: {error}")
            publish_state(True)
            return

        report_message("Opción 1 encendida" if value else "Opción 1 apagada")
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
            report_message(f"No se pudo guardar Opción 2: {error}")
            publish_state(True)
            return

        report_message("Opción 2 encendida" if value else "Opción 2 apagada")
        publish_state(True)

    tk.Checkbutton(root, text="Opción 1", variable=option1, command=toggle1).pack(anchor="w", padx=30, pady=(30, 8))
    tk.Checkbutton(root, text="Opción 2", variable=option2, command=toggle2).pack(anchor="w", padx=30, pady=8)
    tk.Button(root, text="Botón de prueba", command=lambda: report_message("Botón de prueba presionado")).pack(pady=(8, 4))

    def controller_background(action):
        try:
            result = controller_request(action)
            EVENTS.put({"type": "controller_result", "action": action, "result": result})
        except Exception as error:
            EVENTS.put({"type": "controller_result", "action": action, "error": str(error)})

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
        threading.Thread(target=controller_background, args=("open",), daemon=True).start()

    open_button = tk.Button(
        root, text=ui_strings.get("surface.open_tray", "Abrir Test Module"),
        command=on_open_pressed, state="disabled",
    )
    open_button.pack(pady=(3, 12))

    def poll_open_status():
        if root.state() != "withdrawn" and not open_status["pending"] and not open_status["busy"]:
            open_status["pending"] = True
            threading.Thread(target=controller_background, args=("status",), daemon=True).start()
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
        if not open_status["pending"] and not open_status["busy"]:
            open_status["pending"] = True
            threading.Thread(target=controller_background, args=("status",), daemon=True).start()

    def process_events():
        while True:
            try:
                message = EVENTS.get_nowait()
            except queue.Empty:
                break

            kind = message.get("type")
            if kind == "controller_result":
                action = message["action"]
                failure = message.get("error")
                if action == "status":
                    open_status["pending"] = False
                    open_status["available"] = failure is None
                    if failure is None:
                        open_status["opened"] = message["result"]["opened"] is True
                elif action == "open":
                    open_status["busy"] = False
                    if failure is None:
                        open_status["available"] = True
                        open_status["opened"] = True
                        hide()
                    else:
                        report_message("No se pudo abrir Test Module: " + failure)
                refresh_open_button()
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
                else:
                    continue

                publish_state(
                    root.state() != "withdrawn"
                )

            elif kind == "reload":
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
