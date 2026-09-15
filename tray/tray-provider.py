#!/usr/bin/env python3

import json
import os
import queue
import signal
import socket
import subprocess
import threading
import time
import tkinter as tk
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODULE = os.environ.get("NEEBLES_MODULE", "test-module").strip() or "test-module"
TRAY_ID = MODULE
PROTOCOL = 1
SOCKET_PATH = Path(os.environ.get("NEEBLES_TRAY_SOCKET", f"/run/user/{os.geteuid()}/neebles/tray.sock"))
EVENTS = queue.Queue()
STOP = threading.Event()
WRITE_LOCK = threading.Lock()


def send_line(stream, message):
    payload = (json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    with WRITE_LOCK:
        stream.sendall(payload)


def notify(message):
    subprocess.run(
        ["neebles", "notify", "success", "N.E.E.B.L.E.S. Test Module", message],
        check=False,
        stdin=subprocess.DEVNULL,
    )


def reader(stream):
    file = stream.makefile("r", encoding="utf-8")
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

    first = json.loads(stream.makefile("r", encoding="utf-8").readline())
    if first.get("type") != "ack" or first.get("event") != "register":
        raise RuntimeError(f"tray registration failed: {first}")

    # Re-open a reader after registration acknowledgement.
    threading.Thread(target=reader, args=(stream,), daemon=True).start()
    threading.Thread(target=heartbeat, args=(stream,), daemon=True).start()

    root = tk.Tk()
    root.title("N.E.E.B.L.E.S. Test Module Tray")
    root.geometry("360x220")
    root.withdraw()

    option1 = tk.BooleanVar(value=False)
    option2 = tk.BooleanVar(value=False)

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
        notify("Opción 1 encendida" if option1.get() else "Opción 1 apagada")
        publish_state(True)

    def toggle2():
        notify("Opción 2 encendida" if option2.get() else "Opción 2 apagada")
        publish_state(True)

    tk.Checkbutton(root, text="Opción 1", variable=option1, command=toggle1).pack(anchor="w", padx=30, pady=(30, 8))
    tk.Checkbutton(root, text="Opción 2", variable=option2, command=toggle2).pack(anchor="w", padx=30, pady=8)
    tk.Button(root, text="Botón de prueba", command=lambda: notify("Botón de prueba presionado")).pack(pady=20)

    def hide():
        root.withdraw()
        publish_state(False)

    root.protocol("WM_DELETE_WINDOW", hide)

    def process_events():
        while True:
            try:
                message = EVENTS.get_nowait()
            except queue.Empty:
                break

            kind = message.get("type")
            if kind == "open":
                root.deiconify()
                root.lift()
                publish_state(True)
            elif kind == "close":
                hide()
            elif kind == "focus":
                root.deiconify()
                root.lift()
                root.focus_force()
                publish_state(True)
            elif kind == "resize":
                root.geometry(f"{int(message['width'])}x{int(message['height'])}")
                publish_state(True)
            elif kind == "reload":
                publish_state(root.state() != "withdrawn")

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
    root.mainloop()
    STOP.set()
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
